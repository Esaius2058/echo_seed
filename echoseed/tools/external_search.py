import httpx
import logging
import urllib.parse
import re

logger = logging.getLogger(__name__)


class DeezerSearchTool:
    def __init__(self):
        # Use a shared client with a realistic browser User-Agent.
        # Deezer occasionally blocks requests that look like raw scripts.
        self.client = httpx.Client(
            timeout=10.0,
            headers={"User-Agent": "Mozilla/5.0 (compatible; EchoSeed/1.0)"},
            follow_redirects=True,
        )
        self.base_url = "https://api.deezer.com/search"

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _clean(text: str) -> str:
        """
        Strip content inside parentheses / brackets and common suffixes that
        confuse Deezer's matcher (e.g. "Blinding Lights (Radio Edit)" → "Blinding Lights").
        """
        text = re.sub(r"[\(\[\{][^\)\]\}]*[\)\]\}]", "", text)
        text = re.sub(r"\s*-\s*(feat|ft|with|prod)\.?.*", "", text, flags=re.IGNORECASE)
        return text.strip()

    def _search(self, query: str) -> str | None:
        """Single Deezer search attempt. Returns preview URL or None."""
        encoded = urllib.parse.quote(query)
        url = f"{self.base_url}?q={encoded}&limit=5"

        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()

        for track in data.get("data", []):
            preview = track.get("preview")
            if preview:
                return preview

        return None

    # ── public API ────────────────────────────────────────────────────────────

    def get_preview_url(self, track_name: str, artist_name: str) -> str | None:
        """
        Searches Deezer for a track and returns the 30s preview URL.

        Uses a two-pass strategy:
          Pass 1 — plain freetext query (most reliable against Deezer's API).
          Pass 2 — cleaned query with parenthetical suffixes removed, in case
                   the original name was too specific to match.
        """
        try:
            # Pass 1: plain freetext — Deezer handles this far better than
            # the structured track:"..." artist:"..." syntax.
            query = f"{track_name} {artist_name}"
            preview = self._search(query)
            if preview:
                return preview

            # Pass 2: strip suffixes like "(Remix)", "[Live]", "feat. X" and retry.
            clean_name = self._clean(track_name)
            clean_artist = self._clean(artist_name)
            clean_query = f"{clean_name} {clean_artist}"

            if clean_query != query:
                logger.info(f"Pass 1 failed, retrying with cleaned query: '{clean_query}'")
                preview = self._search(clean_query)
                if preview:
                    return preview

            logger.warning(f"Deezer found no preview for: {track_name} by {artist_name}")
            return None

        except Exception as e:
            logger.error(f"Deezer API error for '{track_name}': {e}")
            return None