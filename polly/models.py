from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

CAP_SEARCH = "search"
CAP_REASONING = "reasoning"
CAP_VISION = "vision"
CAP_AUDIO = "audio"
CAP_CODE = "code"
TIER_FREE = "free"
TIER_PAID = "paid"

# Твой список моделей (сократил desc для красоты, но суть та же)
MODELS_DB = {
    "gemini-fast": {"name": "Gemini 2.5 Flash Lite", "caps": [CAP_VISION, CAP_SEARCH, CAP_CODE], "tier": TIER_FREE, "desc": "Быстрый, видит, ищет"},
    "gemini-search": {"name": "Gemini 3 Flash (Search)", "caps": [CAP_VISION, CAP_SEARCH], "tier": TIER_FREE, "desc": "Спец по Google Search"},
    "gemini": {"name": "Gemini 3 Flash", "caps": [CAP_VISION, CAP_AUDIO, CAP_SEARCH, CAP_CODE], "tier": TIER_FREE, "desc": "Баланс скорости/ума"},
    "gemini-large": {"name": "Gemini 3 Pro", "caps": [CAP_REASONING, CAP_SEARCH], "tier": TIER_PAID, "desc": "Мощнейшая, ПЛАТНАЯ"},
    "perplexity-fast": {"name": "Perplexity Sonar", "caps": [CAP_SEARCH], "tier": TIER_FREE, "desc": "Чистый поисковик"},
    "perplexity-reasoning": {"name": "Perplexity Sonar R.", "caps": [CAP_REASONING, CAP_SEARCH], "tier": TIER_FREE, "desc": "Поиск + Мышление"},
    "claude": {"name": "Claude Sonnet 4.5", "caps": [CAP_VISION, CAP_CODE], "tier": TIER_FREE, "desc": "Топ для кода"},
    "claude-fast": {"name": "Claude Haiku 4.5", "caps": [CAP_VISION], "tier": TIER_FREE, "desc": "Быстрый Claude"},
    "openai": {"name": "GPT-5 Mini", "caps": [CAP_VISION], "tier": TIER_FREE, "desc": "Стандарт OpenAI"},
    "deepseek": {"name": "DeepSeek V3.2", "caps": [CAP_REASONING, CAP_CODE], "tier": TIER_FREE, "desc": "Китаец, пишет код"},
    "qwen-coder": {"name": "Qwen 3 Coder", "caps": [CAP_CODE], "tier": TIER_FREE, "desc": "Спец по коду"},
}

def get_model_info(model_id):
    return MODELS_DB.get(model_id, {"name": model_id, "caps": [], "tier": TIER_FREE, "desc": "Unknown"})

def supports_search(model_id):
    return CAP_SEARCH in get_model_info(model_id)["caps"]

def list_models_table():
    table = Table(title="🤖 Pollinations Models", box=box.ROUNDED, padding=(0, 1))
    
    # Настройки колонок, чтобы не "плыло"
    table.add_column("ID", style="cyan bold", no_wrap=True)
    table.add_column("Name", style="green", no_wrap=True)
    table.add_column("Caps", style="magenta")
    table.add_column("Tier", style="yellow", no_wrap=True)
    table.add_column("Description", style="dim")

    for mid, info in MODELS_DB.items():
        caps_icons = []
        if CAP_SEARCH in info["caps"]: caps_icons.append("🔍")
        if CAP_REASONING in info["caps"]: caps_icons.append("🧠")
        if CAP_CODE in info["caps"]: caps_icons.append("💻")
        if CAP_VISION in info["caps"]: caps_icons.append("👁️")
        
        tier_str = "💎 PAID" if info["tier"] == TIER_PAID else "Free"
        
        table.add_row(mid, info["name"], " ".join(caps_icons), tier_str, info["desc"])
    
    console.print(table)
