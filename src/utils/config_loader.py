import json
from pathlib import Path

class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_config(self) -> dict:
        return self.config