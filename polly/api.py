# polly/api.py
import requests
import json
from .tools import get_tools_schema

API_URL = "https://gen.pollinations.ai/v1/chat/completions"

def create_payload(model, history, config_data):
    # Логика Reasoning (Thinking)
    # Если включено - ставим высокий бюджет токенов для качества
    # Если выключено - ставим минимальный/disabled
    thinking_payload = {"type": "disabled"}
    
    if config_data.get("reasoning"):
        # Для Pollinations бюджет мышления в токенах
        thinking_payload = {
            "type": "enabled", 
            "budget_tokens": 4096 # Высокое качество
        }

    return {
        "model": model,
        "messages": history,
        "tools": get_tools_schema(model),
        "stream": True,
        "thinking": thinking_payload,
        # Если модель поддерживает reasoning_effort (openai o1/o3), можно добавить:
        # "reasoning_effort": "high" 
    }

def stream_completion(payload, api_key=None):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=120)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network Error: {e}")
