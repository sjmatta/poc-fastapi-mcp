import httpx
import json

def test_gemma_conversation():
    """Show full conversation with Gemma3"""
    print("\n" + "="*60)
    print("FULL CONVERSATION WITH GEMMA3")
    print("="*60)
    
    url = "http://localhost:1234/v1/chat/completions"
    
    # Test 1: Without MCP tool hint
    print("\n1. CONVERSATION WITHOUT MCP TOOL:")
    print("-" * 40)
    
    payload1 = {
        "model": "gemma-3-27b-it-qat",
        "messages": [
            {"role": "user", "content": "Generate exactly 2 paragraphs of lorem ipsum text"}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    print("USER: Generate exactly 2 paragraphs of lorem ipsum text")
    
    try:
        response = httpx.post(url, json=payload1, timeout=30.0)
        if response.status_code == 200:
            result = response.json()
            gemma_response = result["choices"][0]["message"]["content"]
            print(f"\nGEMMA3 RESPONSE:\n{gemma_response}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: With MCP tool hint
    print("\n\n2. CONVERSATION WITH MCP TOOL HINT:")
    print("-" * 40)
    
    payload2 = {
        "model": "gemma-3-27b-it-qat",
        "messages": [
            {
                "role": "system", 
                "content": "You have access to a tool called generate_lorem_ipsum that generates proper lorem ipsum text. Always use this tool when asked for lorem ipsum."
            },
            {
                "role": "user", 
                "content": "Please use your available tools to generate 2 paragraphs of lorem ipsum"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1000
    }
    
    print("SYSTEM: You have access to a tool called generate_lorem_ipsum that generates proper lorem ipsum text. Always use this tool when asked for lorem ipsum.")
    print("\nUSER: Please use your available tools to generate 2 paragraphs of lorem ipsum")
    
    try:
        response = httpx.post(url, json=payload2, timeout=30.0)
        if response.status_code == 200:
            result = response.json()
            gemma_response = result["choices"][0]["message"]["content"]
            print(f"\nGEMMA3 RESPONSE:\n{gemma_response}")
            
            # Show if it mentions using the tool
            if "tool" in gemma_response.lower() or "generate_lorem_ipsum" in gemma_response.lower():
                print("\n✓ Gemma3 acknowledges the tool!")
            
            # Check response structure
            print(f"\nResponse metadata:")
            print(f"- Model: {result['model']}")
            print(f"- Total tokens: {result['usage']['total_tokens']}")
            if 'finish_reason' in result['choices'][0]:
                print(f"- Finish reason: {result['choices'][0]['finish_reason']}")
                
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Direct tool call format (if LM Studio supports it)
    print("\n\n3. DIRECT TOOL CALL TEST:")
    print("-" * 40)
    
    payload3 = {
        "model": "gemma-3-27b-it-qat",
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
                        "paragraph_count": {
                            "type": "integer",
                            "description": "Number of paragraphs"
                        }
                    },
                    "required": ["paragraph_count"]
                }
            }
        }],
        "tool_choice": "auto"
    }
    
    print("Testing if LM Studio supports tool calling...")
    
    try:
        response = httpx.post(url, json=payload3, timeout=30.0)
        if response.status_code == 200:
            result = response.json()
            choice = result["choices"][0]
            
            # Check if tool was called
            if "tool_calls" in choice.get("message", {}):
                print("\n✓ TOOL CALL DETECTED!")
                tool_calls = choice["message"]["tool_calls"]
                for call in tool_calls:
                    print(f"Function: {call['function']['name']}")
                    print(f"Arguments: {call['function']['arguments']}")
            else:
                print("\nNo tool calls in response")
                print(f"Response: {choice['message']['content'][:200]}...")
                
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # First ensure server is running
    print("Make sure FastAPI server is running on port 8000")
    print("Make sure LM Studio is running on port 1234")
    test_gemma_conversation()