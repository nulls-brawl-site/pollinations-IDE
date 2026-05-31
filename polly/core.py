import json
import os
import shlex
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live
from rich.text import Text

from .config import ConfigManager
from .api import create_payload, stream_completion, get_api_config
from .tools import execute_local_tool
from .utils import upgrade_polly
from .models import list_models_table
from . import tui

console = Console()

class PollyIDE:
    def __init__(self):
        self.cfg_mgr = ConfigManager()
        self.cfg = self.cfg_mgr.load()
        self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]

    def _reload_config(self):
        self.cfg = self.cfg_mgr.load()

    def handle_slash_command(self, cmd_line):
        try:
            parts = shlex.split(cmd_line)
        except ValueError:
            parts = cmd_line.split()

        base = parts[0].lower()

        if base == "/reset":
            self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]
            tui.success("Context cleared")
            return True

        elif base == "/upgrade" or base == "/update":
            upgrade_polly()
            return True

        elif base == "/models":
            self._interactive_models()
            return True

        elif base == "/config":
            self._show_config()
            return True

        elif base == "/providers":
            self._interactive_providers()
            return True

        elif base == "/prompt":
            if len(parts) < 2:
                tui.error("Usage: /prompt /path/to/custom_prompt.txt")
                return True
            path = parts[1]
            if os.path.exists(path):
                self.cfg_mgr.update("custom_prompt_path", os.path.abspath(path))
                self.history = [{"role": "system", "content": self.cfg_mgr.get_system_prompt()}]
                tui.success(f"System prompt loaded from {path}. Memory reset.")
            else:
                tui.error(f"File not found: {path}")
            return True

        elif base == "/google":
            if len(parts) < 2:
                console.print(f"[dim]Google Search: {self.cfg.get('google_search', False)}[/]")
                return True
            val = parts[1].lower() in ("on", "true", "1", "yes")
            self.cfg_mgr.update("google_search", val)
            self._reload_config()
            tui.success(f"Google Search: {val}")
            return True

        elif base == "/reasoning":
            if len(parts) < 2:
                console.print(f"[dim]Reasoning: {self.cfg.get('reasoning', False)}[/]")
                return True
            val = parts[1].lower() in ("on", "true", "1", "yes")
            self.cfg_mgr.update("reasoning", val)
            self._reload_config()
            tui.success(f"Reasoning: {val}")
            return True

        elif base == "/api":
            if len(parts) < 2:
                masked = self.cfg.get("api_key", "") or ""
                if masked:
                    masked = masked[:8] + "..." + masked[-4:] if len(masked) > 12 else "***"
                console.print(f"[dim]API Key: {masked or 'not set'}[/]")
                return True
            self.cfg_mgr.update("api_key", parts[1])
            self._reload_config()
            tui.success("API Key saved")
            return True

        elif base == "/model":
            if len(parts) < 2:
                console.print(f"[dim]Model: {self.cfg.get('model', 'claude')}[/]")
                return True
            self.cfg_mgr.update("model", parts[1])
            self._reload_config()
            tui.success(f"Model: {parts[1]}")
            return True

        elif base == "/help":
            self._show_help()
            return True

        elif base == "/exit" or base == "/quit":
            console.print("[dim]Goodbye![/]")
            exit(0)

        return False

    def _interactive_providers(self):
        while True:
            self._reload_config()
            providers = self.cfg.get("providers", {})
            active = self.cfg.get("active_provider")
            has_key = bool(self.cfg.get("api_key"))

            choice = tui.provider_dashboard(providers, active, has_key)

            if choice == "Add Provider":
                name, url, key = tui.add_provider_wizard()
                if name and url:
                    providers = dict(self.cfg.get("providers", {}))
                    providers[name] = {"url": url, "key": key}
                    self.cfg_mgr.update("providers", providers)

            elif choice == "Switch Provider":
                sel = tui.switch_provider_dialog(providers, active, has_key)
                if sel:
                    if sel == "pollinations":
                        self.cfg_mgr.update("active_provider", None)
                        tui.success("Switched to Pollinations API")
                    else:
                        self.cfg_mgr.update("active_provider", sel)
                        tui.success(f"Switched to {sel}")
                    tui.confirm("Press Enter to continue", default=True)

            elif choice == "Remove Provider":
                name = tui.remove_provider_dialog(providers)
                if name:
                    providers = dict(self.cfg.get("providers", {}))
                    del providers[name]
                    if active == name:
                        self.cfg_mgr.update("active_provider", None)
                    self.cfg_mgr.update("providers", providers)
                    tui.success(f"Removed {name}")

            elif choice == "Default (Pollinations)":
                if tui.confirm("Switch to default Pollinations API?", default=True):
                    self.cfg_mgr.update("active_provider", None)
                    tui.success("Switched to Pollinations API")

            elif choice == "Back":
                break

    def _interactive_models(self):
        self._reload_config()
        current = self.cfg.get("model", "claude")
        new_model = tui.model_selector(current, self.cfg)
        if new_model and new_model != current:
            self.cfg_mgr.update("model", new_model)
            self._reload_config()
            tui.success(f"Model set to: [bold cyan]{new_model}[/]")

    def _show_config(self):
        tui.clear()
        tui.console.print(tui.WELCOME_ART)
        tui.console.print("[bold #eab308]  Configuration[/]\n")
        safe = {k: v for k, v in self.cfg.items() if k not in ("providers",)}
        safe["providers_count"] = len(self.cfg.get("providers", {}))
        safe["active_provider"] = self.cfg.get("active_provider") or "pollinations"
        console.print(Panel(json.dumps(safe, indent=2), title="[bold]Config[/]", border_style="cyan"))
        tui.Prompt.ask("[dim]Press Enter to continue[/]", default="")

    def _show_help(self):
        tui.clear()
        tui.console.print(tui.WELCOME_ART)
        tui.console.print("[bold #eab308]  Commands[/]\n")

        cmds = [
            ("/model <id>", "Select AI model"),
            ("/models", "Interactive model selector"),
            ("/api <key>", "Set Pollinations API key"),
            ("/providers", "Manage custom API providers"),
            ("/google on|off", "Toggle Google search tool"),
            ("/reasoning on|off", "Toggle reasoning/thinking"),
            ("/prompt <path>", "Load custom system prompt"),
            ("/config", "Show configuration"),
            ("/reset", "Clear conversation context"),
            ("/upgrade", "Update to latest version"),
            ("/help", "Show this help"),
            ("/exit", "Exit"),
        ]

        from rich.table import Table
        from rich import box
        table = Table(box=box.SIMPLE, border_style="dim cyan")
        table.add_column("Command", style="bold yellow")
        table.add_column("Description", style="dim")
        for cmd, desc in cmds:
            table.add_row(cmd, desc)
        console.print(table)
        tui.Prompt.ask("[dim]Press Enter to continue[/]", default="")

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
        tui.clear()
        tui.console.print(tui.WELCOME_ART)

        api = self.cfg_mgr.get_api_config()
        provider_str = f" [bold magenta]@{api['name']}[/]" if api['name'] != 'pollinations' else ""
        tui.console.print(
            f"[dim]Model: {self.cfg['model']}{provider_str}  "
            f"Reasoning: {'[green]ON[/]' if self.cfg['reasoning'] else 'OFF'}  "
            f"Google: {'[green]ON[/]' if self.cfg.get('google_search') else 'OFF'}[/]"
        )
        tui.console.print("[dim]Type your request, /help for commands, /exit to quit[/]\n")

        while True:
            try:
                cwd = os.path.basename(os.getcwd())
                prompt_str = f"[bold blue]{cwd}[/] [bold #eab308]>[/] "
                u = Prompt.ask(prompt_str)
                if not u.strip():
                    continue
                if u.startswith("/"):
                    handled = self.handle_slash_command(u)
                    if handled:
                        continue
                self.history.append({"role": "user", "content": u})
                tui.console.print()
                self.run_stream()
            except KeyboardInterrupt:
                tui.console.print("\n[dim]Press Ctrl+C again or type /exit[/]")
            except EOFError:
                tui.console.print("\n[dim]Goodbye![/]")
                break
