import os
import logging
from dotenv import load_dotenv
from echoseed.api.auth import SpotifyAuthService
from echoseed.security.token_manager import TokenManager
from echoseed.security.network_monitor import NetworkMonitor
from echoseed.ui.cli import PlaylistCLI
from echoseed.api.playlist_service import SpotifyPlaylistService
# LangGraph imports
from echoseed.graph.base_graph import build_graph

load_dotenv()
logger = logging.getLogger("EchoSeed")

# Setup basic logging config if not already done elsewhere
logging.basicConfig(level=logging.INFO)

def check_langsmith_config():
    """Fail fast if tracing is not configured."""
    if not os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGCHAIN_TRACING_V2") != "true":
        logger.error("LangSmith environment variables are missing. Tracing will fail.")
        raise ValueError("Configure LANGCHAIN_API_KEY and LANGCHAIN_TRACING_V2 in your .env")


def main():
    try:
        # 1. Enforce Phase 1 Requirements
        check_langsmith_config()

        # 2. Authenticate and get spotify client
        secret_key = os.getenv("SECRET_KEY", "default_secret_for_dev").encode()
        auth_service = SpotifyAuthService()
        auth_service.authenticate()
        spotify_client = auth_service.get_spotify_client()
        access_token = auth_service.get_access_token()

        token_manager = TokenManager(secret_key)
        logger.info("Saving Access Token...")
        token_manager.save_token(access_token)

        network_monitor = NetworkMonitor(refresh_callback=auth_service.refresh_access_token)
        network_monitor.run()

        logger.info("CLI initialized")

        playlist_service = SpotifyPlaylistService(spotify_client)
        playlist_name = input("Enter the name of the playlist to mix: ")
        playlist_id = playlist_service.get_playlist_id(playlist_name)

        # This returns a List[Track] based on your provided function
        all_track_objects = playlist_service.get_playlist_tracks(playlist_id)

        test_tracks = all_track_objects[:5]
        logger.info(f"Limiting analysis to {len(test_tracks)} tracks for testing.")
        # LangGraph Orchestration
        logger.info("Initializing LangGraph state...")

        # extract only the IDs for the main 'tracks' list
        track_ids = [t.id for t in test_tracks]

        # populate metadata for the fetcher agent
        track_metadata = {
            t.id: {"name": t.name, "artist": t.artist}
            for t in test_tracks
        }

        # create a mapping for the analyzer to find the audio files
        preview_urls = {t.id: t.preview_url for t in test_tracks if t.preview_url}

        initial_state = {
            "playlist_id": playlist_id,
            "tracks": track_ids,
            "track_metadata": track_metadata,
            "preview_urls": preview_urls,
            "features": {}
        }

        logger.info("Building and Compiling Graph...")
        logger.info(f"${len(preview_urls)} preview urls found")
        graph = build_graph()

        logger.info("Invoking LangGraph Pipeline...")
        result = graph.invoke(initial_state)

        logger.info("--- Analysis Complete ---")

        # Verify how many tracks were successfully analyzed
        analyzed_features = result.get("features", {})
        logger.info(f"Successfully extracted features for {len(analyzed_features)} tracks.")

        # Print a sample to ensure the embedding and math features are present
        if analyzed_features:
            sample_id = list(analyzed_features.keys())[0]
            logger.info(f"Sample Metadata for {sample_id}: {analyzed_features[sample_id]}")

    except Exception as e:
        logger.error("Application failed: %s", str(e))
        exit(1)


if __name__ == "__main__":
    main()