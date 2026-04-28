from typing import TypedDict, Any, List, Dict
from typing_extensions import NotRequired

class TrackMeta(TypedDict):
    name: str
    artist: str

class FeatureVector(TypedDict):
    track_id: str
    bpm: float
    key: str
    energy: float
    valence: NotRequired[float]
    arousal: NotRequired[float]
    brightness: NotRequired[float]
    danceability: NotRequired[float]
    mood_tags: NotRequired[list[str]]
    embedding: NotRequired[list[float]]

class EchoSeedState(TypedDict):
    playlist_id: str
    tracks: List[str]
    track_metadata: Dict[str, TrackMeta]
    preview_urls: Dict[str, str]
    features: Dict[str, FeatureVector]
