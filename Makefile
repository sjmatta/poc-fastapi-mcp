.PHONY: help setup run test test-detail clean server test-server act-test act-list

help:
	@echo "Available commands:"
	@echo "  make setup        - Install dependencies with uv"
	@echo "  make run          - Run the FastAPI server"
	@echo "  make test         - Run all tests with pytest"
	@echo "  make test-quick   - Run tests without LM Studio"
	@echo "  make test-llm     - Run LLM conversation tests"
	@echo "  make test-server  - Run server and tests together"
	@echo "  make act-test     - Test GitHub Actions locally with act"
	@echo "  make act-list     - List available GitHub Actions workflows"
	@echo "  make clean        - Clean cache and temporary files"

setup:
	uv sync

run:
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest tests/ -v

test-quick:
	uv run pytest tests/ -v -k "not (llm or lm_studio)"

test-llm:
	uv run pytest tests/test_llm_conversation.py -v

test-server:
	@echo "Starting server and running tests..."
	@uv run uvicorn src.main:app --port 8000 > /dev/null 2>&1 & SERVER_PID=$$!; \
	sleep 3; \
	uv run pytest tests/ -v -s; \
	TEST_EXIT=$$?; \
	kill $$SERVER_PID 2>/dev/null || true; \
	exit $$TEST_EXIT

clean:
	rm -rf __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

act-list:
	act -l

act-test:
	@echo "Testing GitHub Actions locally with act..."
	@echo "Make sure to add your OpenAI API key to .env file"
	act push --secret-file .env