import sys
import os
import time
import uuid
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.globals import set_debug

def main():
    load_dotenv()

    # Check for valid token
    token = os.getenv("STRAVA_ACCESS_TOKEN")
    expires_at = os.getenv("STRAVA_EXPIRES_AT")
    
    if not token or (expires_at and time.time() > float(expires_at)):
        print("Strava token missing or expired. Starting authentication setup...")
        from strava_agent.authenticate import authenticate
        if not authenticate():
            print("Authentication failed. Please check your credentials.")
            sys.exit(1)

    # Import graph after ensuring env vars are set
    from strava_agent.graph import build_graph
    from strava_agent.llm import get_llm
    from strava_agent.tools import get_athlete_stats, get_activities_in_range, get_activity_information
    from strava_agent.prompts import get_system_prompt
    from strava_agent.logger import InteractionLogger

    set_debug(False)
    
    # Initialize LLM with configuration
    model = os.getenv("LLM_MODEL", "qwen3:8b")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0"))
    llm = get_llm(model=model, temperature=temperature)
    
    # Define tools to use
    tools = [get_athlete_stats, get_activities_in_range, get_activity_information]
    
    app = build_graph(llm, tools=tools)
    logger = InteractionLogger()
    
    system_message = SystemMessage(content=get_system_prompt())

    # Handle command line arguments for single-question mode
    if len(sys.argv) > 1:
        if sys.argv[1] == "--graph":
            print(app.get_graph().draw_mermaid())
            return

        question = " ".join(sys.argv[1:])
        print(f"User: {question}")
        
        messages = [system_message, HumanMessage(content=question)]
        try:
            final_state = app.invoke({"messages": messages})
            print("-" * 30)
            print(f"Agent: {final_state['messages'][-1].content}")
        except Exception as e:
            print(f"Error: {e}")
        return

    # Simple CLI loop
    print("Strava Agent CLI (Type 'quit' to exit)")
    print("-" * 30)
    
    session_id = str(uuid.uuid4())
    # Initialize history with system message
    messages = [system_message]
    
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit"]:
                break
                
            logger.log(session_id, "user", user_input)
            messages.append(HumanMessage(content=user_input))
            
            # Invoke the graph
            final_state = app.invoke({"messages": messages})
            
            # Update history
            messages = final_state["messages"]
            
            # Print the last message content (Agent response)
            response = messages[-1].content
            print(f"Agent: {response}")
            logger.log(session_id, "assistant", response)
            print("-" * 30)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            # If the graph failed, remove the last user message so we don't have a dangling question
            if messages and isinstance(messages[-1], HumanMessage):
                messages.pop()

if __name__ == "__main__":
    main()
