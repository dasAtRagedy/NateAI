import hashlib
import json
from typing import Dict, List

class ConversationManager:
    """Handles conversation state, storage and retrieval"""

    def __init__(self, config, storage):
        self.config = config
        self.messages = []
        self.conversation_hash = None
        self.storage = storage
        self._initialize_conversation()

    def _initialize_conversation(self):
        """Sets up conversation"""
        if self.config.continue_conversation:
            self.load_latest_conversation()
        if self.config.use_system_prompt:
            self.append_message({
                'role': 'system',
                'content': self.config.system_prompt
            })
        self.append_message({
            "role": "user",
            "content": self.config.message
        })
        self._generate_hash()

    def save_conversation(self):
        """Saves current conversation"""
        self.storage.save_conversation(self.conversation_hash, self.messages)
    
    def load_conversation(self, conversation_hash: str):
        """Loads conversation from a given hash"""
        self.messages = self.storage.load_conversation(conversation_hash)
        self.conversation_hash = conversation_hash

    def load_latest_conversation(self):
        """Loads latest conversation"""
        self.load_conversation(self.storage.get_last_conversation_hash())
    
    def _generate_hash(self):
        """Generates SHA1 hash of messages until (not including) first completion"""
        if not self.messages:
            raise ValueError("No user prompt or system prompt was provided")
        hash_input = ""
        for i, message in enumerate(self.messages):
            if i >= 2 or message["role"] == "assistant": break    
            hash_input += message["role"] + message["content"]
        self.conversation_hash = hashlib.sha1(hash_input.lower().encode()).hexdigest()
    
    def set_hash(self, hash):
        self.conversation_hash = hash
    
    def append_message(self, message: Dict[str, str]):
        """{"role": "system|user|assistant", "content": "message", <optionally more info for storage>}"""
        self.messages.append(message)
    
    def append_messages(self, messages: List[Dict[str, str]]):
        for message in messages:
            self.append_message(message)
    
    def conversation_to_json(conversation):
        return json.dumps(conversation, indent=4)
