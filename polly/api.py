import requests
import json
from .tools import get_tools_schema

API_URL = "https://gen.pollinations.ai/v1/chat/completions"

def create_payload(model, history, config_data):
    # Базовый пейлоад
    payload = {
        "model": model,
        "messages": history,
        "tools": get_tools_schema(model),
        "stream": True,
    }

    # Логика добавления Reasoning параметров только если это включено
    if config_data.get("reasoning", False):
        # 1. Для моделей Claude и Kimi (используют 'thinking')
        # Gemini тоже переходит на thinking, добавим его сюда
        if any(x in model for x in ["claude", "kimi", "gemini"]):
            payload["thinking"] = {
                "type": "enabled", 
                "budget_tokens": config_data.get("budget_tokens", 4096)
            }
        
        # 2. Для моделей OpenAI o1/o3 (используют 'reasoning_effort')
        elif "o1" in model or "o3" in model:
            payload["reasoning_effort"] = config_data.get("reasoning_effort", "high")
        
        # 3. DeepSeek R1 обычно работает сам по себе, но если нужно принудить:
        elif "deepseek" in model:
            # Pollinations иногда игнорирует, но попробуем
            pass 
            
    # ВАЖНО: Если reasoning выключен, мы НЕ добавляем поле "thinking" вообще.
    return payload

def stream_completion(payload, api_key=None):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        # Увеличим таймаут, так как reasoning-модели могут думать долго перед первым токеном
        response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=180)
        
        # Если сервер вернул ошибку, пробуем прочитать тело ответа для деталей перед raise
        if response.status_code >= 400:
            try:
                error_msg = response.json()
                print(f"API Error Details: {error_msg}")
            except:
                pass 
                
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network Error ({e}) - Check parameters or model compatibility.")
