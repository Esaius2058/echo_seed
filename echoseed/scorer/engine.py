import numpy as np
import logging
from echoseed.scorer.camelot import get_harmonic_score
from echoseed.state.schema import FeatureVector

logger = logging.getLogger("echoseed.scorer")

DEFAULT_WEIGHTS = {
    "embedding": 0.35,  
    "harmonic": 0.20,   
    "energy": 0.15,     
    "mood": 0.20,       
    "slope": 0.10       
}

def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    v1, v2 = np.array(vec1), np.array(vec2)
    if v1.size == 0 or v2.size == 0:
        return 0.0
    norm1, norm2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))

def _slope_compatibility(slope_a: float, slope_b: float) -> float:
    if slope_a < 0 and slope_b > 0:
        return 1.0 
    elif slope_a > 0 and slope_b > 0:
        return 0.5 
    elif slope_a < 0 and slope_b < 0:
        return 0.3 
    else:
        return 0.6 

def calculate_similarity(
    seed: FeatureVector, candidate: FeatureVector, weights: dict = DEFAULT_WEIGHTS
) -> dict:
    
    # 1. Acoustic Timbre
    sim_embedding = _cosine_similarity(seed["embedding"], candidate["embedding"])

    # 2. Harmonic Compatibility
    sim_harmonic = float(get_harmonic_score(seed.get("key", "Unknown"), candidate.get("key", "Unknown")))

    # 3. Energy Delta
    sim_energy = float(1.0 - abs(seed["energy"] - candidate["energy"]))

    # 4. Mood Delta (NumPy leak patched)
    v_diff = (seed["valence"] - candidate["valence"]) / 8.0
    a_diff = (seed["arousal"] - candidate["arousal"]) / 8.0
    mood_dist = float(np.sqrt(v_diff**2 + a_diff**2))
    sim_mood = float(max(0.0, 1.0 - (mood_dist / 1.414)))

    # 5. Energy Slope Compatibility
    sim_slope = float(_slope_compatibility(seed.get("slope", 0.0), candidate.get("slope", 0.0)))

    # Calculate weighted sum
    total_score = float(
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
            "mood": round(sim_mood, 3), # Bulletproof standard float
            "slope": round(sim_slope, 3)
        },
    }
