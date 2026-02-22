# Strava Agent Playground 🏃🚴

A conversational AI agent that interacts with your Strava data using **LangGraph**, **LangChain**, and **Ollama**. It features a chat interface built with **Chainlit**.

## 🌟 Features

*   **Natural Language Queries**: Ask questions like "What was my longest run in April?" or "How many rides did I do last week?".
*   **Intelligent Agent**: Uses a graph-based agent (LangGraph) to plan and execute multi-step reasoning.
    *   *Search*: Finds activities within date ranges.
    *   *Analyze*: Aggregates statistics (counts, types).
    *   *Detail*: Fetches deep metrics (elevation, speed) for specific activities when needed.
*   **Local LLM Support**: Designed to work with local models via Ollama (e.g., Qwen, Llama 3).
*   **Interactive UI**: Clean chat interface provided by Chainlit.
*   **Dockerized**: Easy deployment with Docker Compose.

## 🛠️ Tech Stack

*   **Framework**: [LangGraph](https://langchain-ai.github.io/langgraph/) & [LangChain](https://www.langchain.com/)
*   **LLM Backend**: [Ollama](https://ollama.com/) (Local LLMs)
*   **Frontend**: [Chainlit](https://docs.chainlit.io/)
*   **API Integration**: [StravaLib](https://github.com/stravalib/stravalib)
*   **Package Manager**: [uv](https://github.com/astral-sh/uv)

## 📋 Prerequisites

1.  **Strava Account**: You need a Strava account and an API Application.
    *   Go to [Strava API Settings](https://www.strava.com/settings/api).
    *   Create an app to get your `Client ID` and `Client Secret`.
2.  **Ollama**: Install Ollama and pull a model.
    ```bash
    ollama pull qwen2.5:14b  # or your preferred model
    ```
3.  **Python 3.12+** (if running locally).
4.  **Docker** (optional, for containerized run).

## 🚀 Setup & Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd strava-playground
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env  # If you have an example, otherwise create one
```

Add your Strava credentials and LLM configuration:

```ini
# Strava API Credentials
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret

# LLM Configuration
LLM_MODEL=qwen2.5:14b
LLM_TEMPERATURE=0
```

### 3. Authenticate with Strava

Before the agent can access your data, you must authenticate to generate an access token.

**Using Make (Recommended):**
```bash
make auth
```

**Manually:**
```bash
uv run strava-auth
```

This will open a browser window. Authorize the app, and the script will automatically update your `.env` file with the `STRAVA_ACCESS_TOKEN` and `STRAVA_REFRESH_TOKEN`.

## 🏃 Running the App

### Option A: Using Docker (Recommended)

Ensure Ollama is running on your host machine.

```bash
make docker-up
```

Access the chat interface at `http://localhost:8000`.

To stop:
```bash
make docker-down
```

### Option B: Running Locally

1.  **Install Dependencies**:
    ```bash
    make install
    ```
2.  **Run Chainlit**:
    ```bash
    make run
    ```