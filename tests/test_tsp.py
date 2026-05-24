from echoseed.tools.tsp_solver import greedy_tsp

def test_greedy_tsp_basic():
    matrix = {
        "A": {"B": 0.9, "C": 0.2, "D": 0.1},
        "B": {"A": 0.9, "C": 0.8, "D": 0.1},
        "C": {"A": 0.2, "B": 0.8, "D": 0.7},
        "D": {"A": 0.1, "B": 0.1, "C": 0.7},
    }
    result = greedy_tsp(matrix)
    assert len(result) == 4           # all tracks present
    assert len(set(result)) == 4      # no duplicates
    assert result == ["B", "A", "C", "D"]  # known optimal greedy path

def test_greedy_tsp_single_track():
    assert greedy_tsp({"A": {}}) == ["A"]

def test_greedy_tsp_empty():
    assert greedy_tsp({}) == []
