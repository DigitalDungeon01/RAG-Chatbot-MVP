from typing import Annotated, List, Optional, TypedDict
from langgraph.graph.message import add_messages

class State(TypedDict):
    
    # entry point
    messages: Annotated[List[dict], add_messages] 
    
    # answer generator node
    answer: Optional[str]
    
    history_snapshots: list[dict] 
    
    # From semantic optimizer filter node
    optimized_query: Optional[str]
    
    # semantic search node
    retrieved_docs: Optional[List[dict]] 
    
    # evaluation node
    evaluation_feedback: Optional[str]
    confidence_score: Optional[float]
    iteration_count: int
    
    # online search node (mcp+llm)
    online_search_required: bool
    tavily_results: Optional[str]
    
    
    # csv export node(mcp+llm)
    csv_export_required: bool
    csv_export_results: Optional[str] # return filename
    
    # chart generator node(mcp+llm)
    chart_image_required: bool    
    chart_image_results: Optional[str] #retrn url
    
    # Guard Rail messages node
    safety_flag_messages: bool
    
    # Guard Rail answer node
    safety_flag_answer: bool
    
    hallucination_score: Optional[float]
    
    
    