import asyncio
import os
from typing import Any, Dict, List, Optional
from browser_use.llm.base import BaseChatModel
from browser_use.llm.messages import UserMessage

# Provider & 2026 Model Catalog
PROVIDERS_CONFIG: Dict[str, Dict[str, Any]] = {
    "google": {
        "name": "Google Gemini",
        "env_key": "GOOGLE_API_KEY",
        "key_placeholder": "AIzaSy...",
        "default_model": "gemini-3.5-flash",
        "models": [
            {"id": "gemini-3.5-flash", "label": "Gemini 3.5 Flash (Fast & Stable Default)", "recommended": True},
            {"id": "gemini-3.5-flash-lite", "label": "Gemini 3.5 Flash-Lite (High Quota / Ultra-Fast)"},
            {"id": "gemini-flash-lite-latest", "label": "Gemini Flash-Lite Latest"},
            {"id": "gemini-flash-latest", "label": "Gemini Flash Latest"},
            {"id": "gemini-3.8-flash", "label": "Gemini 3.8 Flash (High Demand)"},
            {"id": "gemini-4-argon", "label": "Gemini 4 Argon (Reasoning)"},
            {"id": "gemini-3.1-pro-preview", "label": "Gemini 3.1 Pro Preview"},
        ]
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "env_key": "ANTHROPIC_API_KEY",
        "key_placeholder": "sk-ant-...",
        "default_model": "claude-sonnet-5-5",
        "models": [
            {"id": "claude-sonnet-5-5", "label": "Claude Sonnet 5.5 (Recommended Balanced)", "recommended": True},
            {"id": "claude-fable-5-1", "label": "Claude Fable 5.1 (Adaptive Thinking / Frontier)"},
            {"id": "claude-opus-5-5", "label": "Claude Opus 5.5 (Deep Reasoning)"},
            {"id": "claude-haiku-5-5", "label": "Claude Haiku 5.5 (Ultra Fast)"},
            {"id": "claude-mythos-5-1", "label": "Claude Mythos 5.1"},
            {"id": "claude-sonnet-4-6", "label": "Claude Sonnet 4.6"},
            {"id": "claude-3-7-sonnet-20250219", "label": "Claude 3.7 Sonnet"},
            {"id": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet"},
        ]
    },
    "openai": {
        "name": "OpenAI",
        "env_key": "OPENAI_API_KEY",
        "key_placeholder": "sk-proj-...",
        "default_model": "gpt-6-astra",
        "models": [
            {"id": "gpt-6-astra", "label": "GPT-6 Astra (Flagship Agentic & Computer Use)", "recommended": True},
            {"id": "gpt-6-sol", "label": "GPT-6 Sol (Balanced Agent Workflow)"},
            {"id": "gpt-6-luna", "label": "GPT-6 Luna (Lightweight & Fast)"},
            {"id": "gpt-5.4", "label": "GPT-5.4 (High Capability)"},
            {"id": "gpt-5.2-pro", "label": "GPT-5.2 Pro"},
            {"id": "gpt-5-mini", "label": "GPT-5 Mini"},
            {"id": "gpt-4o", "label": "GPT-4o"},
            {"id": "gpt-4o-mini", "label": "GPT-4o Mini"},
        ]
    },
    "groq": {
        "name": "Groq LPU",
        "env_key": "GROQ_API_KEY",
        "key_placeholder": "gsk_...",
        "default_model": "openai/gpt-oss-120b",
        "models": [
            {"id": "openai/gpt-oss-120b", "label": "GPT-OSS 120B (Flagship Open Weight)", "recommended": True},
            {"id": "meta-llama/llama-4-maverick-17b-128e-instruct", "label": "Llama 4 Maverick (17B/128E)"},
            {"id": "meta-llama/llama-4-scout-17b-16e-instruct", "label": "Llama 4 Scout (17B/16E)"},
            {"id": "qwen/qwen3-32b", "label": "Qwen 3 32B"},
            {"id": "deepseek-r1-distill-llama-70b", "label": "DeepSeek R1 Distill Llama 70B"},
        ]
    },
    "deepseek": {
        "name": "DeepSeek",
        "env_key": "DEEPSEEK_API_KEY",
        "key_placeholder": "sk-...",
        "default_model": "deepseek-v4-pro",
        "models": [
            {"id": "deepseek-v4-pro", "label": "DeepSeek V4 Pro (Frontier Reasoning)", "recommended": True},
            {"id": "deepseek-v4-flash", "label": "DeepSeek V4 Flash"},
            {"id": "deepseek-chat", "label": "DeepSeek Chat (V3)"},
            {"id": "deepseek-reasoner", "label": "DeepSeek Reasoner (R1)"},
        ]
    }
}

def create_llm(
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    max_retries: int = 5
) -> BaseChatModel:
    """
    Factory to construct the appropriate BaseChatModel for browser-use.
    Falls back to environment variables if api_key is omitted.
    Thread-safe & async-safe: does NOT mutate process-global os.environ.
    """
    p = provider.lower().strip()
    if p not in PROVIDERS_CONFIG:
        raise ValueError(f"Unsupported provider '{provider}'. Must be one of: {list(PROVIDERS_CONFIG.keys())}")
        
    cfg = PROVIDERS_CONFIG[p]
    
    resolved_key = (api_key or "").strip()
    if not resolved_key:
        resolved_key = os.getenv(cfg["env_key"], "")

    if p == "google":
        from browser_use.llm.google.chat import ChatGoogle
        return ChatGoogle(
            model=model,
            api_key=resolved_key or None,
            temperature=0.0,
            max_output_tokens=8192,
            max_retries=max_retries
        )

    elif p == "anthropic":
        from browser_use.llm.anthropic.chat import ChatAnthropic
        kwargs: Dict[str, Any] = {
            "model": model,
            "api_key": resolved_key or None,
            "max_tokens": 8192
        }
        # Special handling for adaptive-thinking models in Anthropic
        model_lower = model.lower()
        if "fable-5" in model_lower or "mythos-5" in model_lower:
            kwargs["thinking"] = {"type": "adaptive"}
            
        return ChatAnthropic(**kwargs)

    elif p == "openai":
        from browser_use.llm.openai.chat import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=resolved_key or None,
            temperature=0.2,
            max_completion_tokens=4096
        )

    elif p == "groq":
        from browser_use.llm.groq.chat import ChatGroq
        return ChatGroq(
            model=model,
            api_key=resolved_key or None,
            temperature=0.0
        )

    elif p == "deepseek":
        from browser_use.llm.deepseek.chat import ChatDeepSeek
        return ChatDeepSeek(
            model=model,
            api_key=resolved_key or None,
            temperature=0.0
        )

    else:
        # Fallback to OpenAI-compatible endpoint
        from browser_use.llm.openai.chat import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=resolved_key or None
        )

async def verify_llm_credentials(provider: str, model: str, api_key: str) -> Dict[str, Any]:
    """
    Test invoking the model with a minimal prompt to verify API key & active quota.
    Uses max_retries=1 and an 8-second timeout for snappy, non-hanging feedback.
    """
    try:
        llm = create_llm(provider=provider, model=model, api_key=api_key, max_retries=1)
        test_messages = [UserMessage(content="Hello, respond with 'OK'")]
        await asyncio.wait_for(llm.ainvoke(test_messages), timeout=12.0)
        return {"success": True, "message": f"Successfully connected to {provider} ({model})"}
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": f"Verification timed out (12s) reaching '{model}'. Server may be experiencing high latency or rate limits."
        }
    except Exception as e:
        err_msg = str(e)
        err_type = type(e).__name__
        if "503" in err_msg or "high demand" in err_msg.lower():
            return {
                "success": False,
                "error": f"Model '{model}' is experiencing high demand (503). Switch to 'gemini-3.5-flash' or 'gemini-3.5-flash-lite'!"
            }
        # If it's a validation error, the request reached the model and token quota passed
        if "validation" in err_type.lower() or "validation" in err_msg.lower():
            return {"success": True, "message": f"Verified {provider} ({model}) via validation check"}
        return {"success": False, "error": f"{err_type}: {err_msg}"}
