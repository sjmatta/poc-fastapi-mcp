import pytest
import requests
import httpx
import os
import json

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
    """Test LLM integration with interesting lorem ipsum tasks"""
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    
    print("\n" + "="*60)
    print("LLM CONVERSATION TEST")
    print("="*60)
    print(f"API: {LM_URL}")
    print(f"Model: {LM_MODEL}")
    print(f"API Key: {'Present' if API_KEY else 'Not set'}")
    
    # Test 1: Simple generation and analysis
    print("\n\nTEST 1: Generate and Count Letters")
    print("-" * 40)
    print("USER: Generate 50 words of lorem ipsum and count how many times the letter 'a' appears")
    
    resp1 = httpx.post(LM_URL, json={
        "model": LM_MODEL,
        "messages": [{"role": "user", "content": "Generate 50 words of lorem ipsum and count how many times the letter 'a' appears"}],
        "temperature": 0.1,
        "max_tokens": 500
    }, headers=headers, timeout=30)
    
    result1 = resp1.json()
    content1 = result1['choices'][0]['message']['content']
    print(f"\nASSISTANT:\n{content1}")
    
    # Test 2: Tool usage with analysis
    print("\n\nTEST 2: Tool Usage + Analysis")
    print("-" * 40)
    
    if "openai" in LM_URL:
        # Step 1: Initial request with tool
        print("USER: Use the lorem ipsum generator to create 2 paragraphs, then tell me a fun fact about the generated text")
        
        resp2 = httpx.post(LM_URL, json={
            "model": LM_MODEL,
            "messages": [
                {"role": "user", "content": "Use the lorem ipsum generator to create 2 paragraphs, then tell me a fun fact about the generated text (like word count, most common letter, longest word, etc.)"}
            ],
            "tools": [{
                "type": "function",
                "function": {
                    "name": "generate_lorem_ipsum",
                    "description": "Generate lorem ipsum placeholder text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "paragraph_count": {"type": "integer", "description": "Number of paragraphs to generate"}
                        },
                        "required": ["paragraph_count"]
                    }
                }
            }],
            "temperature": 0.1
        }, headers=headers, timeout=30)
        
        result2 = resp2.json()
        message2 = result2['choices'][0]['message']
        
        if "tool_calls" in message2 and message2['tool_calls']:
            # Step 2: Show tool call
            tool_call = message2['tool_calls'][0]
            print(f"\nASSISTANT: I'll generate 2 paragraphs of lorem ipsum for you.")
            print(f"[Calling tool: {tool_call['function']['name']}({tool_call['function']['arguments']})]")
            
            # Step 3: Execute tool
            args = json.loads(tool_call['function']['arguments'])
            lorem_resp = requests.get(f"{BASE_URL}/lorem/{args.get('paragraph_count', 2)}")
            lorem_text = "\n\n".join(lorem_resp.json()['paragraphs'])
            
            print(f"\nTOOL RESPONSE:\n{lorem_text}")
            
            # Step 4: Continue conversation with analysis
            print("\n[Sending tool result back to LLM for analysis...]")
            
            resp3 = httpx.post(LM_URL, json={
                "model": LM_MODEL,
                "messages": [
                    {"role": "user", "content": "Use the lorem ipsum generator to create 2 paragraphs, then tell me a fun fact about the generated text (like word count, most common letter, longest word, etc.)"},
                    message2,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "content": lorem_text
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }, headers=headers, timeout=30)
            
            result3 = resp3.json()
            final_response = result3['choices'][0]['message']['content']
            print(f"\nASSISTANT:\n{final_response}")
        else:
            print("\nASSISTANT: [No tool call made - this is unexpected!]")
            print(message2.get('content', 'No response'))
    else:
        # Fallback for non-OpenAI
        print("USER: Generate 2 paragraphs of lorem ipsum and analyze them")
        resp2 = httpx.post(LM_URL, json={
            "model": LM_MODEL,
            "messages": [
                {"role": "system", "content": "You have access to generate_lorem_ipsum tool"},
                {"role": "user", "content": "Generate 2 paragraphs of lorem ipsum and tell me something interesting about them"}
            ],
            "temperature": 0.1
        }, headers=headers, timeout=30)
        
        result2 = resp2.json()
        print(f"\nASSISTANT:\n{result2['choices'][0]['message']['content']}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])