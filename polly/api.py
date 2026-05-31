import requests
import json
from rich.console import Console
from .tools import get_tools_schema

console = Console()
DEFAULT_API_URL = "https://gen.pollinations.ai/v1/chat/completions"

def get_api_config(config_data):
    active = config_data.get("active_provider")
    providers = config_data.get("providers", {})

    if active and active in providers:
        p = providers[active]
        return {
            "url": p.get("url", DEFAULT_API_URL),
            "key": p.get("key", config_data.get("api_key")),
            "name": active,
        }
    return {
        "url": DEFAULT_API_URL,
        "key": config_data.get("api_key"),
        "name": "pollinations",
    }

def sanitize_history(history):
    if not history:
        return []

    cleaned = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content")
        tool_calls = msg.get("tool_calls")

        has_content = content is not None and str(content).strip() != ""
        has_tool_calls = tool_calls is not None and len(tool_calls) > 0
        is_tool_result = role == "tool"

        if not has_content and not has_tool_calls and not is_tool_result:
            continue

        if not cleaned:
            cleaned.append(msg)
            continue

        prev = cleaned[-1]

        if role == 'user' and prev['role'] == 'user':
            prev_content = prev.get("content", "")
            curr_content = msg.get("content", "")
            prev['content'] = f"{prev_content}\n\n{curr_content}"
        else:
            cleaned.append(msg)

    return cleaned

def create_payload(model, history, config_data):
    clean_history = sanitize_history(history)
    tools = get_tools_schema(config_data)

    payload = {
        "model": model,
        "messages": clean_history,
        "tools": tools,
        "stream": True,
    }

    if config_data.get("reasoning", False):
        if "gemini" in model.lower():
            pass
        elif "claude" in model.lower() or "kimi" in model.lower():
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": config_data.get("budget_tokens", 4096)
            }
        elif "o1" in model.lower() or "o3" in model.lower():
            payload["reasoning_effort"] = config_data.get("reasoning_effort", "high")

    return payload

def stream_completion(payload, config_data):
    api = get_api_config(config_data)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api['key']}",
    }

    try:
        response = requests.post(
            api["url"],
            headers=headers,
            json=payload,
            stream=True,
            timeout=120
        )

        if response.status_code >= 400:
            try:
                err = response.json()
                msg = err.get('error', {}).get('message', str(err))
                console.print(f"\n[bold red][API ERROR][/]: {msg}")
            except:
                console.print(f"\n[bold red][API ERROR][/]: Status {response.status_code}")
                console.print(response.text[:200])
            response.raise_for_status()

        return response

    except requests.exceptions.RequestException as e:
        raise Exception(f"Network Error: {e}")
