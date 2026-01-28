"""LLM abstraction layer supporting both local (Ollama) and online (OpenAI, etc.) models."""

import os
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def call_online_llm(
    prompt: str,
    provider: str = "openai",
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Call online LLM API (OpenAI, Anthropic, etc.).
    
    Args:
        prompt: Input prompt
        provider: API provider ('openai', 'anthropic', etc.)
        model: Model name (defaults based on provider)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        Generated text response
    """
    if provider.lower() == "openai":
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI library not installed. Install with: pip install openai"
            )
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Get your API key from: https://platform.openai.com/api-keys"
            )
        
        client = OpenAI(api_key=api_key)
        model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Fast and cost-effective
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates high-quality Python test code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens or 4000,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            # Check for specific error types
            if "insufficient_quota" in error_str or "429" in error_str:
                raise RuntimeError(
                    f"OpenAI quota exceeded. Error: {e}\n"
                    f"Solutions:\n"
                    f"  1. Add payment method: https://platform.openai.com/account/billing\n"
                    f"  2. Check usage: https://platform.openai.com/usage\n"
                    f"  3. Use local model instead: unset OPENAI_API_KEY\n"
                    f"  4. Wait for quota reset (usually monthly)"
                )
            elif "rate_limit" in error_str.lower():
                raise RuntimeError(
                    f"OpenAI rate limit exceeded. Error: {e}\n"
                    f"Wait a few minutes and try again, or use local model: unset OPENAI_API_KEY"
                )
            else:
                raise RuntimeError(f"OpenAI API error: {e}")
    
    else:
        raise ValueError(f"Unsupported online provider: {provider}. Supported: 'openai'")


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
    
    model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    api_url = api_url or os.getenv(
        "OLLAMA_API_URL", "http://localhost:11434/api/generate"
    )
    
    # Quick health check: verify Ollama is responding
    try:
        health_check = requests.get(api_url.replace("/api/generate", "/api/tags"), timeout=5)
        if health_check.status_code != 200:
            raise ConnectionError(
                f"Ollama API is not responding correctly. "
                f"Make sure Ollama is running: ollama serve"
            )
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Cannot connect to Ollama at {api_url}. "
            f"Make sure Ollama is running: ollama serve"
        )
    except Exception:
        pass  # If health check fails, continue anyway - might be a network issue
    
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
    
    # Increase timeout for larger models (codellama:7b can take longer)
    # Default: 300s (5 min), but allow up to 600s (10 min) for larger models
    timeout = 600 if "codellama" in model.lower() or "13b" in model.lower() or "34b" in model.lower() else 300
    
    try:
        response = requests.post(api_url, json=payload, timeout=timeout)
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
            f"LLM API request timed out after {timeout} seconds. "
            f"The model might be too slow, the prompt too large, or Ollama may not be using GPU. "
            f"Try: 1) Restart Ollama (pkill ollama && ollama serve), "
            f"2) Pre-warm model (ollama run {model} 'test'), "
            f"3) Check GPU usage in Activity Monitor, "
            f"4) Use a smaller model."
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


def call_llm(
    prompt: str,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    api_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Unified LLM interface supporting both local (Ollama) and online (OpenAI, etc.) models.
    
    Determines which provider to use based on:
    1. LLM_PROVIDER environment variable ('local' or 'openai')
    2. Presence of OPENAI_API_KEY (if set, uses OpenAI)
    3. Defaults to 'local' (Ollama)
    
    Args:
        prompt: Input prompt
        model: Model name (provider-specific)
        provider: Force specific provider ('local' or 'openai')
        api_url: API URL for local Ollama (ignored for online)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        Generated text response
    """
    # Determine provider
    if provider:
        use_provider = provider.lower()
    elif os.getenv("LLM_PROVIDER"):
        use_provider = os.getenv("LLM_PROVIDER").lower()
    elif os.getenv("OPENAI_API_KEY"):
        use_provider = "openai"
    else:
        use_provider = "local"
    
    if use_provider == "openai":
        try:
            return call_online_llm(
                prompt=prompt,
                provider="openai",
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except RuntimeError as e:
            # If quota/rate limit error, provide helpful fallback suggestion
            error_str = str(e)
            if "quota" in error_str.lower() or "rate_limit" in error_str.lower():
                print("\n" + "="*70)
                print("⚠️  OpenAI API Error - Switching to Local Model")
                print("="*70)
                print("OpenAI quota/rate limit exceeded. Falling back to local Ollama.")
                print("\nTo fix OpenAI issues:")
                print("  1. Add payment: https://platform.openai.com/account/billing")
                print("  2. Check usage: https://platform.openai.com/usage")
                print("\nTo force local model:")
                print("  unset OPENAI_API_KEY")
                print("  export LLM_PROVIDER=local")
                print("="*70 + "\n")
                
                # Auto-fallback to local if OPENAI fails
                if os.getenv("LLM_AUTO_FALLBACK", "true").lower() == "true":
                    fallback_model = model or os.getenv("OLLAMA_MODEL", "llama3.2:1b")
                    print(f"Auto-fallback enabled: Using local Ollama model '{fallback_model}' instead...")
                    return call_local_llm(
                        prompt=prompt,
                        model=fallback_model,
                        api_url=api_url,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
            raise
    else:
        return call_local_llm(
            prompt=prompt,
            model=model,
            api_url=api_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

