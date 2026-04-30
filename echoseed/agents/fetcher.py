import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from echoseed.state.schema import EchoSeedState
from echoseed.tools.external_search import DeezerSearchTool

logger = logging.getLogger("preview_fetcher")

# Reuse a single thread pool across calls — avoids spawning a new pool per node run.
# Max workers is capped at 10 to avoid hammering the Deezer API.
_executor = ThreadPoolExecutor(max_workers=10)


async def _fetch_single(
    deezer: DeezerSearchTool,
    track_id: str,
    name: str,
    artist: str = "unknown artist",
) -> tuple[str, str | None]:
    """
    Runs a single blocking Deezer search in a thread so it doesn't block the
    event loop. Returns a (track_id, preview_url | None) tuple.
    """
    loop = asyncio.get_event_loop()
    logger.info(f"Searching Deezer for: {name} - {artist}")
    try:
        url = await loop.run_in_executor(
            _executor,
            lambda: deezer.get_preview_url(name, artist),
        )
        return track_id, url
    except Exception as e:
        logger.warning(f"Deezer search failed for {name} - {artist}: {e}")
        return track_id, None


async def _fetch_all_previews(
    deezer: DeezerSearchTool,
    tracks_needing_search: dict[str, dict],
) -> dict[str, str]:
    """
    Fires off all Deezer searches concurrently and collects results.
    Total wall time = slowest single request, not sum of all requests.
    """
    tasks = [
        _fetch_single(deezer, track_id, meta["name"], meta["artist"])
        for track_id, meta in tracks_needing_search.items()
    ]

    results = await asyncio.gather(*tasks)

    # Filter out tracks where no preview was found
    return {track_id: url for track_id, url in results if url}


async def fetcher_node(state: EchoSeedState):
    """
    Fetches preview URLs from Deezer for any tracks that Spotify didn't provide
    a preview for. All Deezer searches are fired in parallel, so total fetch time
    equals the duration of the single slowest request rather than the sum of all.
    """
    logger.info("Sourcing missing preview URLs from Deezer (parallel fetch).")

    deezer = DeezerSearchTool()
    preview_updates: dict[str, str] = {}
    tracks_needing_search: dict[str, dict] = {}

    track_metadata = state.get("track_metadata", {})

    for track_id in state["tracks"]:
        # Spotify already gave us a preview URL — nothing to do.
        existing_url = state.get("preview_urls", {}).get(track_id)
        if existing_url:
            preview_updates[track_id] = existing_url
            continue

        meta = track_metadata.get(track_id)
        if not meta:
            logger.warning(f"No metadata found for {track_id}, skipping Deezer search.")
            continue

        # Queue this track for parallel fetching
        tracks_needing_search[track_id] = meta

    # Run all Deezer searches concurrently
    if tracks_needing_search:
        logger.info(
            f"Firing {len(tracks_needing_search)} Deezer searches in parallel."
        )
        fetched = await _fetch_all_previews(deezer, tracks_needing_search)
        preview_updates.update(fetched)
        logger.info(
            f"Parallel fetch complete. "
            f"Found {len(fetched)}/{len(tracks_needing_search)} preview URLs."
        )

    return {"preview_urls": preview_updates}