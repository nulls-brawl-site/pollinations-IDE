# polly/utils.py
import subprocess
import sys
from rich.console import Console

console = Console()

def upgrade_polly():
    """Обновляет Polly через git (заглушка для будущего репозитория)"""
    console.print("[yellow]Checking for updates...[/]")
    
    # URL твоего будущего репозитория
    # repo_url = "https://github.com/YOUR_USERNAME/polly.git"
    
    # CMD = [sys.executable, "-m", "pip", "install", "--upgrade", f"git+{repo_url}"]
    
    # try:
    #     subprocess.check_call(CMD)
    #     console.print("[green]Polly upgraded successfully! Restart needed.[/]")
    # except subprocess.CalledProcessError as e:
    #     console.print(f"[red]Upgrade failed: {e}[/]")
    
    console.print("[dim]Update feature is currently disabled until GitHub release.[/]")

def print_banner(model_name):
    console.print(f"[bold green]Polly IDE[/] [dim]v2.1[/]")
    console.print(f"[dim]Engine: {model_name}[/]")
