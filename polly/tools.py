import os
import shutil
import subprocess
import time
import threading
import signal
from rich.prompt import Prompt
from rich.console import Console
from .models import supports_search

console = Console()

# Глобальное хранилище запущенных фоновых процессов
# Format: {pid: subprocess.Popen}
ACTIVE_PROCESSES = {}

def get_tools_schema(config):
    tools = [
        # --- ФАЙЛОВАЯ СИСТЕМА ---
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List all files in directory. No limits.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string", "default": "."}}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read FULL content of a file. No truncation.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Create/Overwrite file.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delete_item",
                "description": "Delete file/folder.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_folder",
                "description": "Mkdir -p",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "move_item",
                "description": "Move/Rename",
                "parameters": {"type": "object", "properties": {"src": {"type": "string"}, "dest": {"type": "string"}}, "required": ["src", "dest"]}
            }
        },
        
        # --- EXECUTE / ENV ---
        {
            "type": "function",
            "function": {
                "name": "execute_command",
                "description": "Run shell command. Use 'background=True' for servers/tunnels/long scripts.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "command": {"type": "string", "description": "Command to run"},
                        "background": {"type": "boolean", "description": "Set True for servers/daemons. Default False."}
                    }, 
                    "required": ["command"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "secrets_env",
                "description": "Request secrets securely.",
                "parameters": {
                    "type": "object", 
                    "properties": {"keys": {"type": "array", "items": {"type": "string"}}}, 
                    "required": ["keys"]
                }
            }
        }
    ]

    if config.get("google_search", True):
        tools.append({"type": "google_search"})
    
    return tools

def stream_process_output(process, capture_buffer):
    """Читает вывод процесса в реальном времени и пишет в консоль"""
    try:
        # Читаем stdout посимвольно/построчно
        for line in iter(process.stdout.readline, ''):
            if not line: break
            print(line, end='') # Вывод прямо в терминал пользователя
            capture_buffer.append(line)
    except:
        pass

def execute_local_tool(name, args):
    try:
        if name == "list_files":
            path = args.get("path", ".")
            if not os.path.exists(path): return f"Error: Path '{path}' not found."
            items = os.listdir(path)
            items.sort()
            res = []
            for item in items: # УБРАН ЛИМИТ [:100]
                full = os.path.join(path, item)
                mark = "📁" if os.path.isdir(full) else "📄"
                res.append(f"{mark} {item}")
            return f"Dir: {os.path.abspath(path)}\n" + "\n".join(res)
        
        elif name == "read_file":
            with open(args["path"], 'r', encoding='utf-8') as f:
                return f.read() # УБРАН ЛИМИТ на чтение
        
        elif name == "write_file":
            p = args["path"]
            os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
            with open(p, 'w', encoding='utf-8') as f:
                f.write(args["content"])
            return f"Success: Wrote {len(args['content'])} chars to {p}"
        
        elif name == "delete_item":
            p = args["path"]
            if os.path.isdir(p): shutil.rmtree(p)
            else: os.remove(p)
            return f"Deleted {p}"

        elif name == "create_folder":
            os.makedirs(args["path"], exist_ok=True)
            return f"Created {args['path']}"

        elif name == "move_item":
            shutil.move(args["src"], args["dest"])
            return f"Moved {args['src']} to {args['dest']}"

        # --- EXECUTE COMMAND (THE BEAST) ---
        elif name == "execute_command":
            cmd = args["command"]
            is_bg = args.get("background", False)
            
            # Change Dir Support
            if cmd.startswith("cd "):
                try:
                    os.chdir(cmd[3:].strip())
                    return f"CWD changed to {os.getcwd()}"
                except Exception as e:
                    return f"Error: {e}"

            console.print(f"[bold dim]>> Executing: {cmd}[/]")
            if is_bg:
                console.print(f"[yellow]>> Starting in BACKGROUND mode (Monitoring for 10s)...[/]")

            # Запускаем процесс
            try:
                # Используем Popen для контроля
                process = subprocess.Popen(
                    cmd, 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True, 
                    bufsize=1,
                    preexec_fn=os.setsid # Создаем группу процессов (чтобы убивать все дерево)
                )
            except Exception as e:
                return f"Failed to start: {e}"

            # Буфер для логов
            output_buffer = []
            
            # Если это фоновый процесс (сервер)
            if is_bg:
                ACTIVE_PROCESSES[process.pid] = process
                
                # Запускаем поток чтения логов (чтобы не блокировать, но видеть начало)
                # Читаем логи 10 секунд
                start_time = time.time()
                while time.time() - start_time < 10:
                    line = process.stdout.readline()
                    if not line: 
                        if process.poll() is not None: break # Умер
                        continue
                    print(f"[BG] {line}", end='')
                    output_buffer.append(line)
                
                # Проверка статуса
                if process.poll() is None:
                    return f"SUCCESS: Process started (PID {process.pid}) and is running.\nLogs so far:\n{''.join(output_buffer)}\n[Polly]: I will keep this running."
                else:
                    return f"ERROR: Process started but crashed immediately (Code {process.returncode}).\nLogs:\n{''.join(output_buffer)}"

            # Если это обычный процесс (установка, ls, скрипт)
            else:
                try:
                    # Читаем вывод в реальном времени
                    for line in iter(process.stdout.readline, ''):
                        print(line, end='')
                        output_buffer.append(line)
                    
                    process.wait() # Ждем завершения
                    return "".join(output_buffer)
                
                except KeyboardInterrupt:
                    # ОБРАБОТКА CTRL+C
                    console.print("\n[bold red]>> User interrupted command (SIGINT)[/]")
                    # Убиваем группу процессов
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    return f"Command interrupted by user.\nPartial Output:\n{''.join(output_buffer)}"

        elif name == "secrets_env":
            keys = args.get("keys", [])
            console.print(f"\n[bold yellow]🔒 SECRETS REQUEST:[/]")
            env_map = {}
            if os.path.exists(".env"):
                with open(".env", "r") as f:
                    for line in f:
                        if "=" in line:
                            p = line.strip().split("=", 1)
                            env_map[p[0]] = p[1]
            for key in keys:
                if key not in env_map:
                    val = Prompt.ask(f"Enter {key}", password=True)
                    env_map[key] = val
            with open(".env", "w") as f:
                for k, v in env_map.items():
                    f.write(f"{k}={v}\n")
            return "Secrets saved to .env"

    except Exception as e:
        return f"System Error: {str(e)}"
    
    return "Unknown tool"
