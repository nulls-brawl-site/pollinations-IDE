import subprocess
import sys
import os
import time
from rich.console import Console
from rich.panel import Panel

console = Console()
REPO_URL = "https://github.com/nulls-brawl-site/pollinations-IDE.git"

def restart_program():
    """
    Перезапускает Polly.
    ВАЖНО: Удаляет аргументы 'upgrade' из команды запуска, 
    чтобы не попасть в бесконечный цикл обновлений.
    """
    console.print("[yellow]🔄 Restarting Polly system...[/]")
    time.sleep(1)
    
    # Фильтруем аргументы: убираем всё, что связано с апгрейдом
    # Было: ['/usr/bin/polly', 'upgrade']
    # Стало: ['/usr/bin/polly']
    new_argv = [arg for arg in sys.argv if "upgrade" not in arg.lower() and "/upgrade" not in arg.lower()]
    
    # Перезапускаем процесс с чистыми аргументами
    os.execv(sys.executable, [sys.executable] + new_argv)

def upgrade_polly():
    """
    Обновляет Polly с GitHub.
    Использует --no-cache-dir для проверки свежих коммитов,
    но без --force-reinstall, чтобы не качать лишние библиотеки.
    """
    console.print(Panel(f"[yellow]Pulling updates from GitHub...[/]\n[dim]{REPO_URL}[/]", title="System Upgrade"))
    
    try:
        # Убрали --force-reinstall, оставили только --upgrade и --no-cache-dir
        # Это заставит pip проверить Git, но не будет перекачивать rich/requests если они есть.
        cmd = [
            sys.executable, "-m", "pip", "install", 
            "--upgrade", 
            "--no-cache-dir", 
            f"git+{REPO_URL}"
        ]
        
        process = subprocess.run(cmd, text=True)
        
        if process.returncode != 0:
            console.print(f"[bold red]❌ Update failed with code {process.returncode}[/]")
            return

        console.print("[bold green]🚀 Upgrade Successful![/]")
        console.print("[dim]Launching new version...[/]")
        
        # Перезапуск в обычный режим
        restart_program()

    except Exception as e:
        console.print(f"[bold red]❌ Critical Error:[/]\n{str(e)}")
