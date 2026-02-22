import json
from typing import TypedDict, Annotated
from langchain_core.messages import ToolMessage, SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.language_models import BaseChatModel

from .tools import get_athlete_stats, get_activities_in_range, get_activity_information

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

def reasoner_node(state: AgentState, llm_with_tools):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

def post_process_node(state: AgentState):
    """
    A deterministic node that runs after tools to calculate summaries (like counts)
    so the LLM doesn't have to count raw JSON lines.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if the last message is from our specific tool
    if isinstance(last_message, ToolMessage) and last_message.name == "get_activities_in_range":
        content = last_message.content
        if "No activities" not in content and "Error" not in content:
            # Parse JSONL to get stats
            lines = content.strip().split('\n')
            total_count = len(lines)
            
            # Count by type
            type_counts = {}
            for line in lines:
                try:
                    activity = json.loads(line)
                    a_type = activity.get("type", "Unknown")
                    type_counts[a_type] = type_counts.get(a_type, 0) + 1
                except json.JSONDecodeError:
                    continue

            # Format breakdown
            breakdown = ", ".join([f"{k}: {v}" for k, v in type_counts.items()])
            
            # Inject a system message with the hard fact to guide the LLM
            return {"messages": [SystemMessage(content=f"SYSTEM ANALYSIS: The tool returned {total_count} activities. Breakdown: {breakdown}. The full list with IDs is available in the context above for specific inquiries.")]}
    return {}

def route_tools(state: AgentState):
    """Determine if we need post-processing based on the last tool called."""
    messages = state["messages"]
    last_message = messages[-1]
    
    if isinstance(last_message, ToolMessage) and last_message.name == "get_activities_in_range":
        return "post_process"
    return "agent"

def build_graph(llm: BaseChatModel, tools: list = None):
    """Build the agent graph with the given LLM and tools."""
    if tools is None:
        tools = [get_athlete_stats, get_activities_in_range, get_activity_information]

    llm_with_tools = llm.bind_tools(tools)

    # Build Graph
    builder = StateGraph(AgentState)
    
    # Use a lambda or partial to pass the bound LLM to the node
    builder.add_node("agent", lambda state: reasoner_node(state, llm_with_tools))
    builder.add_node("tools", ToolNode(tools))
    builder.add_node("post_process", post_process_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_conditional_edges("tools", route_tools, ["post_process", "agent"])
    builder.add_edge("post_process", "agent")

    return builder.compile()

if __name__ == "__main__":
    # Allow running this file directly to visualize the graph
    # Usage: python -m strava_agent.graph
    from unittest.mock import MagicMock

    # Mock LLM to build graph without API keys
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = MagicMock()

    app = build_graph(mock_llm)
    print(app.get_graph().draw_mermaid())