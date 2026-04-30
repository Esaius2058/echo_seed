import requests
import io
import logging
from echoseed.state.schema import EchoSeedState, FeatureVector

logger = logging.getLogger("audio_analyzer")

# Use the Private IP of your m7i instance
WORKER_URL = "http://10.0.10.180:8000/analyze"

def analyzer_node(state: EchoSeedState):
    logger.info("Starting audio analysis for %d tracks", len(state["tracks"]))
    features_dict = {}

    for track_id in state["tracks"]:
        preview_url = state.get("preview_urls", {}).get(track_id)

        if not preview_url:
            logger.warning(f"No preview URL for {track_id}. Skipping.")
            continue

        try:
            # 1. Download preview
            audio_response = requests.get(preview_url, timeout=10)

            # Check if the request actually succeeded
            if audio_response.status_code != 200:
                logger.error(f"Deezer download failed ({audio_response.status_code}) for {track_id}")
                continue

            audio_bytes = audio_response.content

            # Print the first 10 bytes to verify it's an MP3
            # MP3 files usually start with 'ID3' (hex: 49 44 33) or 0xFF 0xFB
            logger.info(f"First bytes for {track_id}: {audio_bytes[:10]}")

            if b'<!DOCTYPE' in audio_bytes or b'<html' in audio_bytes:
                logger.error(f"Received HTML instead of audio for {track_id}. URL might be expired.")
                continue

            # 2. Hit the m7i Worker for the heavy math
            # This returns BOTH the BPM and the Embedding
            worker_response = requests.post(
                WORKER_URL,
                files={'file': (f"{track_id}.mp3", audio_bytes, 'audio/mpeg')},
                timeout=45  # Heavy AI inference needs a long timeout
            )

            if worker_response.status_code != 200:
                logger.error(f"Worker failed for {track_id}: {worker_response.text}")
                continue

            data = worker_response.json()

            # 3. Construct the FeatureVector
            # Note: Set defaults for things the worker doesn't provide yet
            feature_vec: FeatureVector = {
                "track_id": track_id,
                "bpm": data["bpm"],
                "embedding": data["embedding"],
                "key": "Unknown",
                # Padding missing keys with neutral defaults so the TypedDict is happy
                "arousal": 0.5,
                "valence": 0.5,
                "brightness": 0.0,
                "danceability": 0.5,
                "energy": 0.5,
                "mood_tags": ["pending_full_analysis"]
            }

            features_dict[track_id] = feature_vec
            logger.info(f"Successfully enriched {track_id} via m7i worker.")

        except Exception as e:
            logger.error(f"Pipeline failure for {track_id}: {e}")
            continue

    return {"features": features_dict}