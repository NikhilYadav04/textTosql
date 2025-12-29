from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Simple state for pipeline"""

    messages: Annotated[List, add_messages]
    user_query: str
    schema: str
    sql_query: Optional[str]
    results: Optional[dict]
    answer: Optional[str]
    error: Optional[str]
    retry_count: int
    evaluation_score : Optional[float]