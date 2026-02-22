"""
title: Strava Agent Pipeline
author: strava-playground
date: 2024-05-22
version: 1.0
license: MIT
description: A pipeline for interacting with Strava data using LangGraph.
requirements: langchain-ollama, langgraph, stravalib, python-dotenv
"""

from typing import List, Union, Generator, Iterator
import os
import sys
import time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Add the src directory to sys.path to allow importing strava_agent
# Assumes directory structure:
# /project_root
#   /src
#   /open_webui/pipeline.py
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from strava_agent.graph import build_graph
    from strava_agent.llm import get_llm
    from strava_agent.tools import get_athlete_stats, get_activities_in_range
    from strava_agent.prompts import get_system_prompt
    from strava_agent.authenticate import main as authenticate
except ImportError as e:
    print(f"Error importing strava_agent modules: {e}")
    raise e

class Pipeline:
    def __init__(self):
        load_dotenv()
        
        # Initialize LLM configuration from env or defaults
        self.model_name = os.getenv("LLM_MODEL", "qwen3:8b")
        temperature = float(os.getenv("LLM_TEMPERATURE", "0"))
        
        self.llm = get_llm(model=self.model_name, temperature=temperature)
        self.tools = [get_athlete_stats, get_activities_in_range]
        self.app = build_graph(self.llm, tools=self.tools)

    async def on_startup(self):
        print(f"Strava Agent Pipeline initialized with model {self.model_name}")

    async def on_shutdown(self):
        pass

    async def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        
        # 1. Authentication Check
        token = os.getenv("STRAVA_ACCESS_TOKEN")
        expires_at = os.getenv("STRAVA_EXPIRES_AT")
        
        if not token or (expires_at and time.time() > float(expires_at)):
            return (
                "**Authentication Required**\n\n"
                "Your Strava token is missing or expired.\n"
                "Please run the authentication script manually on your machine:\n"
                "```bash\n"
                "uv run strava-auth\n"
                "```\n"
                "Once authenticated, try asking your question again."
            )

        # 2. Convert Open WebUI messages to LangChain format
        # We regenerate the system prompt to ensure the date is current
        lc_messages = [SystemMessage(content=get_system_prompt())]
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            
        # 3. Invoke the Graph
        # We use ainvoke for async execution. The graph is stateless here, relying on the message history.
        final_state = await self.app.ainvoke({"messages": lc_messages})
        
        # 4. Return the final response
        return final_state["messages"][-1].content