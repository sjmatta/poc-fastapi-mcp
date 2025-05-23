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
    
    print("\n" + "="*60)
    print("LLM CONVERSATION TEST RESULTS")
    print("="*60)
    
    print(f"\nTesting with: {LM_URL}")
    print(f"Model: {LM_MODEL}")
    print(f"API Key present: {'Yes' if API_KEY else 'No'}")
    
    print("\n1. WITHOUT TOOLS:")
    print("-" * 40)
    print("Request: Generate 50 words of lorem ipsum")
    content1 = result1['choices'][0]['message']['content']
    print(f"Response preview: {content1[:200]}...")
    print(f"Contains 'lorem': {'lorem' in content1.lower()}")
    
    print("\n2. WITH TOOLS:")
    print("-" * 40)
    print("Request: Generate 2 paragraphs of lorem ipsum")
    
    # Check if tool was called
    message2 = result2['choices'][0]['message']
    if "tool_calls" in message2 and message2['tool_calls']:
        tool_calls = message2['tool_calls']
        print(f"✓ LLM made {len(tool_calls)} tool call(s):")
        for call in tool_calls:
            print(f"\n  Tool: {call['function']['name']}")
            print(f"  Arguments: {call['function']['arguments']}")
            try:
                import json
                args = json.loads(call['function']['arguments'])
                print(f"  Parsed: paragraph_count = {args.get('paragraph_count', 'N/A')}")
            except:
                pass
    else:
        content2 = message2.get('content', '')
        print(f"✗ No tool calls made")
        print(f"Response preview: {content2[:200] if content2 else 'No content'}...")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])