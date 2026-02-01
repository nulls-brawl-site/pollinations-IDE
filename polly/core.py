import json
import os
import shlex
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live

from .config import ConfigManager
from .api import create_payload, stream_completion
from .tools import execute_local_tool
from .utils import upgrade_polly
from .models import list_models_table

console = Console()

class PollyIDE:
    def __init__(self):
        self.cfg_mgr = ConfigManager()
        self.cfg = self.cfg_mgr.load()
        self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]

    def handle_slash_command(self, cmd_line):
        """Обработчик команд типа /reset, /api, /google"""
        try:
            # Используем shlex для правильного разбора кавычек: /api "my key"
            parts = shlex.split(cmd_line)
        except ValueError:
            parts = cmd_line.split()
            
        base = parts[0].lower()
        
        # --- COMMANDS ---
        
        if base == "/reset":
            self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]
            console.print("[yellow]🧹 Context memory cleared.[/]")
            return True
            
        elif base == "/upgrade":
            upgrade_polly()
            return True
            
        elif base == "/models":
            list_models_table()
            return True

        elif base == "/config":
            console.print(Panel(json.dumps(self.cfg, indent=2), title="Current Config", border_style="cyan"))
            return True
        
        # --- SETTINGS TOGGLES ---

        elif base == "/google":
            if len(parts) < 2: 
                console.print("[red]Usage: /google on|off[/]")
                return True
            val = parts[1].lower() == "on"
            self.cfg_mgr.update("google_search", val)
            self.cfg = self.cfg_mgr.load() # Reload config
            console.print(f"[green]Google Search set to: {val}[/]")
            return True

        elif base == "/reasoning":
            if len(parts) < 2: 
                console.print("[red]Usage: /reasoning on|off[/]")
                return True
            val = parts[1].lower() == "on"
            self.cfg_mgr.update("reasoning", val)
            self.cfg = self.cfg_mgr.load()
            console.print(f"[green]Reasoning (Thinking) set to: {val}[/]")
            return True

        elif base == "/api":
            if len(parts) < 2:
                console.print("[red]Usage: /api \"sk-your-key\"[/]")
                return True
            key = parts[1]
            self.cfg_mgr.update("api_key", key)
            self.cfg = self.cfg_mgr.load()
            console.print("[green]API Key updated.[/]")
            return True
        
        elif base == "/model":
            if len(parts) < 2:
                console.print("[red]Usage: /model name (e.g. claude)[/]")
                return True
            self.cfg_mgr.update("model", parts[1])
            self.cfg = self.cfg_mgr.load()
            console.print(f"[green]Model switched to {parts[1]}[/]")
            return True

        elif base == "/help":
            console.print("[bold cyan]Polly Commands:[/]")
            console.print(" [green]/reset[/]          - Clear history")
            console.print(" [green]/upgrade[/]        - Force update")
            console.print(" [green]/models[/]         - List all models")
            console.print(" [green]/config[/]         - Show settings")
            console.print(" [green]/google on|off[/]  - Toggle search")
            console.print(" [green]/reasoning on|off[/]- Toggle thinking")
            console.print(" [green]/api \"key\"[/]      - Set API key")
            console.print(" [green]/model name[/]     - Switch model")
            return True
            
        elif base == "/exit":
            exit(0)
            
        return False

    def run_stream(self):
        payload = create_payload(self.cfg["model"], self.history, self.cfg)
        full_content = ""
        tool_buffer = []
        markdown_text = ""
        
        # Стриминг текста
        with Live(Panel("...", title=f"Polly ({self.cfg['model']}) @ {os.getcwd()}", border_style="blue"), refresh_per_second=10) as live:
            try:
                response = stream_completion(payload, self.cfg["api_key"])
                for line in response.iter_lines():
                    if not line: continue
                    decoded = line.decode('utf-8')
                    if not decoded.startswith('data: '): continue
                    data_str = decoded.replace('data: ', '')
                    if data_str == '[DONE]': break
                    
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0]["delta"]
                        
                        if "content" in delta and delta["content"]:
                            txt = delta["content"]
                            full_content += txt
                            markdown_text += txt
                            live.update(Panel(Markdown(markdown_text), title=f"Polly ({self.cfg['model']}) @ {os.getcwd()}", border_style="blue"))
                        
                        if "tool_calls" in delta:
                            t_calls = delta["tool_calls"]
                            for tc in t_calls:
                                if "index" in tc:
                                    idx = tc["index"]
                                    while len(tool_buffer) <= idx:
                                        tool_buffer.append({"id": "", "function": {"name": "", "arguments": ""}, "type": "function"})
                                    if "id" in tc: tool_buffer[idx]["id"] += tc["id"]
                                    if "function" in tc:
                                        if "name" in tc["function"]: tool_buffer[idx]["function"]["name"] += tc["function"]["name"]
                                        if "arguments" in tc["function"]: tool_buffer[idx]["function"]["arguments"] += tc["function"]["arguments"]
                    except: continue
            except Exception as e:
                live.update(Panel(f"[red]Error: {e}[/]", title="Crash"))
                return

        if full_content:
            self.history.append({"role": "assistant", "content": full_content})

        # Обработка инструментов ПОСЛЕ завершения текстового стрима
        if tool_buffer:
            self.history.append({"role": "assistant", "content": full_content, "tool_calls": tool_buffer})
            
            for tool in tool_buffer:
                func_name = tool["function"]["name"]
                call_id = tool["id"]
                try:
                    args = json.loads(tool["function"]["arguments"])
                except:
                    args = {}

                # --- АНИМАЦИЯ ИСПОЛНЕНИЯ ---
                # Формируем красивое описание действия
                status_text = f"Executing {func_name}..."
                if func_name == "write_file":
                    status_text = f"Writing file '{args.get('path', 'unknown')}'..."
                elif func_name == "read_file":
                    status_text = f"Reading file '{args.get('path', 'unknown')}'..."
                elif func_name == "execute_command":
                    status_text = f"Running: {args.get('command', '')}..."
                
                # Показываем спиннер, пока выполняется действие
                with console.status(f"[bold yellow]{status_text}[/]", spinner="dots"):
                    if func_name == "google_search":
                        result = "Context injected by Pollinations Backend."
                    else:
                        result = execute_local_tool(func_name, args)

                # Когда закончили, выводим финальную строку (как лог)
                console.print(f"[dim]🛠  Tool: {func_name} ({args.get('path', '') or args.get('command', '')})[/]")

                self.history.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": func_name,
                    "content": str(result)
                })
            
            # Рекурсия (модель видит результат и продолжает отвечать)
            self.run_stream()

    def start(self):
        console.clear()
        console.print(Panel(f"[bold green]Polly IDE v2.3[/]\n[dim]Model: {self.cfg['model']} | Reasoning: {self.cfg['reasoning']}[/]", border_style="green"))
        
        while True:
            try:
                user_in = Prompt.ask(f"\n[bold blue]You ({os.path.basename(os.getcwd())})[/]")
                if not user_in: continue
                
                if user_in.startswith("/"):
                    if self.handle_slash_command(user_in):
                        continue

                self.history.append({"role": "user", "content": user_in})
                self.run_stream()
            except KeyboardInterrupt:
                break
