from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from agents.state import AgentState
from agents.nodes import generate_sql_node, execute_sql_node, format_answer_node, evaluate_node
from colorama import Fore


def create_graph(db):
    """Create the LangGraph Workflow"""

    workflow = StateGraph(AgentState)

    # Add Nodes with db parameter
    workflow.add_node("generate_sql", lambda state: generate_sql_node(state, db))
    workflow.add_node("execute_sql", lambda state: execute_sql_node(state, db))
    workflow.add_node("format_answer", format_answer_node)
    workflow.add_node("evaluate", evaluate_node)

    # Define flow
    workflow.add_edge(START, "generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")

    # Conditional routing after execution
    def check_execution(state):
        if state.get("error") and state.get("retry_count", 0) < 2:
            return "generate_sql"  # Retry
        return "format_answer"

    workflow.add_conditional_edges(
        "execute_sql",
        check_execution,
        {"generate_sql": "generate_sql", "format_answer": "format_answer"},
    )

    workflow.add_edge("format_answer", "evaluate")
    workflow.add_edge("evaluate", END)

    # Compile
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app


print(f"{Fore.GREEN}Graph module loaded")