from rich.console import Console                        from rich.table import Table
from rich import box
                                                        console = Console()

CAP_SEARCH = "search"                                   CAP_REASONING = "reasoning"                             CAP_VISION = "vision"
CAP_AUDIO = "audio"
CAP_CODE = "code"                                       TIER_FREE = "free"
TIER_PAID = "paid"                                      
# СТРОГО ПО СПИСКУ POLLINATIONS
MODELS_DB = {
    # --- TEXT / CODING ---
    "openai": {"name": "GPT-5 Mini", "caps": [CAP_VISION], "tier": TIER_FREE, "desc": "Standard"},
    "openai-fast": {"name": "GPT-5 Nano", "caps": [CAP_VISION], "tier": TIER_FREE, "desc": "Fast & Cheap"},
    "openai-large": {"name": "GPT-5.2", "caps": [CAP_VISION, CAP_REASONING], "tier": TIER_FREE, "desc": "Powerful"},
    "qwen-coder": {"name": "Qwen3 Coder 30B", "caps": [CAP_CODE], "tier": TIER_FREE, "desc": "Top Coding Model"},
    "deepseek": {"name": "DeepSeek V3.2", "caps": [CAP_REASONING, CAP_CODE], "tier": TIER_FREE, "desc": "Reasoning & Code"},
    "mistral": {"name": "Mistral Small 3.2 24B", "caps": [], "tier": TIER_FREE, "desc": "General Purpose"},         "grok": {"name": "xAI Grok 4 Fast", "caps": [], "tier": TIER_FREE, "desc": "Fast Text"},                        "nova-fast": {"name": "Amazon Nova Micro", "caps": [], "tier": TIER_FREE, "desc": "Micro Model"},                                                                       # --- GOOGLE GEMINI ---
    "gemini-fast": {"name": "Gemini 2.5 Flash Lite", "caps": [CAP_VISION, CAP_SEARCH, CAP_CODE], "tier": TIER_FREE, "desc": "Fast with Search"},
    "gemini-search": {"name": "Gemini 3 Flash (Search)", "caps": [CAP_VISION, CAP_SEARCH, CAP_CODE], "tier": TIER_FREE, "desc": "Optimized for Search"},
    "gemini": {"name": "Gemini 3 Flash", "caps": [CAP_VISION, CAP_AUDIO, CAP_SEARCH, CAP_CODE], "tier": TIER_FREE, "desc": "Balanced"},                                     "gemini-large": {"name": "Gemini 3 Pro", "caps": [CAP_VISION, CAP_AUDIO, CAP_REASONING, CAP_SEARCH], "tier": TIER_PAID, "desc": "PAID ONLY"},
    "gemini-legacy": {"name": "Gemini 2.5 Pro", "caps": [CAP_VISION, CAP_AUDIO, CAP_REASONING, CAP_SEARCH, CAP_CODE], "tier": TIER_PAID, "desc": "PAID ONLY"},                                                                      # --- ANTHROPIC CLAUDE ---
    "claude-fast": {"name": "Claude Haiku 4.5", "caps": [CAP_VISION], "tier": TIER_FREE, "desc": "Fastest Claude"},
    "claude": {"name": "Claude Sonnet 4.5", "caps": [CAP_VISION], "tier": TIER_FREE, "desc": "Intelligent Coding"},
    "claude-large": {"name": "Claude Opus 4.5", "caps": [CAP_VISION], "tier": TIER_PAID, "desc": "PAID ONLY"},  
    # --- SEARCH & REASONING ---                            "perplexity-fast": {"name": "Perplexity Sonar", "caps": [CAP_SEARCH], "tier": TIER_FREE, "desc": "Search Engine"},
    "perplexity-reasoning": {"name": "Perplexity Sonar Reasoning", "caps": [CAP_REASONING, CAP_SEARCH], "tier": TIER_FREE, "desc": "Thinking Search"},                      "nomnom": {"name": "NomNom", "caps": [CAP_SEARCH], "tier": TIER_FREE, "desc": "Experimental Search"},           "kimi": {"name": "Moonshot Kimi K2.5", "caps": [CAP_VISION, CAP_REASONING], "tier": TIER_FREE, "desc": "Thinking Model"},                                               "minimax": {"name": "MiniMax M2.1", "caps": [CAP_REASONING], "tier": TIER_FREE, "desc": "Thinking Model"},
    "glm": {"name": "Z.ai GLM-4.7", "caps": [CAP_REASONING], "tier": TIER_FREE, "desc": "Thinking Model"},                                                                  # --- SPECIAL ---
    "openai-audio": {"name": "GPT-4o Mini Audio", "caps": [CAP_AUDIO, CAP_VISION], "tier": TIER_FREE, "desc": "Audio Native"},
    "chickytutor": {"name": "ChickyTutor", "caps": [], "tier": TIER_FREE, "desc": "Language Tutor"},
    "midijourney": {"name": "MIDIjourney", "caps": [], "tier": TIER_FREE, "desc": "Music Generation"},          }
                                                        def supports_search(model_name):
    """                                                     Проверяет, поддерживает ли указанная модель веб-поиск.
    Используется в tools.py для фильтрации доступных инструментов.                                                  """                                                     if model_name not in MODELS_DB:
        return False                                        return CAP_SEARCH in MODELS_DB[model_name]["caps"]
                                                        def list_models_table():
    table = Table(title="🤖 Polly Models (Pollinations API)", box=box.ROUNDED)
    table.add_column("ID", style="cyan bold")
    table.add_column("Name", style="green")                 table.add_column("Caps", style="magenta")
    table.add_column("Tier", style="yellow")

    for mid, info in MODELS_DB.items():
        caps = []
        if CAP_SEARCH in info["caps"]: caps.append("🔍")
        if CAP_REASONING in info["caps"]: caps.append(" 🧠")
        if CAP_CODE in info["caps"]: caps.append("💻")
        if CAP_VISION in info["caps"]: caps.append("👁️")         if CAP_AUDIO in info["caps"]: caps.append("🎙️")

        tier = "💎" if info["tier"] == TIER_PAID else " 🆓"
        table.add_row(mid, info["name"], " ".join(caps), tier)                                                  
    console.print(table)
