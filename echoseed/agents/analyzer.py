import logging
from echoseed.state.schema import EchoSeedState, FeatureVector
from echoseed.tools.audio_utils import download_and_resample
from echoseed.tools.hf_client import HFClient
from echoseed.tools.librosa_tools import extract_local_features
from echoseed.api.auth import SpotifyAuthService
from echoseed.api.playlist_service import SpotifyPlaylistService

logger = logging.getLogger(__name__)

def analyzer_node(state: EchoSeedState):
    logger.info("[Analyzer] Starting audio analysis for %d tracks", len(state["tracks"]))
    hf = HFClient()
    features_dict = {}
    sp = SpotifyAuthService()
    sp_client = sp.get_spotify_client()
    playlist_service = SpotifyPlaylistService(sp_client)


    for track_id in state["tracks"]:
        logger.info(f"[Analyzer] Extracting features for: {track_id}")


        preview_url = "YOUR_FETCHED_PREVIEW_URL"

        if not preview_url:
            logger.warning(f"[Analyzer] No preview URL for {track_id}. Skipping.")
            continue

        try:
            audio_bytes = download_and_resample(preview_url)
            local_feats = extract_local_features(audio_bytes)

            # HuggingFace Calls
            embedding = hf.get_mert_embedding(audio_bytes)

            # Construct the final vector
            feature_vec: FeatureVector = {
                "track_id": track_id,
                "bpm": 120.0,  # Replace with actual HF tempo call
                "key": "C major",  # Replace with actual HF key call
                "energy": local_feats["energy"],
                "valence": 5.0,  # Replace with actual HF emo call
                "arousal": 5.0,  # Replace with actual HF emo call
                "brightness": local_feats["brightness"],
                "danceability": local_feats["danceability"],
                "mood_tags": ["neutral"],  # Replace with actual HF emo call
                "embedding": embedding
            }
            features_dict[track_id] = feature_vec

        except Exception as e:
            logger.error(f"[Analyzer] Failed to process {track_id}: {e}")
            continue

    # Return the dictionary to update the graph state
    return {"features": features_dict}