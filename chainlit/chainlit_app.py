import os
import time

from dotenv import load_dotenv
import chainlit as cl
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from strava_agent.graph import build_graph
from strava_agent.llm import get_llm
from strava_agent.tools import get_athlete_stats, get_activities_in_range, get_activity_information
from strava_agent.prompts import get_system_prompt
from strava_agent.logger import InteractionLogger
from strava_agent.authenticate import authenticate
from duckdb_layer import DuckDBDataLayer

# Load environment variables
load_dotenv()

# --- App Setup ---
model = os.getenv("LLM_MODEL", "qwen3:8b")
temperature = float(os.getenv("LLM_TEMPERATURE", "0"))
llm = get_llm(model=model, temperature=temperature)

tools = [get_athlete_stats, get_activities_in_range, get_activity_information]
app = build_graph(llm, tools=tools)
logger = InteractionLogger()

# Initialize Chainlit Data Layer for History
cl.data_layer = DuckDBDataLayer(os.getenv("DUCKDB_PATH", "interactions.duckdb"))

# --- Chainlit Handlers ---

@cl.on_chat_start
async def on_chat_start():
    # Reload env vars in case they changed (e.g. re-auth)
    load_dotenv(override=True)
    
    # Check for valid token
    token = os.getenv("STRAVA_ACCESS_TOKEN")
    expires_at = os.getenv("STRAVA_EXPIRES_AT")
    
    if not token or (expires_at and time.time() > float(expires_at)):
        await cl.Message(
            content="Strava token is missing or expired. Please login.", 
            actions=[cl.Action(name="auth_strava", payload={"value": "login"}, label="Login with Strava")]
        ).send()
        return

    await start_chat_session()

async def start_chat_session():
    system_message = SystemMessage(content=get_system_prompt())
    cl.user_session.set("history", [system_message])
    await cl.Message(content="Hello! I'm your Strava assistant. Ask me about your activities!").send()

@cl.action_callback("auth_strava")
async def on_auth_action(action):
    await cl.Message(content="Opening browser for authentication... Please check the new tab.").send()
    res = await cl.make_async(authenticate)()
    if res:
        await cl.Message(content="Authentication successful!").send()
        await action.remove()
        await start_chat_session()
    else:
        await cl.Message(content="Authentication failed.").send()

@cl.on_message
async def on_message(message: cl.Message):
    session_id = cl.user_session.get("id")
    
    # Log user message
    await cl.make_async(logger.log)(session_id, "user", message.content)

    history = cl.user_session.get("history")
    history.append(HumanMessage(content=message.content))
    
    # Show a loading indicator
    msg = cl.Message(content="")
    await msg.send()
    
    # Stream the graph to show node transitions
    # stream_mode="updates" yields the output of each node as it finishes
    async for output in app.astream({"messages": history}, stream_mode="updates"):
        for node_name, state_update in output.items():
            
            # Append new messages to history
            new_messages = state_update["messages"]
            
            # If it's the agent node, it contains the AI response
            if node_name == "agent":
                for m in new_messages:
                    if isinstance(m, AIMessage) and m.content:
                        msg.content = m.content
                        await msg.update()
            
            # If it's the post_process node, it contains the system analysis
            elif node_name == "post_process":
                for m in new_messages:
                    if isinstance(m, SystemMessage):
                        async with cl.Step(name="System Analysis", type="llm") as step:
                            step.output = m.content

            # Add to session history so follow-ups work
            history.extend(new_messages)
            cl.user_session.set("history", history)

    # Log assistant response
    if msg.content:
        await cl.make_async(logger.log)(session_id, "assistant", msg.content)