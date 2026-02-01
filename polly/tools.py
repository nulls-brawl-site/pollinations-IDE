# polly/tools.py
import os
import subprocess
from .models import supports_search

def get_tools_schema(model_id):
    """Возвращает список инструментов, доступных для конкретной модели"""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files in directory (ls -la equivalent)",
                "parameters": {"type": "object", "properties": {"path": {"type": "string", "default": "."}}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read file content. ALWAYS use this before editing code.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Create or Overwrite file with content.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_command",
                "description": "Execute shell command. Use carefully.",
                "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}
            }
        }
    ]

    # Добавляем поиск ТОЛЬКО если модель в белом списке
    if supports_search(model_id):
        tools.append({"type": "google_search"})
    
    return tools

def execute_local_tool(name, args):
    try:
        if name == "list_files":
            path = args.get("path", ".")
            if not os.path.exists(path): return "Error: Path not found."
            items = os.listdir(path)
            result = []
            for item in items[:50]:
                full = os.path.join(path, item)
                prefix = "📁" if os.path.isdir(full) else "📄"
                result.append(f"{prefix} {item}")
            return "\n".join(result)
        
        elif name == "read_file":
            path = args["path"]
            if not os.path.exists(path): return "Error: File not found."
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif name == "write_file":
            with open(args["path"], 'w', encoding='utf-8') as f:
                f.write(args["content"])
            return f"Success: File '{args['path']}' written."
        
        elif name == "execute_command":
            cmd = args["command"]
            forbidden = ["rm -rf /", ":(){ :|:& };:"] 
            if any(f in cmd for f in forbidden):
                return "Error: Command blocked by safety policy."
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = (result.stdout + result.stderr).strip()
            return output if output else "Command executed (no output)."

    except Exception as e:
        return f"Tool Execution Error: {str(e)}"
    return "Unknown tool"
