import pytest
from unittest.mock import MagicMock
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
from strava_agent.graph import post_process_node, route_tools, build_graph

def test_post_process_node_analysis():
    """Test that post_process_node correctly analyzes JSONL output from tools."""
    # Simulate output from get_activities_in_range
    tool_output = '{"type": "Run", "id": 1}\n{"type": "Ride", "id": 2}\n{"type": "Run", "id": 3}'
    
    message = ToolMessage(
        content=tool_output,
        tool_call_id="call_123",
        name="get_activities_in_range"
    )
    
    state = {"messages": [message]}
    result = post_process_node(state)
    
    assert "messages" in result
    system_msg = result["messages"][0]
    assert isinstance(system_msg, SystemMessage)
    assert "SYSTEM ANALYSIS" in system_msg.content
    assert "3 activities" in system_msg.content
    assert "Run: 2" in system_msg.content
    assert "Ride: 1" in system_msg.content

def test_post_process_node_skip():
    """Test that post_process_node skips for other tools."""
    message = ToolMessage(content="stats", tool_call_id="1", name="get_athlete_stats")
    state = {"messages": [message]}
    result = post_process_node(state)
    assert result == {}

def test_route_tools():
    """Test routing logic."""
    # Should route to post_process if it's the activities tool
    msg1 = ToolMessage(content="...", tool_call_id="1", name="get_activities_in_range")
    assert route_tools({"messages": [msg1]}) == "post_process"
    
    # Should route to agent for other tools
    msg2 = ToolMessage(content="...", tool_call_id="2", name="get_athlete_stats")
    assert route_tools({"messages": [msg2]}) == "agent"

def test_build_graph():
    """Smoke test to ensure graph builds without errors."""
    mock_llm = MagicMock()
    app = build_graph(mock_llm)
    assert app is not None