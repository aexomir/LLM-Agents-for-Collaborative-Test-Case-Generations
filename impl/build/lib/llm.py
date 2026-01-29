"""LLM abstraction layer for local LLM calls."""

import os
from typing import Optional

try:
    import requests
except ImportError:
    requests = None


def call_local_llm(
    prompt: str,
    model: Optional[str] = None,
    api_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> str:
    if requests is None:
        raise ImportError(
            "requests library is required. Install it with: pip install requests"
        )
    
    model = model or os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b-instruct")
    api_url = api_url or os.getenv(
        "OLLAMA_API_URL", "http://localhost:11434/api/generate"
    )
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }
    
    if max_tokens is not None:
        payload["options"]["num_predict"] = max_tokens
    
    try:
        response = requests.post(api_url, json=payload, timeout=300)
        response.raise_for_status()
        
        result = response.json()
        
        if "response" in result:
            return result["response"]
        elif "text" in result:
            return result["text"]
        else:
            raise ValueError(
                f"Unexpected API response format: {list(result.keys())}"
            )
            
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(
            f"Unable to connect to LLM API at {api_url}. "
            f"Make sure Ollama (or your LLM server) is running. Error: {e}"
        )
    except requests.exceptions.Timeout:
        raise TimeoutError(
            f"LLM API request timed out after 300 seconds. "
            f"The model might be too slow or the prompt too large."
        )
    except requests.exceptions.HTTPError as e:
        # Try to get available models for better error message
        available_models = []
        try:
            base_url = api_url.replace("/api/generate", "")
            models_response = requests.get(f"{base_url}/api/tags", timeout=5)
            if models_response.status_code == 200:
                models_data = models_response.json()
                available_models = [m.get("name", "") for m in models_data.get("models", [])]
        except Exception:
            pass  # Ignore errors when fetching available models
        
        error_msg = (
            f"LLM API returned an error: {e}. "
            f"Check that the model '{model}' is available."
        )
        if available_models:
            error_msg += f"\nAvailable models: {', '.join(available_models)}"
            error_msg += f"\nSet OLLAMA_MODEL environment variable or pull the model: ollama pull {model}"
        
        raise ValueError(error_msg)

