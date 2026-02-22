import pytest
import json
import asyncio
from unittest.mock import MagicMock
from strava_agent.tools import get_athlete_stats, get_activities_in_range, get_activity_information

def test_get_athlete_stats(mock_env_vars, mock_strava_client):
    """Test fetching athlete stats."""
    # Setup mock return values
    mock_stats = MagicMock()
    mock_stats.biggest_ride_distance = 120000.0  # 120 km
    mock_stats.all_run_totals.distance = 50000.0 # 50 km
    mock_strava_client.get_athlete_stats.return_value = mock_stats
    
    # Invoke tool
    result = get_athlete_stats.invoke({})
    
    # Verify
    assert "Biggest Ride: 120.0km" in result
    assert "All-time Run Distance: 50.0km" in result

def test_get_activities_in_range(mock_env_vars, mock_strava_client):
    """Test fetching activities in a date range."""
    # Setup mock activity
    mock_activity = MagicMock()
    mock_activity.id = 123
    mock_activity.name = "Morning Run"
    mock_activity.type = "Run"
    mock_activity.distance = 5000.0
    mock_activity.start_date_local.isoformat.return_value = "2023-01-01T10:00:00"
    
    mock_strava_client.get_activities.return_value = [mock_activity]
    
    # Invoke tool
    result = get_activities_in_range.invoke({"start_date": "2023-01-01", "end_date": "2023-01-02"})
    
    # Verify result is a JSONL string
    # Parse the first line of JSONL to verify structure
    data = json.loads(result.split('\n')[0])
    assert data["name"] == "Morning Run"
    assert data["id"] == 123
    assert data["distance_km"] == 5.0

def test_get_activities_in_range_empty(mock_env_vars, mock_strava_client):
    """Test fetching activities when none exist."""
    mock_strava_client.get_activities.return_value = []
    result = get_activities_in_range.invoke({"start_date": "2023-01-01", "end_date": "2023-01-02"})
    assert "No activities found" in result

def test_get_activity_information(mock_env_vars, mock_strava_client):
    """Test fetching detailed activity information (Async)."""
    # Setup mock activity
    mock_activity = MagicMock()
    mock_activity.id = 456
    mock_activity.name = "Long Ride"
    mock_activity.type = "Ride"
    mock_activity.distance = 20000.0
    mock_activity.start_date_local.isoformat.return_value = "2023-01-01T10:00:00"
    mock_activity.elapsed_time = 3600
    mock_activity.average_speed = 10.0 # m/s

    # Since the tool uses asyncio.to_thread to call the client, we mock the client call
    mock_strava_client.get_activity.return_value = mock_activity

    # Run async test
    result = asyncio.run(get_activity_information.ainvoke({"activity_id": 456}))
    
    # Parse result
    data = json.loads(result)
    
    assert data["id"] == 456
    assert data["name"] == "Long Ride"
    assert data["elapsed_time_sec"] == 3600
    assert data["average_speed_kmh"] == 36.0 # 10 m/s * 3.6