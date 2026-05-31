import json
from pathlib import Path

APP_NAME = "pollinations"
CONFIG_DIR = Path.home() / f".{APP_NAME}"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_SYSTEM_PROMPT = """
You are Polly, an elite AI CLI Assistant powered by Pollinations.ai.
- You have full access to the local file system and terminal.
- Use `write_file` to create code, do NOT just print it.
- Use `execute_command` to run shell commands, install packages, start servers.
- If the user asks for information, use your knowledge or available tools.
- Be concise, professional, and accurate.
- Always add .env file if API keys are needed, and ask user using `secrets_env`.
- For background processes (servers, tunnels), pass `background: true`.
"""

class ConfigManager:
    defaults = {
        "api_key": None,
        "model": "claude",
        "reasoning": False,
        "google_search": False,
        "custom_prompt_path": None,
        "providers": {},
        "active_provider": None,
    }

    def __init__(self):
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True)
        if not CONFIG_FILE.exists():
            self.save(self.defaults)

    def load(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
            merged = {**self.defaults, **data}
            if "providers" not in data:
                merged["providers"] = {}
            if "active_provider" not in data:
                merged["active_provider"] = None
            if "google_search" not in data:
                merged["google_search"] = False
            return merged
        except:
            return dict(self.defaults)

    def save(self, data):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def update(self, key, value):
        data = self.load()
        data[key] = value
        self.save(data)

    def get_api_config(self):
        data = self.load()
        active = data.get("active_provider")
        providers = data.get("providers", {})

        if active and active in providers:
            p = providers[active]
            return {
                "url": p.get("url", ""),
                "key": p.get("key", data.get("api_key")),
                "name": active,
            }
        return {
            "url": "gen.pollinations.ai",
            "key": data.get("api_key"),
            "name": "pollinations",
        }

    def get_system_prompt(self):
        data = self.load()
        if data.get("custom_prompt_path"):
            path = Path(data["custom_prompt_path"])
            if path.exists():
                return path.read_text(encoding="utf-8")
        return DEFAULT_SYSTEM_PROMPT
