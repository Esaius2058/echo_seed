from typing import Optional
from pydantic import BaseModel


class Track(BaseModel):
    id: str
    name: str
    artist: str
    album: str
    duration_ms: int
    preview_url: Optional[str] = None  # Crucial for Phase 2 analysis

    @classmethod
    def from_spotify_dict(cls, data: dict):
        """Helper to parse raw Spotify API response into our model."""
        # Spotify nests track data differently depending on the endpoint
        track_info = data.get('track', data)

        return cls(
            id=track_info.get('id'),
            name=track_info.get('name'),
            artist=track_info.get('artists', [{}])[0].get('name', 'Unknown Artist'),
            album=track_info.get('album', {}).get('name', 'Unknown Album'),
            duration_ms=track_info.get('duration_ms', 0),
            preview_url=track_info.get('preview_url')
        )