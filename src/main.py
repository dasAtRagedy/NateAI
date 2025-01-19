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

client = OpenAI()

@dataclass
class Config:
    """Config data struct"""
    model: str
    system_prompt: str
    conversation_folder: str
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
        conversation_folder = Path(self.config['ConversationFolder'])
        if str(conversation_folder).startswith('~'):
            conversation_folder = os.path.join(Path.home(), self.config['ConversationFolder'][1:])
        
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
            raise KeyError("Config file must containt a [DEFAULT] section")

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
    
    def generate_hash(self):
        if not self.messages:
            # FIXME: raise appropriate exception
            raise Exception("No user prompt or system prompt was provided")
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
    
    def retrieve_conversation(self, conversation_hash = None, model = None):
        if conversation_hash == None: conversation_hash = self.conversation_hash
        if model == None: model = self.config.model
        conversation_path = f"{self.config.conversation_folder}/{model}/conversations/{conversation_hash}/"
        try:
            with open(os.path.join(conversation_path, "data.json"), "r") as f:
                self.messages = json.load(f)
        except Exception as e:
            print(f"ERROR: Could not load conversation with hash {conversation_hash}")
            print(f"Exit with exception: {e}")
            quit()
        self.retrieved = True
    
    def conversation_to_markdown(self, messages = None):
        if messages == None: messages = self.messages
        conversation_contents_md = ""
        for msg in messages:
            conversation_contents_md += f"**{msg["role"].title()}**:\n{msg["content"]}\n"
            if msg["role"] == "assistant": conversation_contents_md += "\n"
        return conversation_contents_md
    
    def conversation_to_json(conversation):
        return json.dumps(conversation, indent=4)

def main():
    cfg = ConfigManager("config.ini").get_config()
    
    conversation_manager = ConversationManager(cfg)

    # we access info that we have to have access to
    #   immediately, for example latest conversation ID
    home_path = f"{cfg.conversation_folder}/"
    Path(home_path).mkdir(parents=True, exist_ok=True)
    if cfg.continue_conversation:
        with open(os.path.join(home_path, "info.json"), "r") as f:
            try:
                info = json.load(f)
            except json.decoder.JSONDecodeError:
                print("Could not continue last conversation, error reading history file")
                quit()
        # TODO: exception handling
        ## FIXME: conversation_path is created twice
        conversation_manager.set_hash(info['last_hash'])
        conversation_manager.retrieve_conversation(model=cfg.model)
        # conversation_path = f"{config['ConversationFolder']}/{config["Model"]}/conversations/{info["last_hash"]}/"
        # with open(os.path.join(conversation_path, "data.json"), "r") as f:
        #     messages = json.load(f)

    # we have added messages to message queue if we had any already
    use_cache = not conversation_manager.retrieved

    # user input
    if cfg.system_prompt and cfg.use_system_prompt:
        conversation_manager.append_message({
            "role": "system", 
            "content": cfg.system_prompt
            })

    conversation_manager.append_message({
                "role": "user",
                "content": cfg.message
            })

    # we hash only first input, mostly because we expect user to rarely repeat the exact same two inputs more than once
    # hash_input = ""
    # for message in messages:
    #     hash_input += message["role"] + message["content"]
    # conversation_hash = info["last_hash"] if args["--continue"] else hashlib.sha1(hash_input.lower().encode()).hexdigest()
    conversation_manager.generate_hash()

    conversation_path = f"{cfg.conversation_folder}/{cfg.model}/conversations/{conversation_manager.conversation_hash}/"
    # BUG: when we have a known conversation with multiple messages, we will print out the latest assistant's message, not 
    #   assistant's response to the first message. 
    if (use_cache and os.path.isdir(conversation_path)):
        print("[CACHED]:")
        with open(os.path.join(conversation_path, "data.json"), "r") as f:
            conversation_manager.retrieve_conversation(model=cfg.model)
            # messages = json.load(f)
            print(conversation_manager.messages[-1]["content"])
            print("Conversation ID: " + conversation_manager.conversation_hash)
        return

    # nate output
    completion = client.chat.completions.create(
        model = cfg.model,
        messages = conversation_manager.messages
    )
    conversation_manager.append_message({
        "role": "assistant",
        "content": completion.choices[0].message.content,
        "completion": serialize_completion(completion) # we have future logging in mind
        })

    print(conversation_manager.messages[-1]["content"])
    print("Conversation ID: " + conversation_manager.conversation_hash)

    # conversation creating in string
    conversation_contents_md = ""
    for msg in conversation_manager.messages:
        conversation_contents_md += f"**{msg["role"].title()}**:\n{msg["content"]}\n"
        if msg["role"] == "assistant": conversation_contents_md += "\n"

    # conversation saving md
    Path(conversation_path).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(conversation_path, "conversation.md"), "w+") as f:
        f.write(conversation_manager.conversation_to_markdown())

    # conversation saving json
    with open(os.path.join(conversation_path, "data.json"), "w+", encoding="utf-8") as f:
        json.dump(conversation_manager.messages, f, indent=4)

    # updating info file with latest used hash
    with open(os.path.join(home_path, "info.json"), "w") as f:
        json.dump({
            "last_hash": conversation_manager.conversation_hash
        }, f, indent=4)

# my goat https://gist.github.com/CivilEngineerUK/dbd328b72ebee77c3471670bb91fa6df
def serialize_completion(completion):
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

if __name__ == "__main__":
    main()
