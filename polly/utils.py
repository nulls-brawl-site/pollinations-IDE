import subprocess
import sys
import os
import shutil
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

POLLY_HOME = Path.home() / ".pollinations"
REPO_DIR = POLLY_HOME / "repo"
REPO_URL = "https://github.com/nulls-brawl-site/pollinations-CLI.git"

def restart_program():
    console.print("[yellow]Restarting Pollinations CLI...[/]")
    time.sleep(1)
    new_argv = [arg for arg in sys.argv if "upgrade" not in arg.lower() and "/upgrade" not in arg.lower()]
    os.execv(sys.executable, [sys.executable] + new_argv)

def run_cmd(command, cwd=None, error_msg="Command failed"):
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            console.print(f"[red]{error_msg}: {result.stderr.strip()}[/]")
            return False
        return True
    except Exception as e:
        console.print(f"[red]{error_msg}: {e}[/]")
        return False

def upgrade_polly():
    console.print(Panel(
        f"[bold yellow]Pollinations CLI Updater[/]\n[dim]Source: {REPO_URL}[/]",
        title="Upgrade", border_style="yellow"
    ))

    try:
        if shutil.which("git") is None:
            console.print("[red]Error: 'git' is not installed.[/]")
            return

        if not POLLY_HOME.exists():
            POLLY_HOME.mkdir(parents=True)

        if REPO_DIR.exists():
            if (REPO_DIR / ".git").exists():
                console.print("[dim]Pulling latest changes...[/]")
                run_cmd(["git", "fetch", "origin"], cwd=REPO_DIR)
                run_cmd(["git", "reset", "--hard", "origin/main"], cwd=REPO_DIR)
            else:
                console.print("[yellow]Corrupt repo detected. Re-cloning...[/]")
                shutil.rmtree(REPO_DIR)
                run_cmd(["git", "clone", REPO_URL, str(REPO_DIR)])
        else:
            console.print("[dim]Cloning repository...[/]")
            run_cmd(["git", "clone", REPO_URL, str(REPO_DIR)])

        console.print("[dim]Installing package...[/]")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", ".", "--upgrade", "--quiet"],
            cwd=REPO_DIR, capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            console.print(f"[bold red]Installation failed![/]\n{result.stderr[:500]}")
            return

        console.print("[bold green]Upgrade complete! Restarting...[/]")
        restart_program()

    except Exception as e:
        console.print(f"[bold red]Critical Error:[/]\n{str(e)}")
