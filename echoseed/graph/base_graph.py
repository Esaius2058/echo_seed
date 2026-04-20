from langgraph.graph import StateGraph, END
from echoseed.state.schema import EchoSeedState

def dummy_node(state: EchoSeedState):
    """A placeholder node to verify graph execution and tracing."""
    playlist_id = state.get("playlist_id", "unknown")
    track_count = len(state.get("tracks", []))

    print(f"[Node Execution] Processing playlist {playlist_id}...")
    print(f"[Node Execution] Found {track_count} tracks.")

    # In a real node, you would return state updates here.
    # Returning an empty dict means no state mutations occurred.
    return {}

def build_graph():
    builder = StateGraph(EchoSeedState)

    # Add the node and define the routing
    builder.add_node("dummy", dummy_node)
    builder.set_entry_point("dummy")
    builder.add_edge("dummy", END)

    return builder.compile()