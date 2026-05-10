import os
import asyncio
import logging
from dotenv import load_dotenv
from echoseed.api.auth import SpotifyAuthService
from echoseed.security.token_manager import TokenManager
from echoseed.api.playlist_service import SpotifyPlaylistService
from echoseed.graph.base_graph import build_graph

load_dotenv()
logger = logging.getLogger("EchoSeed")
logging.basicConfig(level=logging.INFO)


async def run_test_pipeline():
    try:
        # 1. Auth Setup
        secret_key = os.getenv("SECRET_KEY", "default_secret_for_dev").encode()
        auth_service = SpotifyAuthService()
        auth_service.authenticate()

        spotify_client = auth_service.get_spotify_client()
        playlist_service = SpotifyPlaylistService(spotify_client)

        # 2. Target Selection
        playlist_name = input("Enter playlist name for the 5-track test: ")
        playlist_id = playlist_service.get_playlist_id(playlist_name)
        all_tracks = playlist_service.get_playlist_tracks(playlist_id)

        test_tracks = all_tracks[:5]
        logger.info(f"Testing pipeline with: {[t.name for t in test_tracks]}")

        # 3. Initial State
        initial_state = {
            "playlist_id": playlist_id,
            "tracks": [t.id for t in test_tracks],
            "track_metadata": {
                t.id: {"name": t.name, "artist": t.artist} for t in test_tracks
            },
            "preview_urls": {},
            "features": {},
        }

        # 4. Graph Execution
        graph = build_graph()
        logger.info("Invoking LangGraph (Async)...")
        result = await graph.ainvoke(initial_state)

        # 5. Validation (Phase 3: Scorer Results)
        sorted_results = result.get("sorted_results", [])

        if not sorted_results:
            logger.error(
                "No sorted results returned. Something went wrong in the scorer."
            )
            return

        logger.info(f"Test Complete. Scored {len(sorted_results)} candidates.")

        # Get the seed track info from the state features
        features = result.get("features", {})
        if not features:
            logger.error("No features returned to identify the seed track.")
            return

        seed_id = list(features.keys())[0]
        seed_name = result["track_metadata"][seed_id]["name"]

        print(f"\n--- SEED TRACK: {seed_name} ---")

        for rank, match in enumerate(sorted_results, 1):
            tid = match["track_id"]
            name = result["track_metadata"][tid]["name"]
            score = match["score"]
            breakdown = match["breakdown"]

            print(f"\n#{rank}: {name} (Total Score: {score})")
            print(
                f"  └─ Timbre: {breakdown['embedding']} | Harmonic: {breakdown['harmonic']} | Energy: {breakdown['energy']} | Mood: {breakdown['mood']}"
            )

    except Exception as e:
        logger.error(f"Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(run_test_pipeline())
