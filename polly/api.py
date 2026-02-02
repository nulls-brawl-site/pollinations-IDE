import requests
import json
from rich.console import Console
from .tools import get_tools_schema

console = Console()
API_URL = "https://gen.pollinations.ai/v1/chat/completions"

def sanitize_history(history):
    """
    Чистит историю для строгих API (Perplexity, Anthropic).
    1. Склеивает подряд идущие сообщения 'user'.
    2. Удаляет пустые сообщения.
    """
    if not history: return []
    
    cleaned = []
    for msg in history:
        # Пропускаем пустой контент, если это не вызов инструмента
        if not msg.get("content") and not msg.get("tool_calls"):
            continue

        if not cleaned:
            cleaned.append(msg)
            continue
        
        prev = cleaned[-1]
        
        # Если User идет сразу за User -> склеиваем их в одно сообщение
        if msg['role'] == 'user' and prev['role'] == 'user':
            prev['content'] += "\n\n" + str(msg['content'])
        else:
            cleaned.append(msg)
    
    return cleaned

def create_payload(model, history, config_data):
    # 1. Сначала чистим историю от дублей
    clean_history = sanitize_history(history)
    
    # 2. Получаем инструменты
    tools = get_tools_schema(config_data)
    
    payload = {
        "model": model,
        "messages": clean_history, # Отправляем чистую историю
        "tools": tools,
        "stream": True,
    }

    # --- ЛОГИКА REASONING (THINKING) ---
    if config_data.get("reasoning", False):
        # Отключаем thinking для Gemini (конфликт с Tools)
        if "gemini" in model.lower():
            pass 
            
        # Perplexity R1 / Sonar Reasoning не требует параметра thinking, он встроен.
        # Но если мы захотим форсировать для других:
        elif "claude" in model.lower() or "kimi" in model.lower():
            payload["thinking"] = {
                "type": "enabled", 
                "budget_tokens": config_data.get("budget_tokens", 4096)
            }
        elif "o1" in model.lower() or "o3" in model.lower():
            payload["reasoning_effort"] = config_data.get("reasoning_effort", "high")

    return payload

def stream_completion(payload, api_key=None):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=120)
        
        if response.status_code >= 400:
            try:
                err = response.json()
                msg = err.get('error', {}).get('message', str(err))
                # Вывод ошибки в консоль
                console.print(f"\n[bold red][API ERROR][/]: {msg}")
            except:
                console.print(f"\n[bold red][API ERROR][/]: Status {response.status_code}")
                
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network Error: {e}")
