.PHONY: help setup run test test-detail clean server test-server

help:
	@echo "Available commands:"
	@echo "  make setup        - Install dependencies with uv"
	@echo "  make run          - Run the FastAPI server"
	@echo "  make test         - Run all tests with pytest"
	@echo "  make test-quick   - Run tests without LM Studio"
	@echo "  make test-detail  - Run detailed Gemma conversation test"
	@echo "  make test-server  - Run server and tests together"
	@echo "  make clean        - Clean cache and temporary files"

setup:
	uv sync

run:
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest test_both.py -v

test-quick:
	uv run pytest test_both.py -v -k "not lm_studio"

test-detail:
	uv run python test_gemma_conversation.py

test-server:
	@echo "Starting server and running tests..."
	@uv run uvicorn main:app --port 8000 > /dev/null 2>&1 & SERVER_PID=$$!; \
	sleep 3; \
	uv run pytest test_both.py -v -s; \
	TEST_EXIT=$$?; \
	kill $$SERVER_PID 2>/dev/null || true; \
	exit $$TEST_EXIT

clean:
	rm -rf __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true