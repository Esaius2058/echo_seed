import logging

logger = logging.getLogger("echoseed.camelot")

CAMELOT_MAP = {
    # Minor Keys (A)
    "g# minor": (1, 0), "ab minor": (1, 0), "d# minor": (2, 0), "eb minor": (2, 0),
    "a# minor": (3, 0), "bb minor": (3, 0), "f minor": (4, 0), "c minor": (5, 0),
    "g minor": (6, 0), "d minor": (7, 0), "a minor": (8, 0), "e minor": (9, 0),
    "b minor": (10, 0), "f# minor": (11, 0), "gb minor": (11, 0), "c# minor": (12, 0),
    "db minor": (12, 0),
    # Major Keys (B)
    "b major": (1, 1), "f# major": (2, 1), "gb major": (2, 1), "c# major": (3, 1),
    "db major": (3, 1), "g# major": (4, 1), "ab major": (4, 1), "d# major": (5, 1),
    "eb major": (5, 1), "a# major": (6, 1), "bb major": (6, 1), "f major": (7, 1),
    "c major": (8, 1), "g major": (9, 1), "d major": (10, 1), "a major": (11, 1),
    "e major": (12, 1),
}

def _normalize_key(raw_key: str) -> str:
    """Forces the worker's key string into the exact dictionary format."""
    return str(raw_key).lower().strip()

def get_harmonic_score(key1: str, key2: str) -> float:
    """
    Calculates DJ harmonic compatibility between two keys.
    Returns a float between 0.0 (Clash) and 1.0 (Perfect Match).
    """
    if key1 == "Unknown" or key2 == "Unknown":
        return 0.5 

    k1 = _normalize_key(key1)
    k2 = _normalize_key(key2)

    val1 = CAMELOT_MAP.get(k1)
    val2 = CAMELOT_MAP.get(k2)

    if not val1 or not val2:
        logger.warning(f"Camelot map miss: '{k1}' or '{k2}'. Returning 0.5.")
        return 0.5

    hour1, mode1 = val1
    hour2, mode2 = val2

    # Calculate shortest path around the 12-hour clock face
    hour_diff = min(abs(hour1 - hour2), 12 - abs(hour1 - hour2))
    mode_diff = abs(mode1 - mode2)

    # DJ Mixing Rules Scoring
    if hour_diff == 0 and mode_diff == 0:
        return 1.0  # Exact match (e.g., 8A to 8A)
    elif hour_diff == 1 and mode_diff == 0:
        return 0.8  # Adjacent hour, same mode (e.g., 8A to 9A)
    elif hour_diff == 0 and mode_diff == 1:
        return 0.7  # Same hour, mode swap (e.g., 8A to 8B)
    elif hour_diff == 1 and mode_diff == 1:
        return 0.5  # Diagonal mix
    elif hour_diff == 2 and mode_diff == 0:
        return 0.4  # +2 Energy Boost mix
    else:
        # Graceful degradation for distant keys instead of flatlining at 0.0
        return max(0.0, 0.4 - (hour_diff * 0.08))

if __name__ == "__main__":
    print(f"C minor -> C minor: {get_harmonic_score('C minor', 'c minor')}")  
    print(f"C minor -> G minor: {get_harmonic_score('C minor', 'G minor')}")  
    print(f"C minor -> Eb major: {get_harmonic_score('C minor', 'Eb major')}") 
    print(f"C minor -> F# minor: {get_harmonic_score('C minor', 'F# minor')}")
