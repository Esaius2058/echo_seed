from statistics import mean

def greedy_tsp(score_matrix: dict[str, dict[str, float]]) -> list[str]:
    """
    Greedy nearest-neighbour TSP solver.
    Starts at the track with the highest average outgoing score,
    then at each step picks the unvisited track with the best
    transition score from the current track.
    """
    if not score_matrix:
        return []

    if len(score_matrix) == 1:
        return list(score_matrix.keys())

    # Start at the track with the best average outgoing compatibility
    start   = max(score_matrix, key=lambda t: mean(score_matrix[t].values()))
    ordered = [start]
    visited = {start}
    current = start

    while len(ordered) < len(score_matrix):
        candidates = {
            t: score_matrix[current][t]
            for t in score_matrix[current]
            if t not in visited
        }
        next_track = max(candidates, key=candidates.get)
        ordered.append(next_track)
        visited.add(next_track)
        current = next_track

    return ordered
