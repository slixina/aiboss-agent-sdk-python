import json
import os
from pathlib import Path
from typing import Optional, Dict, List

CONFIG_DIR = Path.home() / ".aiboss"
CONFIG_FILE = CONFIG_DIR / "config.json"

class Config:
    def __init__(self):
        self._config: Dict = {}
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    self._config = json.load(f)
            except json.JSONDecodeError:
                self._config = {}
        else:
            self._config = {}

    def save(self):
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self._config, f, indent=2)

    @property
    def api_url(self) -> str:
        return self._config.get("api_url", "http://localhost:3000")

    @api_url.setter
    def api_url(self, value: str):
        self._config["api_url"] = value
        self.save()

    @property
    def agent_id(self) -> Optional[str]:
        return self._config.get("agent_id")

    @agent_id.setter
    def agent_id(self, value: str):
        self._config["agent_id"] = value
        self.save()

    @property
    def agent_secret(self) -> Optional[str]:
        return self._config.get("agent_secret")

    @agent_secret.setter
    def agent_secret(self, value: str):
        self._config["agent_secret"] = value
        self.save()

    @property
    def allowed_domains(self) -> List[str]:
        # Default to "*" (allow all) to simplify setup
        return self._config.get("allowed_domains", ["*"])

    @allowed_domains.setter
    def allowed_domains(self, value: List[str]):
        self._config["allowed_domains"] = value
        self.save()

# Global instance
_config_instance = Config()

def get_config() -> Config:
    return _config_instance

# Backward compatibility functions
def get_api_url() -> str:
    return _config_instance.api_url

def get_agent_id() -> Optional[str]:
    return _config_instance.agent_id

def get_agent_secret() -> Optional[str]:
    return _config_instance.agent_secret

def get_allowed_domains() -> List[str]:
    return _config_instance.allowed_domains

def save_config(api_url: str, agent_id: str, agent_secret: Optional[str] = None, allowed_domains: List[str] = None):
    _config_instance.api_url = api_url
    _config_instance.agent_id = agent_id
    if agent_secret:
        _config_instance.agent_secret = agent_secret
    if allowed_domains:
        _config_instance.allowed_domains = allowed_domains
