import logging
from echoseed.state.schema import EchoSeedState
from echoseed.tools.external_search import DeezerSearchTool

logger = logging.getLogger("preview_fetcher")

def fetcher_node(state: EchoSeedState):
    logger.info("Sourcing missing preview URLs from external APIs.")

    deezer = DeezerSearchTool()
    preview_updates = {}

    # We need the actual Track metadata.
    # Let's assume you pass the raw track objects or a dict of metadata in the state.
    # To keep it efficient, we iterate over the metadata map.
    track_metadata = state.get("track_metadata", {})

    for track_id in state["tracks"]:
        # If we already got lucky and Spotify provided one, skip.
        existing_url = state.get("preview_urls", {}).get(track_id)
        if existing_url:
            preview_updates[track_id] = existing_url
            continue

        meta = track_metadata.get(track_id)
        if not meta:
            logger.warning(f"No metadata found for {track_id} to perform search.")
            continue

        # Fetch from Deezer
        logger.info(f"Searching Deezer for: {meta['name']} - {meta['artist']}")
        found_url = deezer.get_preview_url(meta["name"], meta["artist"])

        if found_url:
            preview_updates[track_id] = found_url

    # We return the updated dictionary to merge into the LangGraph state
    return {"preview_urls": preview_updates}