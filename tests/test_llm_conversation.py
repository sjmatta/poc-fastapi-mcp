import pytest
import httpx
import json
import logging

logger = logging.getLogger(__name__)

class TestLlmConversation:
    @pytest.fixture
    def lm_studio_client(self):
        return httpx.Client(base_url="http://localhost:1234")
    
    def test_conversation_flow(self, lm_studio_client):
        try:
            response = self._simple_generation(lm_studio_client)
            assert response.status_code == 200
            assert "lorem" in response.json()["choices"][0]["message"]["content"].lower()
            
            tool_response = self._tool_based_generation(lm_studio_client)
            if tool_response and tool_response.status_code == 200:
                self._verify_tool_usage(tool_response)
                
        except httpx.ConnectError:
            pytest.skip("LM Studio not running")
    
    def _simple_generation(self, client):
        return client.post(
            "/v1/chat/completions",
            json={
                "model": "gemma-3-27b-it-qat",
                "messages": [
                    {"role": "user", "content": "Generate exactly 50 words of lorem ipsum text"}
                ],
                "temperature": 0.1,
                "max_tokens": 200
            },
            timeout=30
        )
    
    def _tool_based_generation(self, client):
        return client.post(
            "/v1/chat/completions",
            json={
                "model": "gemma-3-27b-it-qat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You have access to a generate_lorem_ipsum tool. Use it when asked for lorem ipsum."
                    },
                    {"role": "user", "content": "Generate 2 paragraphs of lorem ipsum using your tools"}
                ],
                "temperature": 0.1
            },
            timeout=30
        )
    
    def _verify_tool_usage(self, response):
        result = response.json()
        message = result["choices"][0]["message"]
        
        if "tool_calls" in message:
            assert len(message["tool_calls"]) > 0
            tool_call = message["tool_calls"][0]
            assert tool_call["function"]["name"] == "generate_lorem_ipsum"
            args = json.loads(tool_call["function"]["arguments"])
            assert "paragraph_count" in args