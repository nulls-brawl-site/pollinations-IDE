import subprocess
import sys
import os
import time
from rich.console import Console
from rich.panel import Panel

console = Console()
# Твой репозиторий
REPO_URL = "https://github.com/nulls-brawl-site/pollinations-IDE.git"

def restart_program():
    """Перезапускает текущий процесс Polly"""
    console.print("[yellow]🔄 Restarting Polly system...[/]")
    time.sleep(1)
    # Заменяем текущий процесс новым экземпляром python
    os.execv(sys.executable, [sys.executable] + sys.argv)

def upgrade_polly():
    """Агрессивное обновление: качает последнюю версию кода, игнорируя кэш и номера версий"""
    console.print(Panel(f"[yellow]Force Pulling from GitHub...[/]\n[dim]{REPO_URL}[/]", title="System Upgrade"))
    
    try:
        # Добавляем флаги:
        # --force-reinstall : переустановить, даже если версия та же
        # --no-cache-dir    : не смотреть в кэш pip, качать свежее с гита
        cmd = [
            sys.executable, "-m", "pip", "install", 
            "--upgrade", 
            "--force-reinstall", 
            "--no-cache-dir", 
            f"git+{REPO_URL}"
        ]
        
        # Запускаем и показываем прогресс (pip будет писать в stdout)
        # В этот раз не скрываем вывод, чтобы было видно, что идет скачивание
        process = subprocess.run(cmd, text=True)
        
        if process.returncode != 0:
            console.print(f"[bold red]❌ Update failed with code {process.returncode}[/]")
            return

        console.print("[bold green]🚀 Upgrade Successful![/]")
        console.print("[dim]Applying changes...[/]")
        
        # Перезапуск
        restart_program()

    except Exception as e:
        console.print(f"[bold red]❌ Critical Error:[/]\n{str(e)}")
