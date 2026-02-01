import os
import shutil
import subprocess
from rich.prompt import Prompt
from rich.console import Console
from .models import supports_search

console = Console()

def get_tools_schema(model_id):
    tools = [
        # --- File System ---
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files in directory (ls -la style). Use path='.' for current.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string", "default": "."}}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read file content.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Create or Overwrite file. Returns success message.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delete_item",
                "description": "Delete a file or folder (rm -rf). BE CAREFUL.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_folder",
                "description": "Create a new directory (mkdir -p).",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "move_item",
                "description": "Move or rename a file/folder.",
                "parameters": {"type": "object", "properties": {"src": {"type": "string"}, "dest": {"type": "string"}}, "required": ["src", "dest"]}
            }
        },
        
        # --- Terminal / Env ---
        {
            "type": "function",
            "function": {
                "name": "execute_command",
                "description": "Execute shell command. Use for pip install, git, running scripts.",
                "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "secrets_env",
                "description": "Securely request API keys from user and save to .env file.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "keys": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "List of env var names (e.g. ['BOT_TOKEN', 'DB_PASS'])"
                        }
                    }, 
                    "required": ["keys"]
                }
            }
        }
    ]

    if supports_search(model_id):
        tools.append({"type": "google_search"})
    
    return tools

def execute_local_tool(name, args):
    try:
        # --- Файловая система ---
        if name == "list_files":
            path = args.get("path", ".")
            if not os.path.exists(path): return f"Error: Path '{path}' not found."
            items = os.listdir(path)
            res = []
            for item in items[:100]: # Limit output
                full = os.path.join(path, item)
                mark = "📁" if os.path.isdir(full) else "📄"
                res.append(f"{mark} {item}")
            return f"Current Dir: {os.getcwd()}\nContents of {path}:\n" + "\n".join(res)
        
        elif name == "read_file":
            with open(args["path"], 'r', encoding='utf-8') as f:
                return f.read()
        
        elif name == "write_file":
            # Auto create dirs if needed
            os.makedirs(os.path.dirname(os.path.abspath(args["path"])), exist_ok=True)
            with open(args["path"], 'w', encoding='utf-8') as f:
                f.write(args["content"])
            return f"Success: Wrote to {args['path']}"
        
        elif name == "delete_item":
            path = args["path"]
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return f"Deleted {path}"

        elif name == "create_folder":
            os.makedirs(args["path"], exist_ok=True)
            return f"Created folder {args['path']}"

        elif name == "move_item":
            shutil.move(args["src"], args["dest"])
            return f"Moved {args['src']} to {args['dest']}"

        # --- Терминал ---
        elif name == "execute_command":
            cmd = args["command"]
            # Разрешаем cd
            if cmd.startswith("cd "):
                new_dir = cmd[3:].strip()
                os.chdir(new_dir)
                return f"Changed directory to {os.getcwd()}"
            
            # Блокируем совсем дичь, но разрешаем pip/git/rm
            if "rm -rf /" in cmd: return "Error: Safety block."

            # Запускаем
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            out = (res.stdout + res.stderr).strip()
            if not out: return "Command executed (no output)."
            return out[:4000] # Truncate long logs

        # --- Секреты ---
        elif name == "secrets_env":
            keys = args.get("keys", [])
            env_content = ""
            
            console.print(f"\n[bold yellow]🔒 AI requests secrets for .env file:[/]")
            
            # Читаем существующий env
            existing = {}
            if os.path.exists(".env"):
                with open(".env", "r") as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            existing[k] = v

            for key in keys:
                if key in existing:
                    val = existing[key]
                    console.print(f"Key [cyan]{key}[/] exists. Keeping old value.")
                else:
                    # Запрашиваем безопасно
                    val = Prompt.ask(f"Enter value for [cyan]{key}[/]", password=True)
                
                env_content += f"{key}={val}\n"
            
            with open(".env", "w") as f:
                f.write(env_content)
            
            return "Success: .env file updated with provided secrets."

    except Exception as e:
        return f"System Error: {str(e)}"
    return "Unknown tool"
