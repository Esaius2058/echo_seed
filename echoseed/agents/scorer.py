import logging
from echoseed.state.schema import EchoSeedState
from echoseed.scorer.engine import calculate_similarity

logger = logging.getLogger("echoseed.scorer_node")

def scorer_node(state: EchoSeedState):
    """
    Scores all analyzed tracks against a seed track and sorts them.
    For Phase 3, we default to using the first valid track as the 'Seed'.
    """
    logger.info("Starting Recommendation Scorer...")

    features = state.get("features", {})
    if len(features) < 2:
        logger.warning("Not enough analyzed tracks to perform similarity scoring.")
        return {"features": features}  # Need at least 2 tracks to compare

    # Grab the first track as the Seed
    seed_id = list(features.keys())[0]
    seed_features = features[seed_id]
    logger.info(f"Using Seed Track: {seed_id}")

    results = []

    for candidate_id, candidate_features in features.items():
        if candidate_id == seed_id:
            continue  # Don't score the seed against itself

        score_data = calculate_similarity(seed_features, candidate_features)

        results.append({
            "track_id": candidate_id,
            "score": score_data["total_score"],
            "breakdown": score_data["breakdown"]
        })

    # Sort candidates by total score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    # Optional: Log the top result to the console for a quick sanity check
    if results:
        top_match = results[0]
        logger.info(f"Top Match for Seed: {top_match['track_id']} with score {top_match['score']}")
        logger.info(f"Breakdown: {top_match['breakdown']}")

    # Return the sorted results (You can append this to your state schema if you want to store the order)
    return {"sorted_results": results}