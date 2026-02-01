import json
import os
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live

from .config import ConfigManager
from .api import create_payload, stream_completion
from .tools import execute_local_tool
from .utils import upgrade_polly, restart_program
from .models import list_models_table

console = Console()

class PollyIDE:
    def __init__(self):
        self.cfg_mgr = ConfigManager()
        self.cfg = self.cfg_mgr.load()
        self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]

    def handle_slash_command(self, cmd):
        """Обработчик команд типа /reset, /upgrade"""
        parts = cmd.split()
        base = parts[0].lower()
        
        if base == "/reset":
            self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]
            console.print("[yellow]🧹 Context memory cleared.[/]")
            return True
            
        elif base == "/upgrade":
            upgrade_polly() # Если обновится, то перезапустится внутри функции
            return True
            
        elif base == "/models":
            list_models_table()
            return True

        elif base == "/config":
            # Показываем конфиг
            console.print(Panel(json.dumps(self.cfg, indent=2), title="Current Config", border_style="cyan"))
            return True
            
        elif base == "/exit":
            exit(0)

        elif base == "/help":
            console.print("[bold]Available Commands:[/]")
            console.print(" /reset   - Clear chat history")
            console.print(" /upgrade - Check for updates")
            console.print(" /models  - List available AI models")
            console.print(" /config  - Show current settings")
            console.print(" /exit    - Quit Polly")
            return True
            
        return False

    def run_stream(self):
        payload = create_payload(self.cfg["model"], self.history, self.cfg)
        full_content = ""
        tool_buffer = []
        markdown_text = ""
        
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
                            # Обновляем панель с текущей директорией в заголовке
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

        if tool_buffer:
            self.history.append({"role": "assistant", "content": full_content, "tool_calls": tool_buffer})
            
            for tool in tool_buffer:
                func_name = tool["function"]["name"]
                call_id = tool["id"]
                try:
                    args = json.loads(tool["function"]["arguments"])
                except:
                    args = {}

                console.print(f"[dim]🔧 Tool: {func_name}[/]")
                
                if func_name == "google_search":
                    result = "Context injected by Pollinations Backend."
                else:
                    result = execute_local_tool(func_name, args)

                self.history.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": func_name,
                    "content": str(result)
                })
            self.run_stream()

    def start(self):
        console.clear()
        console.print(Panel(f"[bold green]Polly IDE v2.2[/]\n[dim]Model: {self.cfg['model']} | CWD: {os.getcwd()}[/]", border_style="green"))
        
        while True:
            try:
                user_in = Prompt.ask(f"\n[bold blue]You ({os.path.basename(os.getcwd())})[/]")
                if not user_in: continue
                
                # Проверяем на slash команду
                if user_in.startswith("/"):
                    if self.handle_slash_command(user_in):
                        continue

                self.history.append({"role": "user", "content": user_in})
                self.run_stream()
            except KeyboardInterrupt:
                break
