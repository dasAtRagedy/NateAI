import json
from typing import List, Dict
from pathlib import Path
import os

class StorageManager:
    """Handles file operations and storage"""

    def __init__(self, base_folder: Path, model: str):
        self.base_folder = base_folder
        self.model = model
        self._ensure_base_folder()

    def save_conversation(self, conversation_hash: str, messages: List[Dict[str, str]]):
        """Saves conversation data to storage"""
        conversation_path = self._get_conversation_path(conversation_hash)
        conversation_path.mkdir(parents=True, exist_ok=True)
        
        with open(conversation_path / 'data.json', "w+", encoding="utf-8") as f:
            json.dump(messages, f, indent=4)

        self._save_markdown(conversation_path / 'conversation.md', messages)
        self._update_last_conversation(conversation_hash)

    def load_conversation(self, conversation_hash: str) -> List[Dict[str, str]]:
        """Loads conversation data from storage"""
        conversation_path = self._get_conversation_path(conversation_hash)
        data_file = conversation_path / 'data.json'
        
        if not data_file.exists():
            raise FileNotFoundError(f"No conversation found with hash: {conversation_hash}")
        try:
            with open(data_file) as f:
                return json.load(f)
        except (json.JSONDecodeError) as e:
            print(f"Could not open data file of conversation with specified hash: {conversation_hash}")
            print(e)
            quit()

    def get_last_conversation_hash(self) -> str:
        """Retrieves hash of the previous conversation"""
        try:
            with open(self.base_folder / 'info.json') as f:
                return json.load(f).get('last_hash')
        except (json.JSONDecodeError, KeyError) as e:
            print('Could not continue last conversation, error while reading history file')
            print(e)
            quit()

    def conversation_exists(self, conversation_hash: str) -> bool:
        """Checks if conversation exists"""
        return self._get_conversation_path(conversation_hash).exists()

    def _get_conversation_path(self, conversation_hash: str) -> Path:
        """Constructs path for a conversation with a specific hash"""
        return self.base_folder / self.model / 'conversations' / conversation_hash
    
    def _ensure_base_folder(self):
        """Ensures base storage folder exists"""
        self.base_folder.mkdir(parents=True, exist_ok=True)

    def _save_markdown(self, path: Path, messages: List[Dict[str, str]]):
        """Saves conversation in Markdown format"""
        markdown = ""
        for msg in messages:
            markdown += f"**{msg["role"].title()}**:\n{msg["content"]}\n"
            if msg["role"] == "assistant":
                markdown += "\n"
        
        with open(path, "w+") as f:
            f.write(markdown)

    def _update_last_conversation(self, conversation_hash: str):
        """Updates info file with latest conversation hash"""
        with open(os.path.join(self.base_folder, "info.json"), "w") as f:
            json.dump({"last_hash": conversation_hash}, f, indent=4)
