import asyncio
import httpx
import logging
from echoseed.state.schema import EchoSeedState, FeatureVector

logger = logging.getLogger("audio_analyzer")

WORKER_URL = "http://10.10.10.2:8000/analyze"

# How many tracks to send to the MI300X concurrently.
# The GPU can handle more but this avoids overwhelming the T3's outbound bandwidth.
MAX_CONCURRENT = 5


async def _process_track(
    client: httpx.AsyncClient,
    track_id: str,
    preview_url: str,
    semaphore: asyncio.Semaphore,
) -> tuple[str, FeatureVector | None]:
    """
    Downloads the preview and sends it to the MI300X worker concurrently.
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

            # ── 2. Send to MI300X worker for heavy inference ───────────────────
            worker_response = await client.post(
                WORKER_URL,
                files={"file": (f"{track_id}.mp3", audio_bytes, "audio/mpeg")},
                timeout=45.0,  # MERT inference needs breathing room
            )

            if worker_response.status_code != 200:
                logger.error(
                    f"Worker failed for {track_id}: {worker_response.text}"
                )
                return track_id, None

            data = worker_response.json()

            # ── 3. Build the FeatureVector ─────────────────────────────────────
            feature_vec: FeatureVector = {
                "track_id":    track_id,
                "bpm":         data["bpm"],
                "embedding":   data["embedding"],
                "key":         "Unknown",
                "arousal":     0.5,
                "valence":     0.5,
                "brightness":  0.0,
                "danceability":0.5,
                "energy":      0.5,
                "mood_tags":   ["pending_full_analysis"],
            }

            logger.info(f"Successfully enriched {track_id} via MI300X worker.")
            return track_id, feature_vec

        except Exception as e:
            logger.error(f"Pipeline failure for {track_id}: {e}")
            return track_id, None


async def _run_parallel_analysis(
    tracks_with_urls: dict[str, str],
) -> dict[str, FeatureVector]:
    """
    Fires all track analysis tasks concurrently against the MI300X worker.
    Wall time = slowest single track, not the sum of all tracks.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # Single shared client for all requests — efficient connection pooling
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


def analyzer_node(state: EchoSeedState):
    """
    Analyzes all tracks in parallel by concurrently downloading previews and
    sending them to the MI300X worker. The GPU processes multiple batches
    simultaneously instead of sitting idle between sequential requests.
    """
    logger.info(
        "Starting parallel audio analysis for %d tracks", len(state["tracks"])
    )

    preview_urls = state.get("preview_urls", {})

    # Separate tracks that have a preview URL from those that don't
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
        f"Firing {len(tracks_with_urls)} tracks at the MI300X concurrently "
        f"(max {MAX_CONCURRENT} in-flight at once)."
    )

    features_dict = asyncio.run(_run_parallel_analysis(tracks_with_urls))

    logger.info(
        f"Parallel analysis complete. "
        f"Enriched {len(features_dict)}/{len(tracks_with_urls)} tracks."
    )

    return {"features": features_dict}
