# polly/core.py
import json
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live

from .config import ConfigManager
from .api import create_payload, stream_completion
from .tools import execute_local_tool

console = Console()

class PollyIDE:
    def __init__(self):
        self.cfg_mgr = ConfigManager()
        self.cfg = self.cfg_mgr.load()
        self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]

    def run_stream(self):
        payload = create_payload(self.cfg["model"], self.history, self.cfg)
        
        full_content = ""
        tool_buffer = []
        
        # UI State
        markdown_text = ""
        
        # В режиме стриминга мы обновляем панель в реальном времени
        with Live(Panel("Waiting for response...", title="Polly", border_style="blue"), refresh_per_second=10) as live:
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

                        # 1. Текст
                        if "content" in delta and delta["content"]:
                            txt = delta["content"]
                            full_content += txt
                            markdown_text += txt
                            live.update(Panel(Markdown(markdown_text), title=f"Polly ({self.cfg['model']})", border_style="blue"))

                        # 2. Мысли (Reasoning)
                        if "reasoning_content" in delta and delta["reasoning_content"]:
                            # Можно выводить отдельно, если нужно
                            pass 

                        # 3. Инструменты (Tool Calls)
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

                    except:
                        continue
            except Exception as e:
                live.update(Panel(f"[red]Error: {e}[/]", title="Crash"))
                return

        # Пост-обработка
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
                
                # Если это Google Search и он был разрешен (хотя API может сам вернуть ответ)
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
            
            # Рекурсия для обработки результата инструмента
            self.run_stream()

    def start(self):
        console.clear()
        console.print(Panel(f"[bold green]Polly IDE v2.1[/]\n[dim]Model: {self.cfg['model']} | Reasoning: {self.cfg['reasoning']}[/]", border_style="green"))
        
        while True:
            try:
                user_in = Prompt.ask("\n[bold blue]You[/]")
                if not user_in: continue
                if user_in.lower() in ['exit', 'quit']: break
                if user_in.lower() == 'clear':
                    self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]
                    console.print("[yellow]Memory Cleared[/]")
                    continue

                self.history.append({"role": "user", "content": user_in})
                self.run_stream()
            except KeyboardInterrupt:
                break
