# polly/models.py

# Возможности моделей
CAP_SEARCH = "search"
CAP_REASONING = "reasoning"
CAP_VISION = "vision"
CAP_AUDIO = "audio"
CAP_CODE = "code"
TIER_FREE = "free"
TIER_PAID = "paid"

# База данных моделей Pollinations (актуализирована по твоему списку)
MODELS_DB = {
    # --- GOOGLE GEMINI ---
    "gemini-fast": {
        "name": "Google Gemini 2.5 Flash Lite",
        "caps": [CAP_VISION, CAP_SEARCH, CAP_CODE],
        "tier": TIER_FREE,
        "desc": "Быстрый, умеет искать и видеть."
    },
    "gemini-search": {
        "name": "Google Gemini 3 Flash (Search)",
        "caps": [CAP_VISION, CAP_SEARCH, CAP_CODE],
        "tier": TIER_FREE,
        "desc": "Специализирован на поиске."
    },
    "gemini": {
        "name": "Google Gemini 3 Flash",
        "caps": [CAP_VISION, CAP_AUDIO, CAP_SEARCH, CAP_CODE],
        "tier": TIER_FREE,
        "desc": "Баланс скорости и функций."
    },
    "gemini-large": {
        "name": "Google Gemini 3 Pro",
        "caps": [CAP_VISION, CAP_AUDIO, CAP_REASONING, CAP_SEARCH],
        "tier": TIER_PAID,
        "desc": "Мощная модель. Требует платный API Key."
    },
    "gemini-legacy": {
        "name": "Google Gemini 2.5 Pro",
        "caps": [CAP_VISION, CAP_AUDIO, CAP_REASONING, CAP_SEARCH, CAP_CODE],
        "tier": TIER_PAID,
        "desc": "Легаси Pro версия. Платная."
    },

    # --- PERPLEXITY ---
    "perplexity-fast": {
        "name": "Perplexity Sonar",
        "caps": [CAP_SEARCH],
        "tier": TIER_FREE,
        "desc": "Онлайн-поисковик."
    },
    "perplexity-reasoning": {
        "name": "Perplexity Sonar Reasoning",
        "caps": [CAP_REASONING, CAP_SEARCH],
        "tier": TIER_FREE,
        "desc": "Поиск + Мышление."
    },
    "nomnom": {
        "name": "NomNom",
        "caps": [CAP_SEARCH],
        "tier": TIER_FREE,
        "desc": "Экспериментальная модель с поиском."
    },

    # --- CLAUDE (Без поиска) ---
    "claude": {
        "name": "Anthropic Claude Sonnet 4.5",
        "caps": [CAP_VISION],
        "tier": TIER_FREE,
        "desc": "Умный, идеален для кода. Нет поиска."
    },
    "claude-fast": {
        "name": "Anthropic Claude Haiku 4.5",
        "caps": [CAP_VISION],
        "tier": TIER_FREE,
        "desc": "Быстрый Claude."
    },
    "claude-large": {
        "name": "Anthropic Claude Opus 4.5",
        "caps": [CAP_VISION],
        "tier": TIER_PAID,
        "desc": "Самый умный Claude. Платный."
    },

    # --- OPENAI / OTHERS ---
    "openai": {"name": "GPT-5 Mini", "caps": [CAP_VISION], "tier": TIER_FREE, "desc": "Стандарт."},
    "openai-large": {"name": "GPT-5.2", "caps": [CAP_VISION, CAP_REASONING], "tier": TIER_FREE, "desc": "Большой GPT."},
    "deepseek": {"name": "DeepSeek V3.2", "caps": [CAP_REASONING], "tier": TIER_FREE, "desc": "Отличный кодер с мышлением."},
    "qwen-coder": {"name": "Qwen3 Coder 30B", "caps": [CAP_CODE], "tier": TIER_FREE, "desc": "Спец по коду."},
    "mistral": {"name": "Mistral Small 3.2", "caps": [], "tier": TIER_FREE, "desc": "Европейская модель."},
}

def get_model_info(model_id):
    return MODELS_DB.get(model_id, {"name": model_id, "caps": [], "tier": TIER_FREE, "desc": "Unknown"})

def supports_search(model_id):
    return CAP_SEARCH in get_model_info(model_id)["caps"]
