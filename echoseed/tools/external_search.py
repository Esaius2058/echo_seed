import httpx
import logging
import urllib.parse

logger = logging.getLogger(__name__)

class DeezerSearchTool:
    def __init__(self):
        self.client = httpx.Client(timeout=10.0)
        self.base_url = "https://api.deezer.com/search"

    def get_preview_url(self, track_name: str, artist_name: str) -> str | None:
        """Searches Deezer for a track and returns the 30s preview URL."""
        # Clean up the query to improve match rates
        query = f'track:"{track_name}" artist:"{artist_name}"'
        encoded_query = urllib.parse.quote(query)
        url = f"{self.base_url}?q={encoded_query}&limit=1"

        try:
            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()

            if data.get("data") and len(data["data"]) > 0:
                preview = data["data"][0].get("preview")
                if preview:
                    return preview

            logger.warning(f"Deezer found no preview for: {track_name} by {artist_name}")
            return None

        except Exception as e:
            logger.error(f"Deezer API failed for {track_name}: {e}")
            return None