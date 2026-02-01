import subprocess
import sys
import os
import time
from rich.console import Console
from rich.panel import Panel

console = Console()
REPO_URL = "https://github.com/nulls-brawl-site/pollinations-IDE.git"

def restart_program():
    """Перезапускает текущий скрипт"""
    console.print("[yellow]🔄 Restarting Polly...[/]")
    time.sleep(1)
    # Заменяем текущий процесс новым
    os.execv(sys.executable, [sys.executable] + sys.argv)

def upgrade_polly():
    """Проверяет обновления и устанавливает их"""
    console.print(Panel(f"[yellow]Checking remote repository...[/]\n[dim]{REPO_URL}[/]", title="System Upgrade"))
    
    try:
        # 1. Запускаем pip install --upgrade git+...
        # Используем capture_output, чтобы проанализировать ответ
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", f"git+{REPO_URL}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        output = process.stdout + process.stderr
        
        if process.returncode != 0:
            console.print(f"[bold red]❌ Update failed![/]\n{output}")
            return

        # 2. Анализируем вывод pip
        if "Requirement already satisfied" in output and "Successfully installed" not in output:
            console.print("[bold green]✅ Polly is already up to date![/]")
            return
        
        # 3. Если было обновление
        console.print("[bold green]🚀 Upgrade Successful![/]")
        console.print("[dim]Updating dependencies...[/]")
        
        # На всякий случай обновляем зависимости (если в setup.py что-то поменялось)
        subprocess.run([sys.executable, "-m", "pip", "install", "."], capture_output=True)
        
        # 4. Перезапуск
        restart_program()

    except Exception as e:
        console.print(f"[bold red]❌ Critical Error:[/]\n{str(e)}")
