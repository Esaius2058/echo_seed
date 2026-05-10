import numpy as np
import logging
from echoseed.scorer.camelot import get_harmonic_score
from echoseed.state.schema import FeatureVector

logger = logging.getLogger("echoseed.scorer")

# Default Algorithm Weights
# Tweak these based on how you want the playlist to transition
DEFAULT_WEIGHTS = {
    "embedding": 0.35,  # Acoustic texture / Timbre
    "harmonic": 0.20,   # Camelot mixing compatibility
    "energy": 0.15,     # Base Pace and intensity
    "mood": 0.20,       # Valence/Arousal emotional distance
    "slope": 0.10       # Handoff pacing (Building vs Fading)
}


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculates cosine similarity between two MERT vectors."""
    v1, v2 = np.array(vec1), np.array(vec2)
    if v1.size == 0 or v2.size == 0:
        return 0.0
    norm1, norm2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))


def _slope_compatibility(slope_a: float, slope_b: float) -> float:
    """
    A fading (negative slope) pairs with a building track
    (positive policy) - the energy handoff feels natural.
    """
    if slope_a < 0 and slope_b > 0:
        return 1.0 # perfect handoff
    elif slope_a > 0 and slope_b > 0:
        return 0.5 # both building — acceptable, slightly relentless
    elif slope_a < 0 and slope_b < 0:
        return 0.3 # both fading — playlist losing energy
    else:
        return 0.6 # A builds into B fading — decent, B will resolve

def calculate_similarity(
    seed: FeatureVector, candidate: FeatureVector, weights: dict = DEFAULT_WEIGHTS
) -> dict:
    """
    Scores a candidate track against a seed track across all dimensions.
    Returns the total score and the breakdown for debugging.
    """
    # 1. Acoustic Timbre (MERT)
    sim_embedding = _cosine_similarity(seed["embedding"], candidate["embedding"])

    # 2. Harmonic Compatibility
    sim_harmonic = get_harmonic_score(seed["key"], candidate["key"])

    # 3. Energy Delta (1.0 = exact match)
    sim_energy = 1.0 - abs(seed["energy"] - candidate["energy"])

    # 4. Mood Delta (Euclidean distance on V/A plane)
    # Normalize the 1-9 scale to 0-1 for distance math
    v_diff = (seed["valence"] - candidate["valence"]) / 8.0
    a_diff = (seed["arousal"] - candidate["arousal"]) / 8.0
    mood_dist = np.sqrt(v_diff**2 + a_diff**2)
    # Max distance is sqrt(1^2 + 1^2) = 1.414. Normalize to 0-1 similarity.
    sim_mood = max(0.0, 1.0 - (mood_dist / 1.414))
    # 5. Energy Slope Compatibility
    # Using .get() with a 0.0 fallback in case the worker hasn't been updated yet
    sim_slope = _slope_compatibility(seed.get("slope", 0.0), candidate.get("slope", 0.0))

    # Calculate weighted sum
    total_score = (
        (sim_embedding * weights["embedding"])
        + (sim_harmonic * weights["harmonic"])
        + (sim_energy * weights["energy"])
        + (sim_mood * weights["mood"])
        + (sim_slope * weights["slope"])
    )

    return {
        "total_score": round(total_score, 4),
        "breakdown": {
            "embedding": round(sim_embedding, 3),
            "harmonic": round(sim_harmonic, 3),
            "energy": round(sim_energy, 3),
            "mood": round(sim_mood, 3),
            "slope": round(sim_slope, 3)
        },
    }
