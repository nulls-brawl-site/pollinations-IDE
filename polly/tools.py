import os
import shutil
import subprocess
from rich.prompt import Prompt
from rich.console import Console

console = Console()

def get_tools_schema(config):
    """
    Возвращает схему инструментов.
    Включает Google Search только если он активирован в настройках пользователя.
    """
    tools = [
        # --- ФАЙЛОВАЯ СИСТЕМА ---
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files and folders in a directory. Use path='.' for current directory.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "path": {"type": "string", "description": "Directory path", "default": "."}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the content of a file.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "path": {"type": "string", "description": "File path"}
                    }, 
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Create a new file or overwrite an existing one with content.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "Full file content"}
                    }, 
                    "required": ["path", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delete_item",
                "description": "Delete a file or directory permanently.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "path": {"type": "string", "description": "Path to item"}
                    }, 
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_folder",
                "description": "Create a new directory (and parent directories if needed).",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"}
                    }, 
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "move_item",
                "description": "Move or rename a file/directory.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "src": {"type": "string", "description": "Source path"},
                        "dest": {"type": "string", "description": "Destination path"}
                    }, 
                    "required": ["src", "dest"]
                }
            }
        },
        
        # --- ТЕРМИНАЛ И ОКРУЖЕНИЕ ---
        {
            "type": "function",
            "function": {
                "name": "execute_command",
                "description": "Execute a shell command (e.g., pip install, git status). Use with caution.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to run"}
                    }, 
                    "required": ["command"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "secrets_env",
                "description": "Securely request API keys or secrets from the user and append them to .env file.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "keys": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "List of variable names (e.g., ['OPENAI_API_KEY', 'DB_PASSWORD'])"
                        }
                    }, 
                    "required": ["keys"]
                }
            }
        }
    ]

    # Добавляем Google Search, если он включен в конфиге пользователя
    # По умолчанию True, если ключа нет
    if config.get("google_search", True):
        tools.append({"type": "google_search"})
    
    return tools

def execute_local_tool(name, args):
    """Исполняет инструменты локально на машине пользователя"""
    try:
        # --- LIST FILES ---
        if name == "list_files":
            path = args.get("path", ".")
            if not os.path.exists(path):
                return f"Error: Path '{path}' does not exist."
            
            items = os.listdir(path)
            items.sort() # Сортировка для удобства
            
            res = []
            for item in items[:100]: # Ограничение вывода
                full_path = os.path.join(path, item)
                prefix = "📁" if os.path.isdir(full_path) else "📄"
                res.append(f"{prefix} {item}")
            
            output = "\n".join(res)
            return f"Directory: {os.path.abspath(path)}\n{output}"
        
        # --- READ FILE ---
        elif name == "read_file":
            path = args["path"]
            if not os.path.exists(path):
                return f"Error: File '{path}' not found."
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # --- WRITE FILE ---
        elif name == "write_file":
            path = args["path"]
            # Создаем папки, если путь содержит несуществующие директории
            directory = os.path.dirname(os.path.abspath(path))
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                
            with open(path, 'w', encoding='utf-8') as f:
                f.write(args["content"])
            return f"Success: File '{path}' written successfully."
        
        # --- DELETE ITEM ---
        elif name == "delete_item":
            path = args["path"]
            if not os.path.exists(path):
                return f"Error: Item '{path}' not found."
            
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return f"Success: Deleted '{path}'."

        # --- CREATE FOLDER ---
        elif name == "create_folder":
            path = args["path"]
            os.makedirs(path, exist_ok=True)
            return f"Success: Created directory '{path}'."

        # --- MOVE ITEM ---
        elif name == "move_item":
            src = args["src"]
            dest = args["dest"]
            shutil.move(src, dest)
            return f"Success: Moved '{src}' to '{dest}'."

        # --- EXECUTE COMMAND ---
        elif name == "execute_command":
            cmd = args["command"]
            
            # Обработка 'cd' (смена директории процесса)
            if cmd.startswith("cd "):
                target_dir = cmd[3:].strip()
                try:
                    os.chdir(target_dir)
                    return f"Changed working directory to: {os.getcwd()}"
                except Exception as e:
                    return f"Error changing directory: {str(e)}"
            
            # Простейшая защита от случайного удаления корня
            if "rm -rf /" in cmd and len(cmd) < 12:
                return "Error: Command blocked by safety policy."

            # Запуск команды
            # Используем shell=True, чтобы работали пайпы и перенаправления
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            output = ""
            if stdout:
                output += f"STDOUT:\n{stdout}\n"
            if stderr:
                output += f"STDERR:\n{stderr}\n"
            
            if not output:
                output = "Command executed successfully (no output)."
                
            # Обрезаем слишком длинный вывод
            return output[:5000]

        # --- SECRETS ENV ---
        elif name == "secrets_env":
            keys = args.get("keys", [])
            if not keys:
                return "Error: No keys provided."
            
            console.print(f"\n[bold yellow]🔒 POLLY REQUESTS SECRETS:[/]")
            console.print("[dim]These values will be saved to .env locally.[/]")
            
            # Читаем текущий .env чтобы не перезатирать лишнее
            env_map = {}
            if os.path.exists(".env"):
                with open(".env", "r") as f:
                    for line in f:
                        if "=" in line:
                            parts = line.strip().split("=", 1)
                            env_map[parts[0]] = parts[1]

            new_entries = []
            for key in keys:
                if key in env_map:
                    console.print(f"Key [cyan]{key}[/] already exists in .env. Skipping.")
                else:
                    # Ввод пароля скрыт
                    val = Prompt.ask(f"Enter value for [cyan]{key}[/]", password=True)
                    env_map[key] = val
                    new_entries.append(key)
            
            # Записываем обратно
            with open(".env", "w") as f:
                for k, v in env_map.items():
                    f.write(f"{k}={v}\n")
            
            if not new_entries:
                return "No new secrets added (.env already contained them)."
            return f"Success: Added {', '.join(new_entries)} to .env file."

    except Exception as e:
        return f"System Error executing {name}: {str(e)}"
    
    return f"Error: Tool '{name}' is not implemented locally."
