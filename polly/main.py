# polly/main.py
import argparse
import sys
from rich.console import Console
from rich.table import Table

from .core import PollyIDE
from .config import ConfigManager
from .utils import upgrade_polly
from .models import MODELS_DB, TIER_PAID, CAP_SEARCH, CAP_REASONING, CAP_CODE

console = Console()

def list_models():
    """Выводит красивую таблицу моделей"""
    table = Table(title="Pollinations Models Available in Polly")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Capabilities", style="magenta")
    table.add_column("Tier", style="yellow")
    table.add_column("Description", style="dim")

    for mid, info in MODELS_DB.items():
        caps = []
        if CAP_SEARCH in info["caps"]: caps.append("🔍")
        if CAP_REASONING in info["caps"]: caps.append("🧠")
        if CAP_CODE in info["caps"]: caps.append("💻")
        if "vision" in info["caps"]: caps.append("👁️")
        
        tier_str = "💎 PAID" if info["tier"] == TIER_PAID else "Free"
        
        table.add_row(mid, info["name"], " ".join(caps), tier_str, info["desc"])
    
    console.print(table)
    console.print("\n[dim]Legend: 🔍 Search | 🧠 Reasoning | 💻 Coding | 👁️ Vision[/]")

def main():
    parser = argparse.ArgumentParser(description="Polly - AI IDE CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # polly config
    cfg_parser = subparsers.add_parser("config", help="Configure Polly")
    cfg_parser.add_argument("--key", help="API Key")
    cfg_parser.add_argument("--model", help="Select Model ID")
    cfg_parser.add_argument("--reasoning", choices=["on", "off"], help="Thinking Mode")
    cfg_parser.add_argument("--prompt-file", help="Custom System Prompt")

    # polly models
    subparsers.add_parser("models", help="List available models")
    
    # polly upgrade
    subparsers.add_parser("upgrade", help="Upgrade Polly")
    
    # polly reset
    subparsers.add_parser("reset", help="Reset all settings")

    args, unknown = parser.parse_known_args()
    mgr = ConfigManager()

    # --- HANDLERS ---
    
    if args.command == "models":
        list_models()
        return

    if args.command == "upgrade":
        upgrade_polly()
        return

    if args.command == "config":
        if args.key: mgr.update("api_key", args.key)
        if args.model: 
            if args.model not in MODELS_DB:
                console.print(f"[red]Warning: Model '{args.model}' not in DB, but trying anyway.[/]")
            mgr.update("model", args.model)
        if args.reasoning: mgr.update("reasoning", args.reasoning == "on")
        if args.prompt_file: mgr.update("custom_prompt_path", args.prompt_file)
        
        # Show Config
        curr = mgr.load()
        console.print(f"[green]Config Updated:[/]\nModel: {curr['model']}\nReasoning: {curr['reasoning']}\nKey: {'Set' if curr['api_key'] else 'None'}")
        return

    # Запуск IDE
    ide = PollyIDE()
    
    # Если запущен с аргументами типа: polly "fix this"
    if unknown:
        msg = " ".join(unknown)
        console.print(f"[bold blue]You:[/] {msg}")
        ide.history.append({"role": "user", "content": msg})
        ide.run_stream()
    else:
        ide.start()

if __name__ == "__main__":
    main()
