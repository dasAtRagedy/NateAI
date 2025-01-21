"""NateAI

Usage: nate [options] [--] <message> ...

--continue  Continue the last conversation
--no-sys    Do not use system argument

"""
import os
from openai import OpenAI
import configparser
# from rich.console import Console
# from rich.markdown import Markdown
from docopt import docopt
from pathlib import Path
import hashlib
import json
from typing import Dict, List
from dataclasses import dataclass
from typing import Protocol

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

    def __init__(self, config_name):
        absolute_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(absolute_dir, config_name)

        self.config = self._load_config(config_path)
        self.args = self._parse_args()

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
            message = ' '.join(self.args['<message>']),
            continue_conversation = self.args['--continue'],
            use_system_prompt = not self.args['--no-sys']
        )

    def _parse_args(self) -> dict:
        args = docopt(__doc__)
        if "<message>" not in args:
            raise ValueError("Message was not provided")
        return args

    def _load_config(self, config_path: str) -> dict:
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
        if not self._try_load_cache():
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
        client = OpenAIClient(OpenAI())
        config = ConfigManager("config.ini").get_config()
        conversation_manager = ConversationManager(config)
        
        nate = NateAI(
            config,
            conversation_manager,
            client
        )
        nate.run()
    except Exception as e:
        print(f'Error: {e}')
        return 1
    return 0

if __name__ == "__main__":
    main()
