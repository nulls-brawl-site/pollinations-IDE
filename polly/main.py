import argparse
import sys
from rich.console import Console
from .core import PollyIDE
from .config import ConfigManager
from .utils import upgrade_polly
from .models import list_models_table

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Polly - AI IDE CLI")
    
    # Делаем подкоманды опциональными, чтобы просто polly запускало IDE
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("config", help="Configure Polly")
    subparsers.add_parser("models", help="List available models")
    subparsers.add_parser("upgrade", help="Force update Polly")
    subparsers.add_parser("reset", help="Reset all settings")
    subparsers.add_parser("help", help="Show this help message")

    # Если пользователь ввел polly --help или -h, argparse сам обработает это.
    # Но если polly help, то нам нужен хендлер ниже.

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
        # Тут можно вызвать логику ресета
        console.print("[yellow]Please use /reset inside the app or delete ~/.polly[/]")
        return
    
    # Если команда config (но без аргументов она мало полезна в CLI, лучше в чате /config)
    if args.command == "config":
        # Можно добавить парсинг аргументов, но мы перенесли всё в /slash commands
        console.print("[dim]Use /config inside Polly or edit ~/.polly/config.json[/]")
        return

    # ЗАПУСК IDE
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
