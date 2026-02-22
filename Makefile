.PHONY: install auth run docker-up docker-down

# Install dependencies locally
install:
	uv sync --group frontend

# Run authentication script locally (opens browser)
auth:
	uv run strava-auth

# Run the Chainlit app locally
run:
	uv run chainlit run chainlit/chainlit_app.py -w

# Docker commands
docker-up:
	docker-compose up --build

docker-down:
	docker-compose down