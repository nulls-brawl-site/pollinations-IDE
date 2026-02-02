import argparse
import sys
import os
from rich.console import Console
from .core import PollyIDE
from .config import ConfigManager
from .utils import upgrade_polly
from .models import list_models_table

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Polly - AI IDE CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("config", help="Configure Polly")
    subparsers.add_parser("models", help="List available models")
    subparsers.add_parser("upgrade", help="Force update Polly")
    subparsers.add_parser("reset", help="Reset all settings")
    subparsers.add_parser("help", help="Show this help message")
    
    p_parser = subparsers.add_parser("prompt", help="Set custom system prompt file")
    p_parser.add_argument("path", help="Path to prompt.txt")

    args, unknown = parser.parse_known_args()
    mgr = ConfigManager()

    if args.command == "help":
        parser.print_help()
        return

    if args.command == "models":
        list_models_table()
        return

    if args.command == "upgrade":
        upgrade_polly()
        return

    if args.command == "reset":
        console.print("[yellow]Please use /reset inside the app or delete ~/.polly[/]")
        return
    
    if args.command == "prompt":
        if os.path.exists(args.path):
            mgr.update("custom_prompt_path", os.path.abspath(args.path))
            console.print(f"[green]System prompt set to {args.path}[/]")
        else:
            console.print(f"[red]File not found: {args.path}[/]")
        return

    ide = PollyIDE()
    if unknown:
        msg = " ".join(unknown)
        console.print(f"[bold blue]You:[/] {msg}")
        ide.history.append({"role": "user", "content": msg})
        ide.run_stream()
    else:
        ide.start()

if __name__ == "__main__":
    main()
