"""NateAI

Usage: nate [options] [--] <message> ...

--continue  Continue the last conversation
--no-sys    Do not use system argument

"""
import os
from openai import OpenAI
# from rich.console import Console
# from rich.markdown import Markdown
from pathlib import Path
import hashlib
import json
from typing import Dict, List
from typing import Protocol
from docopt import docopt

from nate.config import Config, ConfigManager
from nate.storage import StorageManager

class ConversationManager:
    """Handles conversation state, storage and retrieval"""

    def __init__(self, config):
        self.config = config
        self.messages = []
        self.conversation_hash = None
        self.retrieved = False
        self.storage = StorageManager(
            base_folder = self.config.conversation_folder,
            model = self.config.model
        )
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

class AIClient(Protocol):
    """AI client interface"""

    def __init__(self, *, client):
        ...

    def generate_completion(self, model: str, messages: List[Dict[str, str]]):
        """Generate a completion with the AI model"""
        ...

class OpenAIClient(AIClient):
    """Chat client used for communication with models of OpenAI"""

    def __init__(self, client: OpenAI):
        self.client = client

    def generate_completion(self, model: str, messages: List[Dict[str, str]]):
        completion = self.client.chat.completions.create(
            model = model,
            messages = messages
        )
        return self.serialize_completion(completion)

    # my goat https://gist.github.com/CivilEngineerUK/dbd328b72ebee77c3471670bb91fa6df
    # for some reason OpenAI completions cannot be saved in json by default
    @staticmethod
    def serialize_completion(completion):
        """Returns completion in a serializable format"""
        return {
            "id": completion.id,
            "choices": [
                {
                    "finish_reason": choice.finish_reason,
                    "index": choice.index,
                    "message": {
                        "content": choice.message.content,
                        "role": choice.message.role,
                        "function_call": {
                            "arguments": json.loads(
                                choice.message.function_call.arguments) if choice.message.function_call and choice.message.function_call.arguments else None,
                            "name": choice.message.function_call.name
                        } if choice.message and choice.message.function_call else None
                    } if choice.message else None
                } for choice in completion.choices
            ],
            "created": completion.created,
            "model": completion.model,
            "object": completion.object,
            "system_fingerprint": completion.system_fingerprint,
            "usage": {
                "completion_tokens": completion.usage.completion_tokens,
                "prompt_tokens": completion.usage.prompt_tokens,
                "total_tokens": completion.usage.total_tokens
            }
        }

class NateAI():
    """Main application class"""

    def __init__(self, config: Config, conversation_manager: ConversationManager, client: AIClient):
        self.config = config
        self.conversation = conversation_manager
        self.client = client

    def run(self):
        """Main execution flow"""
        if self.config.continue_conversation or not self._try_load_cache():
            completion = self.client.generate_completion(self.config.model, self.conversation.messages)
            self.conversation.append_message({
                'role': "assistant",
                'content': completion['choices'][0]['message']['content'],
                'completion': completion
                })
            self.conversation.save_conversation()

        print(self.conversation.messages[-1]['content'])
        print(f'Conversation ID: {self.conversation.conversation_hash}')

    def _try_load_cache(self) -> bool:
        """Attempts to retrieve conversation from cache"""
        if self.conversation.storage.conversation_exists(self.conversation.conversation_hash):
            print('[CACHED]:')
            self.conversation.load_conversation(self.conversation.conversation_hash)
            return True
        return False

def main():
    try:
        args = docopt(__doc__)
        config_path = Path(os.path.dirname(os.path.dirname(__file__))) / 'config.ini'
        client = OpenAIClient(OpenAI())
        config = ConfigManager(config_path, args).get_config()
        conversation_manager = ConversationManager(config)
        
        nate = NateAI(
            config,
            conversation_manager,
            client
        )
        nate.run()
    except FileNotFoundError as e:
        print(f'Error: {e}')
        return 1
    return 0

if __name__ == "__main__":
    main()
