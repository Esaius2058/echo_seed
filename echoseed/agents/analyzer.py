import logging
from echoseed.state.schema import EchoSeedState, FeatureVector
from echoseed.tools.audio_utils import download_and_resample
from echoseed.tools.hf_client import HFClient
from echoseed.tools.librosa_tools import extract_local_features
from echoseed.api.auth import SpotifyAuthService
from echoseed.api.playlist_service import SpotifyPlaylistService

logger = logging.getLogger("audio_analyzer")

def analyzer_node(state: EchoSeedState):
    logger.info("Starting audio analysis for %d tracks", len(state["tracks"]))
    hf = HFClient()
    features_dict = {}

    for track_id in state["tracks"]:
        logger.info(f"Extracting features for: {track_id}")

        preview_map = state.get("preview_urls", {})
        preview_url = preview_map.get(track_id)

        if not preview_url:
            logger.warning(f"No preview URL for {track_id}. Skipping.")
            continue

        try:
            audio_bytes = download_and_resample(preview_url, target_str=24000)
            local_feats = extract_local_features(audio_bytes)

            # HuggingFace Calls
            embedding = hf.get_mert_embedding(audio_bytes)

            # Construct the final vector
            feature_vec: FeatureVector = {
                "track_id": track_id,
                "bpm": local_feats["bpm"],
                "key": "Unknown",
                # Key extraction requires a chromagram matrix analysis, best left out unless strictly required for DJ mixing
                "energy": local_feats["energy"],
                "valence": emotion_data["valence"],
                "arousal": emotion_data["arousal"],
                "brightness": local_feats["brightness"],
                "danceability": local_feats["danceability"],
                "mood_tags": emotion_data["mood_tags"],
                "embedding": embedding
            }

            features_dict[track_id] = feature_vec
            logger.info(f"Successfully generated feature vector for {track_id}")

        except Exception as e:
            logger.error(f"Failed to process {track_id}: {e}")
            continue

    # Return the dictionary to update the graph state
    return {"features": features_dict}