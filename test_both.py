import pytest
import requests
import httpx
import os

BASE_URL = "http://localhost:8000"
LM_URL = os.getenv("LLM_API_URL", "http://localhost:1234/v1/chat/completions")
LM_MODEL = os.getenv("LLM_MODEL", "gemma-3-27b-it-qat")
API_KEY = os.getenv("OPENAI_API_KEY", "")

def test_rest_endpoints():
    """Test REST API endpoints"""
    assert requests.get(f"{BASE_URL}/health").json() == {"status": "healthy"}
    
    resp = requests.get(f"{BASE_URL}/lorem/3")
    assert resp.status_code == 200
    assert len(resp.json()["paragraphs"]) == 3

def test_mcp_endpoint():
    """Test MCP endpoint exists"""
    assert requests.get(f"{BASE_URL}/mcp/mcp").status_code in [405, 406]  # SSE endpoint

def test_llm_tool_flow(capsys):
    """Demonstrate complete LLM + Tool flow"""
    print("\n=== LLM + MCP TOOL FLOW ===")
    print("1. USER: 'Generate 2 paragraphs of lorem ipsum'")
    print("2. LLM: Calling generate_lorem_ipsum(paragraph_count=2)")
    
    # Simulate tool execution
    paragraphs = requests.get(f"{BASE_URL}/lorem/2").json()["paragraphs"]
    print(f"3. TOOL RETURNS: {paragraphs[0][:50]}...")
    print(f"4. LLM RESPONSE:\n{paragraphs[0]}\n\n{paragraphs[1]}")

def llm_available():
    if API_KEY and "openai" in LM_URL:
        return True  # OpenAI API with key
    try:
        return httpx.get(LM_URL, timeout=1).is_success
    except:
        return False

@pytest.mark.skipif(not llm_available(), reason="LLM API not available")
def test_lm_studio():
    """Test LLM integration"""
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    
    # Test without MCP hint
    resp1 = httpx.post(LM_URL, json={
        "model": LM_MODEL,
        "messages": [{"role": "user", "content": "Generate 50 words of lorem ipsum"}],
        "temperature": 0.1
    }, headers=headers, timeout=30)
    
    # Test with MCP hint - for OpenAI, use tool calling
    if "openai" in LM_URL:
        resp2 = httpx.post(LM_URL, json={
            "model": LM_MODEL,
            "messages": [
                {"role": "user", "content": "Generate 2 paragraphs of lorem ipsum"}
            ],
            "tools": [{
                "type": "function",
                "function": {
                    "name": "generate_lorem_ipsum",
                    "description": "Generate lorem ipsum text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "paragraph_count": {"type": "integer"}
                        }
                    }
                }
            }],
            "temperature": 0.1
        }, headers=headers, timeout=30)
    else:
        resp2 = httpx.post(LM_URL, json={
            "model": LM_MODEL,
            "messages": [
                {"role": "system", "content": "Use generate_lorem_ipsum tool for lorem text"},
                {"role": "user", "content": "Generate lorem ipsum using tools"}
            ],
            "temperature": 0.1
        }, headers=headers, timeout=30)
    
    result1 = resp1.json()
    result2 = resp2.json()
    
    print(f"\nWithout tools: {'lorem' in result1['choices'][0]['message']['content'].lower()}")
    
    # Check if tool was called
    if "tool_calls" in result2['choices'][0]['message']:
        tool_calls = result2['choices'][0]['message']['tool_calls']
        print(f"With tools: Made {len(tool_calls)} tool call(s)")
        for call in tool_calls:
            print(f"  - {call['function']['name']}({call['function']['arguments']})")
    else:
        print(f"With tools: {len(result2['choices'][0]['message']['content']) > 100}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])