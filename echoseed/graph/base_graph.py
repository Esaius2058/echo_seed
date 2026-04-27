from langgraph.graph import StateGraph, END
from echoseed.state.schema import EchoSeedState
from echoseed.agents.analyzer import analyzer_node
from echoseed.agents.fetcher import fetcher_node

def build_graph():
    builder = StateGraph(EchoSeedState)

    # Add the node and define the routing
    builder.add_node("fetcher", fetcher_node)
    builder.add_node("analyzer", analyzer_node)
    builder.set_entry_point("fetcher")
    builder.add_edge("fetcher", "analyzer")
    builder.add_edge("analyzer", END)

    return builder.compile()