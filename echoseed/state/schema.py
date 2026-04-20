from typing import TypedDict, Any

class FeatureVector(TypedDict):
    track_id: str
    bpm: float
    key: str
    energy: float
    valence: float
    arousal: float
    brightness: float
    danceability: float
    mood_tags: list[str]
    embedding: list[float]

class EchoSeedState(TypedDict):
    playlist_id: str
    tracks: list[str]
    preview_urls: dict[str, str]
    features: dict[str, FeatureVector]