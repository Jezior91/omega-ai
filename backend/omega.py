"""
OMEGA-AI :: Stateless Free-Tier AI Backend
============================================
Obsluguje darmowych dostawcow AI: Groq, Google Gemini, OpenRouter, Ollama (local), DeepSeek.

Stateless - brak zapisu do plikow / SQLite. Api_key przekazywany w ARGS.

CLI:
    uv run --with httpx python3 omega.py <command> '<json>'
    lub: echo '<json>' | uv run --with httpx python3 omega.py <command>

Komendy:
    chat   - {provider, model, messages, api_key, system_prompt?}
             -> {response, tokens_used, provider, model, latency_ms}
    models - {provider, api_key?}
             -> {models: [{id, name, free}]}
    test   - {provider, api_key}
             -> {ok, error?}
"""
import sys
import json
import time

# ----------------------------------------------------------------------------
# Provider registry
# ----------------------------------------------------------------------------

PROVIDERS = {
    "groq": {
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "style": "openai",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
    },
    "gemini": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        "style": "gemini",
        "models": [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash",
        ],
    },
    "openrouter": {
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "style": "openai",
        "models": [
            "meta-llama/llama-3.2-3b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
            "google/gemma-2-9b-it:free",
        ],
    },
    "ollama": {
        "endpoint": "http://localhost:11434/api/chat",
        "style": "ollama",
        "models": [
            "llama3.2",
            "mistral",
            "gemma2",
            "phi3",
        ],
    },
    "deepseek": {
        "endpoint": "https://api.deepseek.com/chat/completions",
        "style": "openai",
        "models": [
            "deepseek-chat",
        ],
    },
}


def out(data):
    print(json.dumps(data, ensure_ascii=False))


def err(msg):
    print(json.dumps({"error": str(msg)}, ensure_ascii=False))


# ----------------------------------------------------------------------------
# Message conversion helpers
# ----------------------------------------------------------------------------

def to_gemini_contents(messages, system_prompt=None):
    """Convert OpenAI-style messages list into Gemini contents + systemInstruction."""
    contents = []
    sys_parts = []
    if system_prompt:
        sys_parts.append(system_prompt)

    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "system":
            sys_parts.append(content)
            continue
        gem_role = "model" if role in ("assistant", "model") else "user"
        contents.append({"role": gem_role, "parts": [{"text": content}]})

    payload = {"contents": contents}
    if sys_parts:
        payload["systemInstruction"] = {"parts": [{"text": "\n".join(sys_parts)}]}
    return payload


def prep_openai_messages(messages, system_prompt=None):
    """Ensure system_prompt (if provided) is injected as a leading system message,
    without duplicating an existing system message."""
    msgs = list(messages)
    has_system = any(m.get("role") == "system" for m in msgs)
    if system_prompt and not has_system:
        msgs = [{"role": "system", "content": system_prompt}] + msgs
    return msgs


# ----------------------------------------------------------------------------
# Chat call implementations
# ----------------------------------------------------------------------------

def call_openai_compatible(httpx, endpoint, model, api_key, messages, system_prompt=None, extra_headers=None):
    msgs = prep_openai_messages(messages, system_prompt)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    payload = {"model": model, "messages": msgs}
    r = httpx.post(endpoint, timeout=90, headers=headers, json=payload)
    r.raise_for_status()
    d = r.json()
    choice = d["choices"][0]
    content = choice.get("message", {}).get("content", "")
    usage = d.get("usage", {}) or {}
    tokens_used = usage.get("total_tokens")
    if tokens_used is None:
        tokens_used = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
    return content, tokens_used


def call_gemini(httpx, model, api_key, messages, system_prompt=None):
    endpoint = PROVIDERS["gemini"]["endpoint"].format(model=model, api_key=api_key)
    payload = to_gemini_contents(messages, system_prompt)
    r = httpx.post(endpoint, timeout=90, headers={"Content-Type": "application/json"}, json=payload)
    r.raise_for_status()
    d = r.json()
    candidates = d.get("candidates", [])
    if not candidates:
        raise ValueError(f"No candidates returned by Gemini: {d}")
    parts = candidates[0].get("content", {}).get("parts", [])
    content = "".join(p.get("text", "") for p in parts)
    usage_meta = d.get("usageMetadata", {}) or {}
    tokens_used = usage_meta.get("totalTokenCount", 0)
    return content, tokens_used


def call_ollama(httpx, model, messages, system_prompt=None):
    msgs = prep_openai_messages(messages, system_prompt)
    payload = {"model": model, "messages": msgs, "stream": False}
    r = httpx.post(PROVIDERS["ollama"]["endpoint"], timeout=120, json=payload)
    r.raise_for_status()
    d = r.json()
    content = d.get("message", {}).get("content", "")
    # Ollama does not return token usage in a standard way across models;
    # eval_count (output) + prompt_eval_count (input) approximate total tokens.
    tokens_used = d.get("prompt_eval_count", 0) + d.get("eval_count", 0)
    return content, tokens_used


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------

def cmd_chat(payload):
    import httpx

    provider = payload.get("provider")
    model = payload.get("model")
    messages = payload.get("messages")
    api_key = payload.get("api_key")
    system_prompt = payload.get("system_prompt")

    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}"}
    if not model:
        return {"error": "Missing 'model'"}
    if not messages:
        return {"error": "Missing 'messages'"}
    if provider != "ollama" and not api_key:
        return {"error": f"Missing 'api_key' for provider '{provider}'"}

    cfg = PROVIDERS[provider]
    start = time.time()
    try:
        if provider == "gemini":
            content, tokens_used = call_gemini(httpx, model, api_key, messages, system_prompt)
        elif provider == "ollama":
            content, tokens_used = call_ollama(httpx, model, messages, system_prompt)
        elif provider == "openrouter":
            content, tokens_used = call_openai_compatible(
                httpx, cfg["endpoint"], model, api_key, messages, system_prompt,
                extra_headers={
                    "HTTP-Referer": "https://omega-ai.local",
                    "X-Title": "OMEGA-AI",
                },
            )
        elif cfg["style"] == "openai":
            content, tokens_used = call_openai_compatible(
                httpx, cfg["endpoint"], model, api_key, messages, system_prompt
            )
        else:
            return {"error": f"Unhandled provider style for: {provider}"}
    except httpx.HTTPStatusError as e:
        latency_ms = round((time.time() - start) * 1000, 2)
        body = ""
        try:
            body = e.response.text[:500]
        except Exception:
            pass
        return {
            "error": f"HTTP {e.response.status_code} from {provider}: {body}",
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
        }
    except Exception as e:
        latency_ms = round((time.time() - start) * 1000, 2)
        return {
            "error": f"{type(e).__name__}: {e}",
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
        }

    latency_ms = round((time.time() - start) * 1000, 2)
    return {
        "response": content,
        "tokens_used": tokens_used,
        "provider": provider,
        "model": model,
        "latency_ms": latency_ms,
    }


def cmd_models(payload):
    provider = payload.get("provider")
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}"}
    cfg = PROVIDERS[provider]
    models = [{"id": m, "name": m, "free": True} for m in cfg["models"]]
    return {"models": models}


def cmd_test(payload):
    import httpx

    provider = payload.get("provider")
    api_key = payload.get("api_key")

    if provider not in PROVIDERS:
        return {"ok": False, "error": f"Unknown provider: {provider}"}
    if provider != "ollama" and not api_key:
        return {"ok": False, "error": f"Missing 'api_key' for provider '{provider}'"}

    cfg = PROVIDERS[provider]
    test_model = cfg["models"][0]
    test_messages = [{"role": "user", "content": "ping"}]

    try:
        if provider == "gemini":
            call_gemini(httpx, test_model, api_key, test_messages)
        elif provider == "ollama":
            call_ollama(httpx, test_model, test_messages)
        elif provider == "openrouter":
            call_openai_compatible(
                httpx, cfg["endpoint"], test_model, api_key, test_messages,
                extra_headers={
                    "HTTP-Referer": "https://omega-ai.local",
                    "X-Title": "OMEGA-AI",
                },
            )
        else:
            call_openai_compatible(httpx, cfg["endpoint"], test_model, api_key, test_messages)
        return {"ok": True}
    except httpx.HTTPStatusError as e:
        body = ""
        try:
            body = e.response.text[:300]
        except Exception:
            pass
        return {"ok": False, "error": f"HTTP {e.response.status_code}: {body}"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


COMMANDS = {
    "chat": cmd_chat,
    "models": cmd_models,
    "test": cmd_test,
}


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        err("Usage: omega.py <chat|models|test> [json_payload]")
        return

    command = sys.argv[1]
    if command not in COMMANDS:
        err(f"Unknown command: {command}. Use one of: {', '.join(COMMANDS)}")
        return

    if len(sys.argv) >= 3:
        raw = sys.argv[2]
    else:
        raw = sys.stdin.read()

    try:
        payload = json.loads(raw) if raw and raw.strip() else {}
    except json.JSONDecodeError as e:
        err(f"Invalid JSON input: {e}")
        return

    try:
        result = COMMANDS[command](payload)
    except Exception as e:
        result = {"error": f"{type(e).__name__}: {e}"}

    out(result)


if __name__ == "__main__":
    main()
