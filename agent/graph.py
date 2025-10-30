from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver # session memory
from state import State
from nodes import (guard_rail_messages, semantic_optimizer_filter, semantic_search, 
                  answer_generator, evaluation, hallucination_calculator, 
                  guard_rail_answer, tavily_search_node, csv_generator, chart_generator)
from mcp_tools.mcp_client import initialize_mcp

    
def route_after_guard_rail_messages(state: State) -> str:
    """Route after guard rail messages check"""
    if state.get('safety_flag_messages', False):
        return "end"  # End if safety flag is True (violating guidelines)
    return "semantic_optimizer_filter"


def route_after_answer_generator(state: State) -> str:
    """Route after answer_generator based on tool requirements"""
    
    # If csv export is required, go to csv generator
    if state.get('csv_export_required', False):
        return "csv_generator"
    
    # If chart image is required, go to chart generator
    if state.get('chart_image_required', False):
        return "chart_generator"
    
    # If online search is required, go to tavily search
    if state.get('online_search_required', False):
        return "tavily_search"
    
    # If no tools required, go to evaluation
    return "evaluation"


def route_after_evaluation(state: State) -> str:
    """Route after evaluation based on confidence and iteration count"""
    
    # If confidence < 0.6 and iteration < 2, retry with feedback
    if state.get('confidence_score', 0) < 0.6 and state.get('iteration_count', 0) < 2:
        return "answer_generator"
    
    # Otherwise go to hallucination calculator
    return "hallucination_calculator"


def route_after_tool_usage(state: State) -> str:
    """Route after tool usage (csv_generator, chart_generator, tavily_search)"""
    return "answer_generator"


def route_after_guard_rail_answer(state: State) -> str:
    """Route after final guard rail answer check"""
    return "end"




async def create_graph():
    
    # initialize mcp client with err handling
    try:
        await initialize_mcp()
    except Exception as e:
        print(f"MCP init failed: {e}")
        
    graph = StateGraph(State)
    
    # Add nodes
    graph.add_node("guard_rail_messages", guard_rail_messages)
    graph.add_node("semantic_optimizer_filter", semantic_optimizer_filter)
    graph.add_node("semantic_search", semantic_search)
    graph.add_node("answer_generator", answer_generator)
    graph.add_node("evaluation", evaluation)
    graph.add_node("hallucination_calculator", hallucination_calculator)
    graph.add_node("guard_rail_answer", guard_rail_answer)
    graph.add_node("tavily_search", tavily_search_node)
    graph.add_node("csv_generator", csv_generator)
    graph.add_node("chart_generator", chart_generator)
    
    
    # Set entry point
    graph.set_entry_point("guard_rail_messages")
    
    # Main flow: guard_rail_messages -> semantic_optimizer_filter -> semantic_search -> answer_generator -> evaluation
    graph.add_conditional_edges("guard_rail_messages", route_after_guard_rail_messages, {
        "semantic_optimizer_filter": "semantic_optimizer_filter",
        "end": END
    })
    
    graph.add_edge("semantic_optimizer_filter", "semantic_search")
    graph.add_edge("semantic_search", "answer_generator")
    
    # Conditional routing after answer_generator - tools go directly from answer_generator
    graph.add_conditional_edges("answer_generator", route_after_answer_generator, {
        "csv_generator": "csv_generator",
        "chart_generator": "chart_generator", 
        "tavily_search": "tavily_search",
        "evaluation": "evaluation"
    })
    
    # Conditional routing after evaluation
    graph.add_conditional_edges("evaluation", route_after_evaluation, {
        "answer_generator": "answer_generator",  # retry path
        "hallucination_calculator": "hallucination_calculator"
    })
    
    # Tool usage paths - after using tools, go back to answer_generator
    graph.add_conditional_edges("tavily_search", route_after_tool_usage, {
        "answer_generator": "answer_generator"
    })
    graph.add_conditional_edges("csv_generator", route_after_tool_usage, {
        "answer_generator": "answer_generator"
    })
    graph.add_conditional_edges("chart_generator", route_after_tool_usage, {
        "answer_generator": "answer_generator"
    })
    
    # evaluation routes directly to hallucination_calculator via conditional edges
    
    # Final flow: hallucination_calculator -> guard_rail_answer -> end
    graph.add_edge("hallucination_calculator", "guard_rail_answer")
    graph.add_conditional_edges("guard_rail_answer", route_after_guard_rail_answer, {
        "end": END
    })
    
    memory = MemorySaver() # session memory checkpointer
    return graph.compile(checkpointer=memory)