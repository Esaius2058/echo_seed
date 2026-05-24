from echoseed.state.schema import EchoSeedState
from echoseed.tools.tsp_solver import greedy_tsp
import logging

logger = logging.getLogger("echoseed.sequencer")


def sequencer_node(state: EchoSeedState) -> dict:
    score_matrix = state.get("score_matrix", {})

    if len(score_matrix) < 2:
        logger.warning("Not enough tracks to sequence...returning as-is.")
        return {"ordered_tracks": list(score_matrix.keys())}

    ordered = greedy_tsp(score_matrix)
    logger.info(f"Sequenced {len(ordered)} tracks.")

    # Temporary debug remove after testing
    for track_a, scores in score_matrix.items():
        best = max(scores, key=scores.get)
        logger.info(
            f"{track_a} → best transition: {best} "
            f"(score: {score_matrix[track_a][best]:.4f})"
        )

    return {"ordered_tracks": ordered}
