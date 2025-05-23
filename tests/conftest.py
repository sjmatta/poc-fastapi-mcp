import pytest
import httpx
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def base_url():
    return "http://localhost:8000"

@pytest.fixture
def llm_config():
    import os
    return {
        "url": os.getenv("LLM_API_URL", "http://localhost:1234/v1/chat/completions"),
        "model": os.getenv("LLM_MODEL", "gemma-3-27b-it-qat"),
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "headers": {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', '')}"} if os.getenv("OPENAI_API_KEY") else {}
    }

@pytest.fixture
def http_client():
    with httpx.Client() as client:
        yield client