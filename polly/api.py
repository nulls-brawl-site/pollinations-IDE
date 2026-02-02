import requests
import json
from rich.console import Console
from .tools import get_tools_schema

console = Console()
API_URL = "https://gen.pollinations.ai/v1/chat/completions"

def create_payload(model, history, config_data):
    # Получаем инструменты
    tools = get_tools_schema(config_data)
    
    payload = {
        "model": model,
        "messages": history,
        "tools": tools,
        "stream": True,
    }

    # --- ЛОГИКА REASONING (THINKING) ---
    if config_data.get("reasoning", False):
        
        # 🛑 КРИТИЧЕСКИЙ ФИКС ДЛЯ GEMINI 🛑
        # Gemini падает с ошибкой "missing thought_signature", если включить Thinking + Tools.
        # Мы ПРИНУДИТЕЛЬНО игнорируем reasoning для всех моделей Gemini.
        if "gemini" in model.lower():
            # Можно вывести предупреждение в консоль, если хочешь
            # console.print("[dim]Info: Reasoning disabled for Gemini to allow Tool usage.[/]")
            pass 

        # Для Claude и Kimi (у них Thinking работает с тулзами нормально)
        elif "claude" in model.lower() or "kimi" in model.lower():
            payload["thinking"] = {
                "type": "enabled", 
                "budget_tokens": config_data.get("budget_tokens", 4096)
            }
        
        # Для OpenAI o1/o3
        elif "o1" in model.lower() or "o3" in model.lower():
            payload["reasoning_effort"] = config_data.get("reasoning_effort", "high")

    return payload

def stream_completion(payload, api_key=None):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=120)
        
        # Если 400/500, пробуем показать реальную причину
        if response.status_code >= 400:
            try:
                err = response.json()
                msg = err.get('error', {}).get('message', str(err))
                # Выводим в консоль, чтобы ты видел, что именно ответил Google
                print(f"\n[API ERROR]: {msg}")
            except:
                print(f"\n[API ERROR]: Status {response.status_code}")
                
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network Error: {e}")
