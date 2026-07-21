import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None
_model_name = None

# Provider configs: base_url, api_key_env, default_model
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "default_model": "gemini-3.1-flash-lite",
    },
    "openai": {
        "base_url": None,  # default OpenAI endpoint
        "api_key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o",
    },
}

def _init_client():
    global _client, _model_name
    
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown LLM_PROVIDER: '{provider}'. Choose from: {list(PROVIDERS.keys())}")
    
    config = PROVIDERS[provider]
    api_key = os.getenv(config["api_key_env"])
    
    if not api_key:
        print(f"Warning: {config['api_key_env']} not found in environment variables.")
    
    _model_name = os.getenv("LLM_MODEL", config["default_model"])
    
    kwargs = {"api_key": api_key}
    if config["base_url"]:
        kwargs["base_url"] = config["base_url"]
    
    _client = AsyncOpenAI(**kwargs)
    
    print(f"[LLM] Provider: {provider} | Model: {_model_name}")

def get_openai_client() -> AsyncOpenAI:
    """Returns a configured AsyncOpenAI-compatible client."""
    global _client
    if _client is None:
        _init_client()
    return _client

def get_model_name() -> str:
    """Returns the configured model name."""
    global _model_name
    if _model_name is None:
        _init_client()
    return _model_name
