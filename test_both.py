import pytest
import requests
import httpx

BASE_URL = "http://localhost:8000"
LM_URL = "http://localhost:1234/v1/chat/completions"

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

def lm_studio_available():
    try:
        return httpx.get(LM_URL, timeout=1).is_success
    except:
        return False

@pytest.mark.skipif(not lm_studio_available(), reason="LM Studio not running")
def test_lm_studio():
    """Test LM Studio integration"""
    # Test without MCP hint
    resp1 = httpx.post(LM_URL, json={
        "model": "gemma-3-27b-it-qat",
        "messages": [{"role": "user", "content": "Generate 50 words of lorem ipsum"}],
        "temperature": 0.1
    }, timeout=30)
    
    # Test with MCP hint
    resp2 = httpx.post(LM_URL, json={
        "model": "gemma-3-27b-it-qat",
        "messages": [
            {"role": "system", "content": "Use generate_lorem_ipsum tool for lorem text"},
            {"role": "user", "content": "Generate lorem ipsum using tools"}
        ],
        "temperature": 0.1
    }, timeout=30)
    
    print(f"\nWithout MCP: {'lorem' in resp1.json()['choices'][0]['message']['content'].lower()}")
    print(f"With MCP hint: {len(resp2.json()['choices'][0]['message']['content']) > 500}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])