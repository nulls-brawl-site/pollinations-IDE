import requests
import json
from .tools import get_tools_schema

API_URL = "https://gen.pollinations.ai/v1/chat/completions"

def create_payload(model, history, config_data):
    # Получаем список инструментов на основе конфига
    tools = get_tools_schema(config_data)
    
    payload = {
        "model": model,
        "messages": history,
        "tools": tools,
        "stream": True,
    }

    # --- ЛОГИКА THINKING / REASONING ---
    # Мы включаем thinking ТОЛЬКО если пользователь попросил (/reasoning on)
    
    if config_data.get("reasoning", False):
        
        # ⚠️ ФИКС ДЛЯ GEMINI + TOOLS ⚠️
        # Gemini (Vertex AI) падает с ошибкой "missing a thought_signature",
        # если включить Thinking и одновременно использовать Tools (Function Calling).
        # Поэтому для Gemini мы принудительно ОТКЛЮЧАЕМ thinking, если есть инструменты.
        if "gemini" in model:
            # Не добавляем thinking, чтобы избежать 400 ошибки.
            # Модель все равно умная, справится и так.
            pass

        # Для Claude (работает нормально с тулзами)
        elif "claude" in model or "kimi" in model:
            payload["thinking"] = {
                "type": "enabled", 
                "budget_tokens": config_data.get("budget_tokens", 4096)
            }
        
        # Для OpenAI o1/o3
        elif "o1" in model or "o3" in model:
            payload["reasoning_effort"] = config_data.get("reasoning_effort", "high")

    return payload

def stream_completion(payload, api_key=None):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=180)
        
        # Читаем ошибку, если есть
        if response.status_code >= 400:
            try:
                err = response.json()
                # Красивый вывод ошибки для отладки
                print(f"\n[API ERROR]: {err.get('error', {}).get('message', 'Unknown')}")
            except:
                pass
                
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network/API Error. {e}")
