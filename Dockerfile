FROM python:3.12-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install dependencies
# Rely on the lockfile and install the frontend group (chainlit)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --group frontend

# Copy application code
COPY src/ src/
COPY chainlit/ chainlit/

# Add src to PYTHONPATH and .venv to PATH
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"

# Create a directory for persistent data
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["chainlit", "run", "chainlit/chainlit_app.py", "--host", "0.0.0.0", "--port", "8000"]