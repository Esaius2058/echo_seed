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
    valence: float
    arousal: float
    brightness: float
    danceability: float
    slope: float             # NEW: Captures if the track is building (+) or fading (-)
    mood_tags: list[str]
    embedding: list[float]


class EchoSeedState(TypedDict):
    playlist_id: str
    tracks: List[str]
    track_metadata: Dict[str, TrackMeta]
    preview_urls: Dict[str, str]
    features: Dict[str, FeatureVector]
    sorted_results: NotRequired[List[Dict[str, Any]]]  # NEW: Stores the output of the scorer node