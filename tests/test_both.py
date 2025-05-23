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
    
    try:
        resp1 = httpx.post(LM_URL, json={
            "model": LM_MODEL,
            "messages": [{"role": "user", "content": "Generate 50 words of lorem ipsum and count how many times the letter 'a' appears"}],
            "temperature": 0.1,
            "max_tokens": 500
        }, headers=headers, timeout=30)
        
        result1 = resp1.json()
        if 'error' in result1:
            print(f"\n❌ API Error in Test 1: {result1['error']}")
            return
        content1 = result1['choices'][0]['message']['content']
        print(f"\nASSISTANT:\n{content1}")
    except Exception as e:
        print(f"\n❌ Error in Test 1: {e}")
        print(f"Response status: {resp1.status_code}")
        print(f"Response text: {resp1.text[:500]}")
        return
    
    # Test 2: Tool usage with analysis
    print("\n\nTEST 2: Complete Tool Integration Flow")
    print("-" * 40)
    
    if "openai" in LM_URL:
        # Step 1: Initial request with tool
        user_msg = "I need you to generate 2 paragraphs of lorem ipsum text using the tool, then analyze the generated text and tell me: 1) How many words it contains, 2) Which letter appears most frequently, 3) The longest word in the text. Show me both the generated text AND your analysis."
        print(f"USER: {user_msg}")
        
        resp2 = httpx.post(LM_URL, json={
            "model": LM_MODEL,
            "messages": [
                {"role": "user", "content": user_msg}
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
            print(f"\nASSISTANT: I'll use the lorem ipsum generator to create 2 paragraphs and then analyze the text for you.")
            print(f"\n[TOOL CALL: {tool_call['function']['name']}({tool_call['function']['arguments']})]")
            
            # Step 3: Execute tool (simulating MCP server response)
            args = json.loads(tool_call['function']['arguments'])
            lorem_resp = requests.get(f"{BASE_URL}/lorem/{args.get('paragraph_count', 2)}")
            lorem_text = "\n\n".join(lorem_resp.json()['paragraphs'])
            
            print(f"\n[TOOL RESPONSE - Generated Lorem Ipsum:]")
            print("-" * 40)
            print(lorem_text)
            print("-" * 40)
            
            # Step 4: Send tool result back to LLM for final response
            print("\n[Continuing conversation with tool result...]")
            
            # Create a clean assistant message for the conversation history
            assistant_msg = {
                "role": "assistant",
                "content": message2.get('content'),  # Include content if any
                "tool_calls": [tool_call]  # Only include the specific tool call we're responding to
            }
            
            resp3 = httpx.post(LM_URL, json={
                "model": LM_MODEL,
                "messages": [
                    {"role": "user", "content": user_msg},
                    assistant_msg,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "content": lorem_text
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 800
            }, headers=headers, timeout=30)
            
            result3 = resp3.json()
            if 'error' in result3:
                print(f"\n❌ OpenAI API Error: {result3['error']}")
                return
            final_response = result3['choices'][0]['message']['content']
            
            print(f"\nASSISTANT (Final Response):\n{final_response}")
            
            # Verify the response includes both the text and analysis
            print("\n" + "-" * 40)
            print("VERIFICATION:")
            has_text = "lorem" in final_response.lower() or "text" in final_response.lower()
            has_word_count = "word" in final_response.lower()
            has_letter_analysis = "letter" in final_response.lower() or "character" in final_response.lower()
            has_longest = "longest" in final_response.lower()
            
            print(f"✓ References the generated text: {has_text}")
            print(f"✓ Includes word count: {has_word_count}")
            print(f"✓ Includes letter analysis: {has_letter_analysis}")
            print(f"✓ Identifies longest word: {has_longest}")
            
            if all([has_text, has_word_count, has_letter_analysis, has_longest]):
                print("\n✅ SUCCESS: LLM properly used tool output to complete the analysis!")
            else:
                print("\n⚠️  WARNING: LLM response may be missing some analysis elements")
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