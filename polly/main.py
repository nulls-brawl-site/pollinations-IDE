# polly/main.py
import argparse
from rich.console import Console
from .core import PollyIDE
from .config import ConfigManager
from .utils import upgrade_polly
from .models import list_models_table, MODELS_DB # Импортируем новую функцию

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Polly - AI IDE CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    cfg_parser = subparsers.add_parser("config", help="Configure Polly")
    cfg_parser.add_argument("--key", help="API Key")
    cfg_parser.add_argument("--model", help="Select Model ID")
    cfg_parser.add_argument("--reasoning", choices=["on", "off"], help="Thinking Mode")
    cfg_parser.add_argument("--prompt-file", help="Custom System Prompt")

    subparsers.add_parser("models", help="List available models")
    subparsers.add_parser("upgrade", help="Upgrade Polly")
    subparsers.add_parser("reset", help="Reset all settings")

    args, unknown = parser.parse_known_args()
    mgr = ConfigManager()

    if args.command == "models":
        list_models_table() # Используем красивую таблицу
        return

    if args.command == "upgrade":
        upgrade_polly()
        return

    if args.command == "config":
        if args.key: mgr.update("api_key", args.key)
        if args.model: mgr.update("model", args.model)
        if args.reasoning: mgr.update("reasoning", args.reasoning == "on")
        if args.prompt_file: mgr.update("custom_prompt_path", args.prompt_file)
        
        curr = mgr.load()
        console.print(f"[green]Config Updated:[/]\nModel: {curr['model']}")
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
