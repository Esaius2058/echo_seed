import asyncio
import httpx
import logging
from echoseed.state.schema import EchoSeedState, FeatureVector

logger = logging.getLogger("audio_analyzer")

WORKER_URL = "http://10.0.11.150:8000/analyze"
HEALTH_URL = "http://10.0.11.150:8000/health"

# Dropped to 2. The m7i-flex.large is a CPU instance. 5 concurrent FFmpeg/Librosa 
# decodes will spike your RAM and trigger an OOM kill before the processing lock even catches them.
MAX_CONCURRENT = 2


def normalize_bpm(bpm: float):
    """Clamps BPM to a sensible 60-180 range by halving/doubling harmonics."""
    if bpm == 0:
        return 120.0  # fallback for complete failure
    while bpm > 180.0:
        bpm /= 2.0
    while bpm < 60.0:
        bpm *= 2.0
    return round(bpm, 2)


async def _process_track(
    client: httpx.AsyncClient,
    track_id: str,
    preview_url: str,
    semaphore: asyncio.Semaphore,
) -> tuple[str, FeatureVector | None]:
    """
    Downloads the preview and sends it to the m7i CPU worker concurrently.
    The semaphore caps how many tracks are in-flight at once.
    Returns a (track_id, FeatureVector | None) tuple.
    """
    async with semaphore:
        try:
            # ── 1. Download the preview audio ─────────────────────────────────
            audio_response = await client.get(preview_url, timeout=10.0)

            if audio_response.status_code != 200:
                logger.error(
                    f"Preview download failed ({audio_response.status_code}) "
                    f"for {track_id}"
                )
                return track_id, None

            audio_bytes = audio_response.content
            logger.info(f"First bytes for {track_id}: {audio_bytes[:10]}")

            if b"<!DOCTYPE" in audio_bytes or b"<html" in audio_bytes:
                logger.error(
                    f"Received HTML instead of audio for {track_id}. "
                    f"Preview URL may have expired."
                )
                return track_id, None

            # ── 2. Send to m7i worker for CPU inference ───────────────────────
            worker_response = await client.post(
                WORKER_URL,
                files={"file": (f"{track_id}.mp3", audio_bytes, "audio/mpeg")},
                timeout=180.0,  # CPU MERT inference is slower, needs breathing room
            )

            if worker_response.status_code != 200:
                logger.error(f"Worker failed for {track_id}: {worker_response.text}")
                return track_id, None

            data = worker_response.json()

            # ── 3. Build the FeatureVector ─────────────────────────────────────
            feature_vec: FeatureVector = {
                "track_id": track_id,
                "bpm": normalize_bpm(data.get("bpm")),
                "embedding": data["embedding"],
                "key": data.get("key", "Unknown"),
                "arousal": data.get("arousal", 5.0),
                "valence": data.get("valence", 5.0),
                "brightness": data.get("brightness", 0.5),
                "danceability": data.get("danceability", 0.5),
                "energy": data.get("energy", 0.5),
                "mood_tags": data.get("mood_tags", ["unknown"]), # Pulls actual tags from worker
            }

            logger.info(
                f"Successfully enriched {track_id} via m7i worker "
                f"| BPM: {feature_vec['bpm']} "
                f"| Tags: {feature_vec['mood_tags']}"
            )
            return track_id, feature_vec

        except Exception as e:
            logger.error(f"Pipeline failure for {track_id}: {repr(e)}")
            return track_id, None


async def _run_parallel_analysis(
    tracks_with_urls: dict[str, str],
) -> dict[str, FeatureVector]:
    """
    Fires all track analysis tasks concurrently against the m7i CPU worker.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async with httpx.AsyncClient() as client:
        tasks = [
            _process_track(client, track_id, preview_url, semaphore)
            for track_id, preview_url in tracks_with_urls.items()
        ]
        results = await asyncio.gather(*tasks)

    return {
        track_id: feature_vec
        for track_id, feature_vec in results
        if feature_vec is not None
    }


async def analyzer_node(state: EchoSeedState):
    """
    Analyzes all tracks in parallel by concurrently downloading previews and
    sending them to the m7i worker.
    """
    logger.info("Starting parallel audio analysis for %d tracks", len(state["tracks"]))

    # ── Pre-flight Worker Connection Test ──────────────────────────────────────
    logger.info(f"Testing worker connection at {HEALTH_URL}...")
    try:
        async with httpx.AsyncClient() as client:
            health_response = await client.get(HEALTH_URL, timeout=5.0)
            health_response.raise_for_status()
            logger.info(f"Worker connection successful: {health_response.json()}")
    except Exception as e:
        logger.error(f"Fatal: Cannot reach worker. Connection test failed: {repr(e)}")
        logger.error("Aborting analysis to prevent pipeline hang.")
        return {"features": {}}
    # ──────────────────────────────────────────────────────────────────────────

    preview_urls = state.get("preview_urls", {})

    tracks_with_urls = {
        track_id: preview_urls[track_id]
        for track_id in state["tracks"]
        if preview_urls.get(track_id)
    }

    skipped = len(state["tracks"]) - len(tracks_with_urls)
    if skipped:
        logger.warning(f"Skipping {skipped} tracks with no preview URL.")

    if not tracks_with_urls:
        logger.error("No preview URLs available. Returning empty features.")
        return {"features": {}}

    logger.info(
        f"Firing {len(tracks_with_urls)} tracks at the m7i concurrently "
        f"(max {MAX_CONCURRENT} in-flight at once)."
    )

    features_dict = await _run_parallel_analysis(tracks_with_urls)

    logger.info(
        f"Parallel analysis complete. "
        f"Enriched {len(features_dict)}/{len(tracks_with_urls)} tracks."
    )

    return {"features": features_dict}
