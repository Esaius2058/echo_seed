from typing import TypedDict, Any, List, Dict
from typing_extensions import NotRequired


class TrackMeta(TypedDict):
    name: str
    artist: str


class FeatureVector(TypedDict):
    track_id: str
<<<<<<< HEAD
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
=======
    intro_bpm: float
    outro_bpm: float
    intro_energy: float
    outro_energy: float
    intro_brightness: float
    outro_brightness: float
    intro_danceability: float
    outro_danceability: float
    intro_embed: list[float]
    outro_embed: list[float]
>>>>>>> 6317959 (fix)


class EchoSeedState(TypedDict):
<<<<<<< HEAD
    playlist_id: str
    tracks: List[str]
    track_metadata: Dict[str, TrackMeta]
    preview_urls: Dict[str, str]
    features: Dict[str, FeatureVector]
    sorted_results: NotRequired[List[Dict[str, Any]]]  # NEW: Stores the output of the scorer node
    ordered_tracks: list[str]
=======
    playlist_id:    str
    tracks:         list[str]
    track_metadata: dict[str, dict]
    preview_urls:   dict[str, str]
    features:       dict[str, FeatureVector]
>>>>>>> 6317959 (fix)
