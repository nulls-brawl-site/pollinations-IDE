# polly/config.py
import json
from pathlib import Path

APP_NAME = "polly"
CONFIG_DIR = Path.home() / f".{APP_NAME}"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_SYSTEM_PROMPT = """
You are Polly, an elite IDE AI Assistant.
- You have access to the local file system and terminal.
- Use `write_file` to create code, do not just print it.
- If the user asks for information and you have search capabilities, use them.
- Be concise, professional, and accurate.
"""

class ConfigManager:
    defaults = {
        "api_key": None,
        "model": "claude",
        "reasoning": False,
        "custom_prompt_path": None
    }

    def __init__(self):
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir()
        if not CONFIG_FILE.exists():
            self.save(self.defaults)

    def load(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
            return {**self.defaults, **data}
        except:
            return self.defaults

    def save(self, data):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def update(self, key, value):
        data = self.load()
        data[key] = value
        self.save(data)

    def get_system_prompt(self):
        data = self.load()
        if data.get("custom_prompt_path"):
            path = Path(data["custom_prompt_path"])
            if path.exists():
                return path.read_text(encoding="utf-8")
        return DEFAULT_SYSTEM_PROMPT
