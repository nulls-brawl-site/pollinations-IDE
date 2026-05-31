import json
import os
import shlex
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text
from rich import box

from .config import ConfigManager
from .api import create_payload, stream_completion, get_api_config
from .tools import execute_local_tool
from .utils import upgrade_polly
from .models import list_models_table

console = Console()

POLLY_BANNER = """
[bold yellow]  ____        _ _ _       _       _             _____ _    ___ 
 |  _ \\ ___  | | (_)_ __ (_)_ __ (_)_ _  __ _ / __| | |  |_ _|
 | |_) / _ \\ | | | | '_ \\| | '_ \\| | ' \\/ _` | (__| |_|  | | 
 |  __/ (_) || | | | | | | | | | | | | | (_| |\\__ \\  _|  | | 
 |_|   \\___/ |_|_|_|_| |_|_|_| |_|/ |_|\\__,_||___/_|\\_\\ |___|
                               |__/
[/]
[bold cyan]Pollinations CLI v3.0[/] [dim]AI-powered terminal assistant[/]"""

class PollyIDE:
    def __init__(self):
        self.cfg_mgr = ConfigManager()
        self.cfg = self.cfg_mgr.load()
        self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]
        self._last_md = ""

    def _provider_badge(self):
        api = get_api_config(self.cfg)
        if api["name"] == "pollinations":
            return "[dim yellow]pollinations[/]"
        return f"[bold magenta]{api['name']}[/]"

    def handle_slash_command(self, cmd_line):
        try:
            parts = shlex.split(cmd_line)
        except ValueError:
            parts = cmd_line.split()

        base = parts[0].lower()

        if base == "/reset":
            self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]
            console.print("[yellow]Context cleared.[/]")
            return True

        elif base == "/upgrade" or base == "/update":
            upgrade_polly()
            return True

        elif base == "/models":
            list_models_table()
            return True

        elif base == "/config":
            safe = {k: v for k, v in self.cfg.items() if k not in ("providers",)}
            safe["providers_count"] = len(self.cfg.get("providers", {}))
            safe["active_provider"] = self.cfg.get("active_provider") or "pollinations"
            console.print(Panel(json.dumps(safe, indent=2), title="[bold]Config[/]", border_style="cyan"))
            return True

        elif base == "/providers":
            return self._handle_providers(parts)

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
            if len(parts) < 2:
                console.print(f"[dim]Google Search: {self.cfg.get('google_search', False)}[/]")
                return True
            val = parts[1].lower() in ("on", "true", "1", "yes")
            self.cfg_mgr.update("google_search", val)
            self.cfg = self.cfg_mgr.load()
            console.print(f"[green]Google Search: {val}[/]")
            return True

        elif base == "/reasoning":
            if len(parts) < 2:
                console.print(f"[dim]Reasoning: {self.cfg.get('reasoning', False)}[/]")
                return True
            val = parts[1].lower() in ("on", "true", "1", "yes")
            self.cfg_mgr.update("reasoning", val)
            self.cfg = self.cfg_mgr.load()
            console.print(f"[green]Reasoning: {val}[/]")
            return True

        elif base == "/api":
            if len(parts) < 2:
                masked = self.cfg.get("api_key", "") or ""
                if masked:
                    masked = masked[:8] + "..." + masked[-4:] if len(masked) > 12 else "***"
                console.print(f"[dim]API Key: {masked or 'not set'}[/]")
                return True
            self.cfg_mgr.update("api_key", parts[1])
            self.cfg = self.cfg_mgr.load()
            console.print("[green]API Key saved.[/]")
            return True

        elif base == "/model":
            if len(parts) < 2:
                console.print(f"[dim]Model: {self.cfg.get('model', 'claude')}[/]")
                return True
            self.cfg_mgr.update("model", parts[1])
            self.cfg = self.cfg_mgr.load()
            console.print(f"[green]Model: {parts[1]}[/]")
            return True

        elif base == "/help":
            self._show_help()
            return True

        elif base == "/exit" or base == "/quit":
            console.print("[dim]Goodbye![/]")
            exit(0)

        return False

    def _handle_providers(self, parts):
        sub = parts[1].lower() if len(parts) > 1 else "list"

        if sub == "list":
            providers = self.cfg.get("providers", {})
            active = self.cfg.get("active_provider")
            if not providers:
                console.print("[dim]No custom providers configured. Add one with /providers add[/]")
                return True

            table = Table(title="[bold]Custom Providers[/]", box=box.ROUNDED, border_style="magenta")
            table.add_column("Name", style="cyan bold")
            table.add_column("URL", style="dim")
            table.add_column("Status", style="green")
            for name, p in providers.items():
                marker = " [bold yellow]ACTIVE[/]" if name == active else ""
                table.add_row(name, p.get("url", "")[:50], f"[green]ready{marker}[/]")
            console.print(table)
            return True

        elif sub == "add":
            if len(parts) < 4:
                console.print("[red]Usage: /providers add <name> <url> <api_key>[/]")
                console.print("[dim]Example: /providers add openai https://api.openai.com/v1/chat/completions sk-xxx[/]")
                return True
            name = parts[2]
            url = parts[3]
            key = parts[4] if len(parts) > 4 else ""
            providers = dict(self.cfg.get("providers", {}))
            providers[name] = {"url": url, "key": key}
            self.cfg_mgr.update("providers", providers)
            self.cfg = self.cfg_mgr.load()
            console.print(f"[green]Provider [bold]{name}[/] added.[/]")
            return True

        elif sub == "use":
            if len(parts) < 3:
                console.print("[red]Usage: /providers use <name>[/]")
                return True
            name = parts[2]
            if name == "pollinations":
                self.cfg_mgr.update("active_provider", None)
                self.cfg = self.cfg_mgr.load()
                console.print("[green]Switched to default Pollinations API.[/]")
                return True
            providers = self.cfg.get("providers", {})
            if name not in providers:
                console.print(f"[red]Provider '{name}' not found. Add it with /providers add[/]")
                return True
            self.cfg_mgr.update("active_provider", name)
            self.cfg = self.cfg_mgr.load()
            console.print(f"[green]Switched to provider [bold]{name}[/].[/]")
            return True

        elif sub == "rm" or sub == "remove":
            if len(parts) < 3:
                console.print("[red]Usage: /providers rm <name>[/]")
                return True
            name = parts[2]
            providers = dict(self.cfg.get("providers", {}))
            if name not in providers:
                console.print(f"[red]Provider '{name}' not found.[/]")
                return True
            del providers[name]
            active = self.cfg.get("active_provider")
            if active == name:
                self.cfg_mgr.update("active_provider", None)
            self.cfg_mgr.update("providers", providers)
            self.cfg = self.cfg_mgr.load()
            console.print(f"[yellow]Provider [bold]{name}[/] removed.[/]")
            return True

        else:
            console.print("[red]Unknown subcommand. Use: list | add | use | rm[/]")
            return True

    def _show_help(self):
        t = Table(title="[bold]Pollinations CLI Commands[/]", box=box.ROUNDED, border_style="cyan")
        t.add_column("Command", style="bold yellow")
        t.add_column("Description", style="dim")
        t.add_column("Usage", style="cyan")

        cmds = [
            ("/model", "Select AI model", "/model claude"),
            ("/models", "List all available models", "/models"),
            ("/api", "Set Pollinations API key", "/api sk-xxx"),
            ("/providers", "Manage custom OpenAI v1 providers", "/providers add|list|use|rm"),
            ("/google", "Toggle Google search tool", "/google on"),
            ("/reasoning", "Toggle reasoning/thinking", "/reasoning on"),
            ("/prompt", "Load custom system prompt", "/prompt ~/prompt.txt"),
            ("/config", "Show current configuration", "/config"),
            ("/reset", "Clear conversation context", "/reset"),
            ("/upgrade", "Update to latest version", "/upgrade"),
            ("/exit", "Exit Polly", "/exit"),
        ]
        for cmd, desc, usage in cmds:
            t.add_row(cmd, desc, usage)
        console.print(t)

    def run_stream(self):
        payload = create_payload(self.cfg["model"], self.history, self.cfg)
        full_content = ""
        tool_buffer = []
        md_text = ""
        api = get_api_config(self.cfg)

        with Live(
            Panel(Text("...", style="dim"), title=f"[bold]Polly[/] [dim]({self.cfg['model']} @ {api['name']})[/]", border_style="blue"),
            refresh_per_second=15
        ) as live:
            try:
                response = stream_completion(payload, self.cfg)
                for line in response.iter_lines():
                    if not line:
                        continue
                    decoded = line.decode('utf-8')
                    if not decoded.startswith('data: '):
                        continue

                    data_str = decoded.replace('data: ', '')
                    if data_str == '[DONE]':
                        break

                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0]["delta"]

                        if "content" in delta and delta["content"]:
                            txt = delta["content"]
                            full_content += txt
                            md_text += txt
                            live.update(Panel(
                                Markdown(md_text) if len(md_text) > 10 else Text(md_text),
                                title=f"[bold]Polly[/] [dim]({self.cfg['model']} @ {api['name']})[/]",
                                border_style="blue"
                            ))

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
                live.update(Panel(f"[red]{e}[/]", title="Error", border_style="red"))
                return

        if full_content or tool_buffer:
            msg = {"role": "assistant"}
            if full_content:
                msg["content"] = full_content
            else:
                msg["content"] = None

            if tool_buffer:
                msg["tool_calls"] = tool_buffer

            self.history.append(msg)

        if tool_buffer:
            for tool in tool_buffer:
                func_name = tool["function"]["name"]
                call_id = tool["id"]
                try:
                    args = json.loads(tool["function"]["arguments"])
                except Exception:
                    console.print(f"[red]Error parsing arguments for {func_name}[/]")
                    args = {}

                spinner_text = f"Running {func_name}..."
                if func_name == "write_file":
                    spinner_text = f"Writing {args.get('path', '???')}"
                elif func_name == "read_file":
                    spinner_text = f"Reading {args.get('path', '?')}"
                elif func_name == "google_search":
                    spinner_text = "Searching Google..."

                if func_name == "execute_command":
                    console.print(f"[dim]Executing: {args.get('command', '?')[:80]}[/]")
                    result = execute_local_tool(func_name, args)
                else:
                    with console.status(f"[bold white]{spinner_text}[/]", spinner="dots"):
                        result = execute_local_tool(func_name, args)
                    console.print(f"[dim]{spinner_text} [green]Done[/][/]")

                self.history.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": func_name,
                    "content": str(result)
                })

            self.run_stream()

    def start(self):
        console.clear()
        console.print(POLLY_BANNER)
        api = get_api_config(self.cfg)
        provider_str = f" @ [bold magenta]{api['name']}[/]" if api['name'] != 'pollinations' else ""
        console.print(f"[dim]Model: {self.cfg['model']}{provider_str} | Reasoning: {self.cfg['reasoning']} | Google: {self.cfg.get('google_search', False)}[/]")
        console.print(f"[dim]Type /help for commands | /exit to quit[/]\n")

        while True:
            try:
                cwd = os.path.basename(os.getcwd())
                prompt_str = f"[bold blue]{cwd}[/] [bold white]>[/] "
                u = Prompt.ask(prompt_str)
                if not u.strip():
                    continue
                if u.startswith("/"):
                    handled = self.handle_slash_command(u)
                    if handled:
                        continue
                self.history.append({"role": "user", "content": u})
                self.run_stream()
            except KeyboardInterrupt:
                console.print("\n[dim]Exit with /exit or Ctrl+D[/]")
            except EOFError:
                console.print("\n[dim]Goodbye![/]")
                break
