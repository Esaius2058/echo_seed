from langgraph.graph import StateGraph, END
from echoseed.state.schema import EchoSeedState
from echoseed.agents.analyzer import analyzer_node
from echoseed.agents.fetcher import fetcher_node
from echoseed.agents.scorer import scorer_node
from echoseed.agents.sequencer import sequencer_node

def build_graph():
    builder = StateGraph(EchoSeedState)

    # Add the node and define the routing
    builder.add_node("fetcher", fetcher_node)
    builder.add_node("analyzer", analyzer_node)
    builder.add_node("scorer", scorer_node)
    builder.add_node("sequencer", sequencer_node)
    builder.set_entry_point("fetcher")
    builder.add_edge("fetcher", "analyzer")
    builder.add_edge("analyzer", "scorer")
    builder.add_edge("scorer", "sequencer")
    builder.add_edge("sequencer", END)

    return builder.compile()
