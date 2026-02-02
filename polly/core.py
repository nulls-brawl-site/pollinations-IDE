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
        try:
            parts = shlex.split(cmd_line)
        except ValueError:
            parts = cmd_line.split()
            
        base = parts[0].lower()
        
        if base == "/reset":
            self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]
            console.print("[yellow]🧹 Context cleared.[/]")
            return True
        elif base == "/upgrade":
            upgrade_polly()
            return True
        elif base == "/models":
            list_models_table()
            return True
        elif base == "/config":
            console.print(Panel(json.dumps(self.cfg, indent=2), title="Config", border_style="cyan"))
            return True
        elif base == "/prompt":
            if len(parts) < 2:
                console.print("[red]Usage: /prompt /path/to/custom_prompt.txt[/]")
                return True
            path = parts[1]
            if os.path.exists(path):
                self.cfg_mgr.update("custom_prompt_path", os.path.abspath(path))
                self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]
                console.print(f"[green]System prompt loaded from {path}. Memory reset.[/]")
            else:
                console.print(f"[red]File not found: {path}[/]")
            return True
        elif base == "/google":
            if len(parts) < 2: return True
            val = parts[1].lower() == "on"
            self.cfg_mgr.update("google_search", val)
            self.cfg = self.cfg_mgr.load()
            console.print(f"[green]Google Search: {val}[/]")
            return True
        elif base == "/reasoning":
            if len(parts) < 2: return True
            val = parts[1].lower() == "on"
            self.cfg_mgr.update("reasoning", val)
            self.cfg = self.cfg_mgr.load()
            console.print(f"[green]Reasoning: {val}[/]")
            return True
        elif base == "/api":
            if len(parts) < 2: return True
            self.cfg_mgr.update("api_key", parts[1])
            self.cfg = self.cfg_mgr.load()
            console.print("[green]API Key saved.[/]")
            return True
        elif base == "/model":
            if len(parts) < 2: return True
            self.cfg_mgr.update("model", parts[1])
            self.cfg = self.cfg_mgr.load()
            console.print(f"[green]Model: {parts[1]}[/]")
            return True
        elif base == "/help":
            console.print("[bold]Commands:[/]\n/reset, /upgrade, /models, /config, /prompt <path>\n/google on/off, /reasoning on/off, /api key, /model name")
            return True
        elif base == "/exit":
            exit(0)
        return False

    def run_stream(self):
        payload = create_payload(self.cfg["model"], self.history, self.cfg)
        full_content = ""
        tool_buffer = []
        markdown_text = ""
        
        with Live(Panel("...", title=f"Polly ({self.cfg['model']})", border_style="blue"), refresh_per_second=10) as live:
            try:
                response = stream_completion(payload, self.cfg["api_key"])
                for line in response.iter_lines():
                    if not line: continue
                    decoded = line.decode('utf-8')
                    if not decoded.startswith('data: '): continue
                    
                    data_str = decoded.replace('data: ', '')
                    if data_str == '[DONE]': 
                        break
                    
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0]["delta"]
                        
                        if "content" in delta and delta["content"]:
                            txt = delta["content"]
                            full_content += txt
                            markdown_text += txt
                            live.update(Panel(Markdown(markdown_text), title=f"Polly ({self.cfg['model']})", border_style="blue"))
                        
                        if "tool_calls" in delta:
                            t_calls = delta["tool_calls"]
                            for tc in t_calls:
                                if "index" in tc:
                                    idx = tc["index"]
                                    while len(tool_buffer) <= idx:
                                        tool_buffer.append({"id": "", "function": {"name": "", "arguments": ""}, "type": "function"})
                                    
                                    if "id" in tc: 
                                        tool_buffer[idx]["id"] += tc["id"]
                                    
                                    if "function" in tc:
                                        if "name" in tc["function"]: 
                                            tool_buffer[idx]["function"]["name"] += tc["function"]["name"]
                                        if "arguments" in tc["function"]: 
                                            tool_buffer[idx]["function"]["arguments"] += tc["function"]["arguments"]
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                live.update(Panel(f"[red]Error: {e}[/]", title="Error"))
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

                # АНИМАЦИЯ
                spinner_text = f"Running {func_name}..."
                if func_name == "write_file":
                    path = args.get('path', '???')
                    spinner_text = f"Writing file {path}..."
                elif func_name == "read_file":
                    spinner_text = f"Reading file {args.get('path')}..."
                elif func_name == "execute_command":
                    spinner_text = f"Executing: {args.get('command')}"
                elif func_name == "google_search":
                    spinner_text = f"Searching Google..."

                with console.status(f"[bold white]{spinner_text}[/]", spinner="dots"):
                    if func_name == "google_search":
                        result = "Search results injected by backend."
                    else:
                        result = execute_local_tool(func_name, args)

                console.print(f"[dim]🛠 {spinner_text} [green]Done.[/][/]")

                self.history.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": func_name,
                    "content": str(result)
                })
            
            self.run_stream()

    def start(self):
        console.clear()
        console.print(Panel(f"[bold green]Polly IDE v2.4[/]\n[dim]Model: {self.cfg['model']} | Reasoning: {self.cfg['reasoning']}[/]", border_style="green"))
        
        while True:
            try:
                u = Prompt.ask(f"\n[bold blue]You ({os.path.basename(os.getcwd())})[/]")
                if not u: continue
                if u.startswith("/"):
                    if self.handle_slash_command(u): continue
                self.history.append({"role": "user", "content": u})
                self.run_stream()
            except KeyboardInterrupt:
                break                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0]["delta"]
                        
                        if "content" in delta and delta["content"]:
                            txt = delta["content"]
                            full_content += txt
                            markdown_text += txt
                            live.update(Panel(Markdown(markdown_text), title=f"Polly ({self.cfg['model']})", border_style="blue"))
                        
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
                live.update(Panel(f"[red]Error: {e}[/]", title="Error"))
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

                # --- КРУТАЯ АНИМАЦИЯ ЗДЕСЬ ---
                # Формируем текст ПЕРЕД входом в статус
                spinner_text = f"Running {func_name}..."
                
                if func_name == "write_file":
                    # Показываем полный путь
                    path = args.get('path', '???')
                    spinner_text = f"Writing file {path}..."
                elif func_name == "read_file":
                    spinner_text = f"Reading file {args.get('path')}..."
                elif func_name == "execute_command":
                    spinner_text = f"Executing: {args.get('command')}"
                elif func_name == "google_search":
                    spinner_text = f"Searching Google..."

                # Запускаем спиннер с текстом
                with console.status(f"[bold white]{spinner_text}[/]", spinner="dots"):
                    if func_name == "google_search":
                        result = "Search results injected by backend."
                    else:
                        result = execute_local_tool(func_name, args)

                # Финальный лог (статичный)
                console.print(f"[dim]🛠 {spinner_text} [green]Done.[/][/]")

                self.history.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": func_name,
                    "content": str(result)
                })
            
            self.run_stream()

    def start(self):
        console.clear()
        console.print(Panel(f"[bold green]Polly IDE v2.4[/]\n[dim]Model: {self.cfg['model']} | Reasoning: {self.cfg['reasoning']}[/]", border_style="green"))
        
        while True:
            try:
                u = Prompt.ask(f"\n[bold blue]You ({os.path.basename(os.getcwd())})[/]")
                if not u: continue
                if u.startswith("/"):
                    if self.handle_slash_command(u): continue
                self.history.append({"role": "user", "content": u})
                self.run_stream()
            except KeyboardInterrupt:
                break                                    idx = tc["index"]
                                    while len(tool_buffer) <= idx:
                                        tool_buffer.append({"id": "", "function": {"name": "", "arguments": ""}, "type": "function"})
                                    if "id" in tc: tool_buffer[idx]["id"] += tc["id"]
                                    if "function" in tc:
                                        if "name" in tc["function"]: tool_buffer[idx]["function"]["name"] += tc["function"]["name"]
                                        if "arguments" in tc["function"]: tool_buffer[idx]["function"]["arguments"] += tc["function"]["arguments"]
                    except: continue
            except Exception as e:
                live.update(Panel(f"[red]Error: {e}[/]", title="Error"))
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

                # Анимация
                status_msg = f"Running {func_name}..."
                if func_name == "write_file": status_msg = f"Writing {args.get('path')}..."
                
                with console.status(f"[bold yellow]{status_msg}[/]", spinner="dots"):
                    if func_name == "google_search":
                        result = "Search results injected by backend."
                    else:
                        result = execute_local_tool(func_name, args)

                console.print(f"[dim]🛠 Tool: {func_name} ({args.get('path','') or args.get('command','')})[/]")

                self.history.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": func_name,
                    "content": str(result)
                })
            
            self.run_stream()

    def start(self):
        console.clear()
        console.print(Panel(f"[bold green]Polly IDE v2.3.1[/]\n[dim]Model: {self.cfg['model']}[/]", border_style="green"))
        while True:
            try:
                u = Prompt.ask(f"\n[bold blue]You ({os.path.basename(os.getcwd())})[/]")
                if not u: continue
                if u.startswith("/"):
                    if self.handle_slash_command(u): continue
                self.history.append({"role": "user", "content": u})
                self.run_stream()
            except KeyboardInterrupt:
                break
