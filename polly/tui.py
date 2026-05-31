import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.text import Text
from rich import box
from rich.columns import Columns

console = Console()

WELCOME_ART = r"""
[bold #eab308]
   ___      _ _ _       _       _             _____ _    ___ 
  / _ \___ | | (_)_ __ (_)_ __ (_)_ _  __ _ / __| | |  |_ _|
 / /_)/ _ \| | | | '_ \| | '_ \| | ' \/ _` | (__| |_|  | | 
/ ___/ (_) | | | | | | | | | | | | | | (_| |\___|  _|  | | 
\/    \___/|_|_|_|_| |_|_|_| |_|/ |_|\__,_|     \_\_| |___|
                            |__/                         
[/]
"""

def clear():
    os.system('clear'  if os.name == 'posix' else 'cls')

def header(title="", subtitle=""):
    clear()
    console.print(WELCOME_ART)
    if title:
        console.print(f"[bold #eab308]{title}[/]")
    if subtitle:
        console.print(f"[dim]{subtitle}[/]")
    console.print()

def panel(content, title="", style="blue"):
    console.print(Panel(content, title=title, border_style=style))

def ask(prompt_text, default=None, password=False):
    return Prompt.ask(f"[bold white]{prompt_text}[/]", default=default, password=password)

def confirm(prompt_text, default=True):
    return Confirm.ask(f"[bold white]{prompt_text}[/]", default=default)

def info(text):
    console.print(f"[dim]  {text}[/]")

def success(text):
    console.print(f"[green]  {text}[/]")

def warn(text):
    console.print(f"[yellow]  {text}[/]")

def error(text):
    console.print(f"[red]  {text}[/]")

def divider():
    console.print("[dim]" + "─" * 60 + "[/]")

def menu(title_text, options, back_option=True):
    """Show interactive menu with arrow-like selection using Rich Prompt."""
    items = list(options.keys())
    if back_option:
        items.append("Back")

    table = Table(title=f"[bold #eab308]{title_text}[/]", box=box.SIMPLE, border_style="dim blue")
    table.add_column("#", style="bold cyan", width=4)
    table.add_column("Action", style="white")
    table.add_column("Description", style="dim")

    for i, key in enumerate(items, 1):
        desc = options.get(key, "")
        table.add_row(str(i), key, desc)

    console.print(table)
    console.print()

    choice = Prompt.ask(
        f"[bold white]Select[/] [dim](1-{len(items)})[/]",
        default=str(len(items)),
        show_default=False
    )

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(items):
            return items[idx]
    except ValueError:
        pass
    return items[-1] if back_option else None

def provider_dashboard(providers, active_provider, has_api_key):
    """Beautiful provider management dashboard."""
    clear()
    console.print(WELCOME_ART)
    console.print("[bold #eab308]  Providers[/] [dim]─ Manage API accounts[/]\n")

    table = Table(box=box.ROUNDED, border_style="magenta", title="[bold]API Providers[/]")
    table.add_column("Status", style="bold", width=8)
    table.add_column("Name", style="cyan bold")
    table.add_column("Endpoint", style="dim")
    table.add_column("Key", style="dim")

    if has_api_key:
        masked = "..."
        table.add_row(
            "[green]ACTIVE[/]" if not active_provider else "",
            "pollinations",
            "gen.pollinations.ai",
            "****"
        )

    for name, p in providers.items():
        is_active = name == active_provider
        table.add_row(
            "[green]ACTIVE[/]" if is_active else "",
            name,
            p.get("url", "")[:45],
            "****" if p.get("key") else "[red]no key[/]"
        )

    console.print(table)
    console.print()

    options = {}
    options["Add Provider"] = "Connect a new OpenAI-compatible API"
    if providers:
        options["Switch Provider"] = "Change active API provider"
        options["Remove Provider"] = "Delete a provider account"
    if has_api_key:
        options["Default (Pollinations)"] = "Use built-in Pollinations API"

    choice = menu("Actions", options)
    return choice

def add_provider_wizard():
    """Step-by-step wizard to add a new provider."""
    clear()
    console.print(WELCOME_ART)
    console.print("[bold #eab308]  Add Provider[/] [dim]─ Connect OpenAI-compatible API[/]\n")

    panel(
        "[dim]Enter your OpenAI v1 compatible API details.\n"
        "Examples: OpenAI, Groq, Together, Ollama, vLLM, LocalAI[/]",
        title="New Provider",
        style="magenta"
    )
    console.print()

    name = ask("Provider name (e.g. groq, openai, local)", default="custom")

    console.print()
    info("The chat completions endpoint URL:")
    info("  OpenAI:  https://api.openai.com/v1/chat/completions")
    info("  Groq:    https://api.groq.com/openai/v1/chat/completions")
    info("  Ollama:  http://localhost:11434/v1/chat/completions")
    console.print()

    url = Prompt.ask(
        "[bold white]Endpoint URL[/]",
        default="https://api.openai.com/v1/chat/completions"
    )

    console.print()
    key = Prompt.ask(
        "[bold white]API Key[/] [dim](enter to skip)[/]",
        password=True,
        default=""
    )

    console.print()
    success(f"Provider [bold]{name}[/] ready: [dim]{url}[/]")
    console.print()
    confirm("Save and continue?", default=True)

    return name, url, key

def model_selector(current_model, config_data):
    """Beautiful searchable model selector."""
    from .models import MODELS_DB

    clear()
    console.print(WELCOME_ART)
    console.print("[bold #eab308]  Select Model[/] [dim]─ Choose AI brain[/]\n")

    tier_map = {"free": "[green]FREE[/]", "paid": "[yellow]PAID[/]"}
    table = Table(box=box.ROUNDED, border_style="cyan", title="[bold]Available Models[/]")
    table.add_column("#", style="dim", width=4)
    table.add_column("ID", style="cyan bold")
    table.add_column("Name", style="white")
    table.add_column("Features", style="magenta")
    table.add_column("Tier", style="yellow")

    model_keys = list(MODELS_DB.keys())
    for i, mid in enumerate(model_keys, 1):
        info = MODELS_DB[mid]
        caps = ", ".join(info["caps"]) if info["caps"] else "-"
        tier = tier_map.get(info["tier"], info["tier"])
        marker = "[bold #eab308]>[/]" if mid == current_model else " "
        table.add_row(str(i), f"{marker} {mid}", info["name"], caps, tier)

    console.print(table)
    console.print()
    console.print("[dim]Current:[/] [bold cyan]{0}[/]".format(current_model))
    console.print()

    choice = Prompt.ask(
        f"[bold white]Model ID or #[dim](1-{len(model_keys)})[/]",
        default=current_model
    )

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(model_keys):
            return model_keys[idx]
    except ValueError:
        pass

    if choice in MODELS_DB:
        return choice
    return current_model

def switch_provider_dialog(providers, active_provider, has_api_key):
    """Dialog to switch between providers."""
    clear()
    console.print(WELCOME_ART)
    console.print("[bold #eab308]  Switch Provider[/] [dim]─ Select active API[/]\n")

    items = {}
    if has_api_key:
        items["pollinations"] = "[dim]gen.pollinations.ai[/]"
    for name, p in providers.items():
        marker = " [bold #eab308](current)[/]" if name == active_provider else ""
        items[name] = f"[dim]{p.get('url', '')[:40]}[/]{marker}"

    table = Table(box=box.ROUNDED, border_style="magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Provider", style="cyan bold")
    table.add_column("Info", style="dim")

    keys = list(items.keys())
    for i, name in enumerate(keys, 1):
        table.add_row(str(i), name, items[name])

    console.print(table)
    console.print()

    choice = Prompt.ask(
        f"[bold white]Select[dim](1-{len(keys)})[/]",
        default="1"
    )

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(keys):
            return keys[idx]
    except ValueError:
        pass
    return None

def remove_provider_dialog(providers):
    """Dialog to remove a provider."""
    clear()
    console.print(WELCOME_ART)
    console.print("[bold #eab308]  Remove Provider[/] [dim]─ Delete account[/]\n")

    if not providers:
        info("No custom providers to remove.")
        Prompt.ask("[dim]Press Enter to continue[/]", default="")
        return None

    items = {name: f"[dim]{p.get('url', '')[:40]}[/]" for name, p in providers.items()}

    table = Table(box=box.ROUNDED, border_style="red")
    table.add_column("#", style="dim", width=4)
    table.add_column("Provider", style="cyan bold")
    table.add_column("URL", style="dim")

    keys = list(items.keys())
    for i, name in enumerate(keys, 1):
        table.add_row(str(i), name, items[name])

    console.print(table)
    console.print()

    choice = Prompt.ask(
        f"[bold red]Remove #[dim](1-{len(keys)})[/]",
        default="1"
    )

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(keys):
            name = keys[idx]
            if confirm(f"Delete [bold red]{name}[/]?", default=False):
                return name
    except ValueError:
        pass
    return None

def startup_dashboard(cfg, model_list_fn):
    """Beautiful startup screen with interactive options."""
    clear()
    console.print(WELCOME_ART)

    api = cfg.get_api_config()

    table = Table(box=box.SIMPLE, show_header=False, border_style="dim blue")
    table.add_column("key", style="dim", width=14)
    table.add_column("value", style="white")

    model_info = cfg.cfg.get("model", "claude")
    provider = api["name"]
    reasoning = "ON" if cfg.cfg.get("reasoning") else "OFF"
    google = "ON" if cfg.cfg.get("google_search") else "OFF"
    key_status = "[green]set[/]" if api["key"] else "[red]not set[/]"

    table.add_row("  Model", f"[bold cyan]{model_info}[/]")
    table.add_row("  Provider", f"[bold magenta]{provider}[/]")
    table.add_row("  API Key", key_status)
    table.add_row("  Reasoning", reasoning)
    table.add_row("  Google", google)

    console.print(Panel(table, title="[bold #eab308]Pollinations CLI[/]", border_style="yellow"))
    console.print()

    rows = []
    rows.append(Panel(
        "[bold cyan]New Chat[/]\n[dim]Start building[/]",
        border_style="cyan"
    ))
    rows.append(Panel(
        "[bold magenta]Providers[/]\n[dim]Manage APIs[/]",
        border_style="magenta"
    ))
    rows.append(Panel(
        "[bold green]Models[/]\n[dim]Choose AI brain[/]",
        border_style="green"
    ))
    rows.append(Panel(
        "[bold yellow]Config[/]\n[dim]Settings[/]",
        border_style="yellow"
    ))

    console.print(Columns(rows, equal=True))
    console.print()

    options = {
        "Chat": "Start a conversation with AI",
        "Providers": "Manage API accounts and keys",
        "Models": "Select AI model",
        "Config": "View and edit settings",
        "Exit": "Quit application",
    }

    return menu("Dashboard", options, back_option=False)
