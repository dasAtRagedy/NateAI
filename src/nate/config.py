import configparser
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Dict

@dataclass
class Config:
    """Config data struct"""
    model: str
    system_prompt: str
    conversation_folder: Path
    message: str
    continue_conversation: bool
    use_system_prompt: bool

class ConfigManager:
    """Handles reading and managing configs"""

    def __init__(self, config_path: Path, args: Dict):
        self.config = self._load_config(config_path)
        self.args = self._parse_args(args)

    def get_config(self) -> Config:
        """Returns Config struct with all settings"""
        if str(self.config['ConversationFolder']).startswith('~'):
            conversation_folder = Path.home() / self.config['ConversationFolder'][1:]
        else:
            conversation_folder = Path(self.config['ConversationFolder'])

        return Config(
            model = self.config['Model'],
            system_prompt = self.config.get('SystemPrompt', ''),
            conversation_folder = conversation_folder,
            message = ' '.join(self.args['message']),
            continue_conversation = self.args['continue'],
            use_system_prompt = not self.args['no-sys']
        )

    def _parse_args(self, args) -> dict:
        if "message" not in args:
            raise ValueError("Message was not provided")
        return args

    def _load_config(self, config_path: Path) -> dict:
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        config = configparser.ConfigParser()
        config.read(config_path)

        if "DEFAULT" not in config:
            raise KeyError("Config file must contain a [DEFAULT] section")

        required_keys = ["Model", "SystemPrompt", "ConversationFolder"]
        missing_keys = [key for key in required_keys if key not in config['DEFAULT']]
        if missing_keys:
            raise KeyError(f"Missing required config keys: {', '.join(missing_keys)}")
        return config["DEFAULT"]
