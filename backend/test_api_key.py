import os
from langchain_openai import ChatOpenAI
from openai import AuthenticationError, APIConnectionError
from dotenv import load_dotenv
import requests

load_dotenv()

def get_glm():
    print(f"testing GLM_API_KEY: {os.getenv('GLM_API_KEY')}")
    print(f"testing GLM_BASE_URL: {os.getenv('GLM_BASE_URL')}")
    print(f"testing GLM_MODEL: {os.getenv('GLM_MODEL')}")
    return ChatOpenAI(
        model=os.getenv("GLM_MODEL", "ilmu-glm-5.1"),
        api_key=os.getenv("GLM_API_KEY"),
        base_url=os.getenv("GLM_BASE_URL", "https://api.ilmu.ai/v1"),
        temperature=0.3,
    )

def test_glm_connection():
    """Tests if the GLM API key is activated and the service is reachable."""
    
    headers = {"Authorization": f"Bearer {os.getenv('GLM_API_KEY')}"}
    response = requests.get("https://api.ilmu.ai/v1/models", headers=headers)

    if response.status_code == 200:
        models = response.json().get('data', [])
        print("Available Models on ilmu.ai:")
        for m in models:
            print(f"- {m['id']}")
    else:
        print(f"Failed to fetch models: {response.status_code} - {response.text}")
    
    llm = get_glm()
    
    try:
        # A simple, low-token request to verify the key
        response = llm.invoke("Hi")
        print(" API Key is active!")
        print(f"Response: {response.content}")
        return True
    except AuthenticationError:
        print("❌ Invalid API Key: Please check your GLM_API_KEY environment variable.")
    except APIConnectionError:
        print("❌ Connection Error: Could not reach the Zhipu AI servers.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    
    return False

# Execution
if __name__ == "__main__":
    test_glm_connection()