import os
import json
import asyncio
from datetime import datetime
from langchain_core.tools import tool
from stravalib.client import Client

# Limit concurrent API calls to prevent hitting rate limits
_RATE_LIMITER = asyncio.Semaphore(5)

@tool
def get_athlete_stats():
    """
    Fetch the authenticated athlete's lifetime statistics.
    
    Useful for answering questions about all-time totals (like total run distance) or personal records (like biggest ride).
    Do NOT use this tool for questions about specific activities or time-bound queries like 'this year' or 'last week'.
    """
    try:
        client = Client(access_token=os.getenv("STRAVA_ACCESS_TOKEN"))
        stats = client.get_athlete_stats(client.get_athlete().id)
        # Return a formatted string so the LLM doesn't have to do unit conversion (m -> km)
        return f"Biggest Ride: {stats.biggest_ride_distance / 1000}km. All-time Run Distance: {stats.all_run_totals.distance / 1000}km."
    except Exception as e:
        return f"Error: {e}"

@tool
def get_activities_in_range(start_date: str, end_date: str):
    """
    Fetch activities between a start and end date. Returns a summary JSONL string.
    
    The summary includes id, name, type, distance, and date.
    For detailed metrics like speed, elevation, or time, use get_activity_information with the ID.
    
    Args:
        start_date: The start date in 'YYYY-MM-DD' format.
        end_date: The end date in 'YYYY-MM-DD' format.
    """
    try:
        client = Client(access_token=os.getenv("STRAVA_ACCESS_TOKEN"))
        after = datetime.strptime(start_date, "%Y-%m-%d")
        before = datetime.strptime(end_date, "%Y-%m-%d")
        
        activities = client.get_activities(after=after, before=before)
        
        results = []
        for activity in activities:
            # Extract relevant fields and convert to primitives for JSON
            data = {
                "id": activity.id,
                "name": activity.name,
                "type": str(activity.type),
                "distance_km": float(activity.distance) / 1000 if activity.distance else 0.0,
                "start_date": activity.start_date_local.isoformat()
            }
            results.append(json.dumps(data))
            
        return "\n".join(results) if results else "No activities found in this range."
    except Exception as e:
        return f"Error: {e}"

@tool
async def get_activity_information(activity_id: int):
    """
    Fetch detailed information about a specific activity by its ID.
    Returns full details including average speed, elapsed time, and elevation.
    Can be called in parallel for multiple activities.
    
    Args:
        activity_id: The ID of the activity to fetch.
    """
    async with _RATE_LIMITER:
        try:
            def _fetch_activity():
                client = Client(access_token=os.getenv("STRAVA_ACCESS_TOKEN"))
                activity = client.get_activity(activity_id)
                return {
                    "id": activity.id,
                    "name": activity.name,
                    "type": str(activity.type),
                    "distance_km": float(activity.distance) / 1000 if activity.distance else 0.0,
                    "start_date": activity.start_date_local.isoformat(),
                    "elapsed_time_sec": activity.elapsed_time if activity.elapsed_time else 0,
                    "average_speed_kmh": (float(activity.average_speed) * 3.6) if activity.average_speed else 0.0
                }

            data = await asyncio.to_thread(_fetch_activity)
            return json.dumps(data)
        except Exception as e:
            return f"Error: {e}"