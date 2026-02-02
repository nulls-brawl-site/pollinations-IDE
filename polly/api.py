import requests
import json                                             from rich.console import Console                        from .tools import get_tools_schema
                                                        console = Console()                                     API_URL = "https://gen.pollinations.ai/v1/chat/completions"

def sanitize_history(history):                              """                                                     Чистит историю для строгих API (Perplexity, Anthropic, Vertex AI).                                              1. Склеивает подряд идущие сообщения 'user'.            2. Удаляет пустые сообщения (кроме функциональных).
    """                                                     if not history: return []

    cleaned = []
    for msg in history:                                         role = msg.get("role")                                  content = msg.get("content")
        tool_calls = msg.get("tool_calls")                                                                              # --- ЛОГИКА ФИЛЬТРАЦИИ ---
        # Мы должны оставить сообщение, если:                   # 1. У него есть непустой контент.
        # 2. ИЛИ это вызов инструмента (Assistant с tool_calls).                                                        # 3. ИЛИ это результат инструмента (Role = tool), даже если контент пустой.                             
        has_content = content is not None and str(content).strip() != ""
        has_tool_calls = tool_calls is not None and len(tool_calls) > 0
        is_tool_result = role == "tool"                                                                                 if not has_content and not has_tool_calls and not is_tool_result:                                                   continue
                                                                if not cleaned:
            cleaned.append(msg)
            continue

        prev = cleaned[-1]                              
        # Если User идет сразу за User -> склеиваем их в одно сообщение
        if role == 'user' and prev['role'] == 'user':
            prev_content = prev.get("content", "")
            curr_content = msg.get("content", "")
            prev['content'] = f"{prev_content}\n\n{curr_content}"
        else:
            cleaned.append(msg)                         
    return cleaned

def create_payload(model, history, config_data):
    # 1. Сначала чистим историю от дублей и пустых сообщений                                                        clean_history = sanitize_history(history)
                                                            # 2. Получаем схему инструментов
    tools = get_tools_schema(config_data)

    payload = {
        "model": model,
        "messages": clean_history,
        "tools": tools,                                         "stream": True,
    }                                                   
    # --- ЛОГИКА REASONING (THINKING) ---
    if config_data.get("reasoning", False):
        # Отключаем thinking для Gemini (часто вызывает конфликт с Tools 400 Bad Request)
        if "gemini" in model.lower():
            pass

        # Для моделей Claude/Kimi можно пробовать включать thinking
        elif "claude" in model.lower() or "kimi" in model.lower():                                                          payload["thinking"] = {
                "type": "enabled",                                      "budget_tokens": config_data.get("budget_tokens", 4096)                                                     }                                                   # Для o1/o3 OpenAI
        elif "o1" in model.lower() or "o3" in model.lower():                                                                payload["reasoning_effort"] = config_data.get("reasoning_effort", "high")                                                                                       return payload
                                                        def stream_completion(payload, api_key=None):               headers = {"Content-Type": "application/json"}
    if api_key:                                                 headers["Authorization"] = f"Bearer {api_key}"  
    try:                                                        response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=120)
                                                                if response.status_code >= 400:                             try:
                err = response.json()
                msg = err.get('error', {}).get('message', str(err))                                                             # Вывод ошибки в консоль                                console.print(f"\n[bold red][API ERROR][/]: {msg}")                                                         except:
                console.print(f"\n[bold red][API ERROR][/]: Status {response.status_code}")
                # Если 400, часто помогает просто напечатать тело, чтобы понять причину
                console.print(response.text[:200])

            # Не вызываем raise_for_status сразу, чтобы поток не падал,
            # но вышестоящий код должен обработать это.
            # Для надежности кидаем исключение.
            response.raise_for_status()
                                                                return response
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network Error: {e}")
