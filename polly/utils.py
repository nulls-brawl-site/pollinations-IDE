import subprocess
import sys
import os
import shutil
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

# Папка, где будет лежать исходный код Polly
POLLY_HOME = Path.home() / ".polly"
REPO_DIR = POLLY_HOME / "repo"
REPO_URL = "https://github.com/nulls-brawl-site/pollinations-IDE.git"

def restart_program():
    """Перезапускает Polly, очищая аргументы от команд обновления"""
    console.print("[yellow]🔄 Restarting Polly system...[/]")
    time.sleep(1)
    
    # Убираем аргументы, связанные с апгрейдом, чтобы не зациклить
    new_argv = [arg for arg in sys.argv if "upgrade" not in arg.lower() and "/upgrade" not in arg.lower()]
    
    # Перезапускаем текущий интерпретатор с новым кодом
    os.execv(sys.executable, [sys.executable] + new_argv)

def run_cmd(command, cwd=None, error_msg="Command failed"):
    """Запускает shell команду и проверяет ошибки"""
    try:
        subprocess.check_call(command, cwd=cwd, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # Если тихо не вышло, пробуем громко, чтобы юзер видел ошибку
        subprocess.check_call(command, cwd=cwd, shell=False)

def upgrade_polly():
    """
    Надежное обновление:
    1. Клонирует/Пуллит репозиторий вручную.
    2. Устанавливает через pip install .
    """
    console.print(Panel(f"[bold yellow]System Update[/]\n[dim]Source: {REPO_URL}[/]", title="Updater", border_style="yellow"))
    
    try:
        # 1. Проверяем наличие git
        if shutil.which("git") is None:
            console.print("[red]❌ Error: 'git' is not installed on this system.[/]")
            return

        # 2. Подготавливаем папку репозитория
        if not POLLY_HOME.exists():
            POLLY_HOME.mkdir(parents=True)

        if REPO_DIR.exists():
            # Если папка есть, проверяем, это git репозиторий или мусор
            if (REPO_DIR / ".git").exists():
                console.print("📥 Pulling latest changes from GitHub...")
                # Сбрасываем локальные изменения и тянем новое
                run_cmd(["git", "fetch", "origin"], cwd=REPO_DIR)
                run_cmd(["git", "reset", "--hard", "origin/main"], cwd=REPO_DIR)
            else:
                # Если папка битая, удаляем
                console.print("[yellow]⚠️ Corrupt repo detected. Re-cloning...[/]")
                shutil.rmtree(REPO_DIR)
                run_cmd(["git", "clone", REPO_URL, str(REPO_DIR)])
        else:
            # Чистый клон
            console.print("📥 Cloning repository...")
            run_cmd(["git", "clone", REPO_URL, str(REPO_DIR)])

        # 3. Установка зависимостей и пакета
        console.print("📦 Installing package...")
        
        # pip install . (из папки репозитория)
        # --upgrade нужно, чтобы обновить зависимости
        cmd = [sys.executable, "-m", "pip", "install", ".", "--upgrade"]
        
        process = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True)
        
        if process.returncode != 0:
            console.print(f"[bold red]❌ Installation failed![/]\n{process.stderr}")
            return

        console.print("[bold green]✅ Update Complete![/]")
        
        # 4. Перезапуск
        restart_program()

    except Exception as e:
        console.print(f"[bold red]❌ Critical Error:[/]\n{str(e)}")
