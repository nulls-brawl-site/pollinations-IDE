import subprocess
import sys
from rich.console import Console
from rich.panel import Panel

console = Console()

# Твой репозиторий
REPO_URL = "https://github.com/nulls-brawl-site/pollinations-IDE.git"

def upgrade_polly():
    """Обновляет Polly напрямую с GitHub"""
    console.print(Panel(f"[yellow]Connecting to GitHub...[/]\n[dim]{REPO_URL}[/]", title="System Upgrade"))
    
    try:
        # Используем текущий интерпретатор python для вызова pip
        # Флаг --upgrade обновит пакет, даже если он уже установлен
        # Флаг --force-reinstall заставит переписать файлы
        cmd = [
            sys.executable, "-m", "pip", "install", 
            "--upgrade", 
            f"git+{REPO_URL}"
        ]
        
        # Запускаем процесс обновления
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode == 0:
            console.print(f"\n[bold green]✅ Upgrade Successful![/]")
            console.print("[dim]Please restart Polly to apply changes.[/]")
            
            # Показываем лог последних изменений (если бы мы их парсили, но пока просто успех)
            sys.exit(0)
        else:
            console.print(f"\n[bold red]❌ Upgrade Failed[/]")
            console.print(f"[red]Error log:[/]\n{process.stderr}")
            
    except Exception as e:
        console.print(f"\n[bold red]❌ Critical Error:[/]\n{str(e)}")

def print_banner(model_name):
    console.print(f"[bold green]Polly IDE[/] [dim]v2.1[/]")
    console.print(f"[dim]Engine: {model_name}[/]")
