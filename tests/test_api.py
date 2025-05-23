import pytest
import json
import httpx

class TestRestEndpoints:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_lorem_generation(self, client):
        count = 3
        response = client.get(f"/lorem/{count}")
        assert response.status_code == 200
        data = response.json()
        assert "paragraphs" in data
        assert len(data["paragraphs"]) == count
        assert all(isinstance(p, str) and len(p) > 0 for p in data["paragraphs"])

class TestMcpEndpoint:
    def test_mcp_endpoint_exists(self, http_client, base_url):
        try:
            response = http_client.get(f"{base_url}/mcp/mcp")
            assert response.status_code in [307, 405, 406]
        except httpx.ConnectError:
            pytest.skip("Server not running")

class TestLlmIntegration:
    @pytest.fixture
    def is_llm_available(self, llm_config):
        if llm_config["api_key"] and "openai" in llm_config["url"]:
            return True
        try:
            response = httpx.get(llm_config["url"], timeout=1)
            return response.is_success
        except:
            return False
    
    def test_lorem_generation_and_analysis(self, llm_config, http_client, is_llm_available):
        if not is_llm_available:
            pytest.skip("LLM API not available")
        
        response = self._call_llm(
            http_client,
            llm_config,
            "Generate 50 words of lorem ipsum and count how many times the letter 'a' appears"
        )
        
        assert response.status_code == 200
        content = response.json()['choices'][0]['message']['content']
        assert 'lorem' in content.lower()
        assert any(char.isdigit() for char in content)
    
    def test_tool_integration_flow(self, llm_config, http_client, client, is_llm_available):
        if not is_llm_available:
            pytest.skip("LLM API not available")
        
        if "openai" not in llm_config["url"]:
            pytest.skip("Tool integration test requires OpenAI API")
        
        tool_response = self._test_tool_call_flow(http_client, llm_config, client)
        
        assert tool_response is not None
        assert "word" in tool_response.lower()
        assert "letter" in tool_response.lower()
        assert "longest" in tool_response.lower()
    
    def _call_llm(self, http_client, llm_config, message):
        return http_client.post(
            llm_config["url"],
            json={
                "model": llm_config["model"],
                "messages": [{"role": "user", "content": message}],
                "temperature": 0.1,
                "max_tokens": 500
            },
            headers=llm_config["headers"],
            timeout=30
        )
    
    def _test_tool_call_flow(self, http_client, llm_config, app_client):
        user_msg = ("Generate 2 paragraphs of lorem ipsum text using the tool, "
                   "then analyze: 1) word count, 2) most frequent letter, "
                   "3) longest word. Show both text and analysis.")
        
        initial_response = http_client.post(
            llm_config["url"],
            json={
                "model": llm_config["model"],
                "messages": [{"role": "user", "content": user_msg}],
                "tools": [self._get_tool_definition()],
                "temperature": 0.1
            },
            headers=llm_config["headers"],
            timeout=30
        )
        
        result = initial_response.json()
        message = result['choices'][0]['message']
        
        if "tool_calls" not in message or not message['tool_calls']:
            return None
        
        tool_call = message['tool_calls'][0]
        args = json.loads(tool_call['function']['arguments'])
        
        lorem_response = app_client.get(f"/lorem/{args.get('paragraph_count', 2)}")
        lorem_text = "\n\n".join(lorem_response.json()['paragraphs'])
        
        final_response = http_client.post(
            llm_config["url"],
            json={
                "model": llm_config["model"],
                "messages": [
                    {"role": "user", "content": user_msg},
                    {
                        "role": "assistant",
                        "content": message.get('content'),
                        "tool_calls": [tool_call]
                    },
                    {
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "content": lorem_text
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 800
            },
            headers=llm_config["headers"],
            timeout=30
        )
        
        if final_response.status_code == 200:
            return final_response.json()['choices'][0]['message']['content']
        return None
    
    def _get_tool_definition(self):
        return {
            "type": "function",
            "function": {
                "name": "generate_lorem_ipsum",
                "description": "Generate lorem ipsum placeholder text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "paragraph_count": {
                            "type": "integer",
                            "description": "Number of paragraphs to generate"
                        }
                    },
                    "required": ["paragraph_count"]
                }
            }
        }