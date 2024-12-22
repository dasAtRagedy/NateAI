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

client = OpenAI()

class ConfigManager:
    """Handles reading and managing configs"""
    def __init__(self, config_name):
        self._parse_config_file(config_name)
        self._parse_args()

    def _parse_args(self):
        self.flags = docopt(__doc__)
        if "<message>" not in self.flags:
            raise Exception(
                """<message> has not been provided. This exception suggests incorrect
                module-level docstring for **docopt**"""
                )
        self.message = ' '.join(self.flags["<message>"])
    
    def _parse_config_file(self, config_name):
        self.absolute_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(self.absolute_dir, config_name)

        if not os.path.isfile(config_path):
            # FIXME: raise appropriate exception
            raise Exception("Unable to read from config file")

        config = configparser.ConfigParser()
        config.read(config_path)

        if "DEFAULT" not in config:
            # FIXME: raise appropriate exception
            raise Exception("[DEFAULT] section does not exist in config file")
        # NOTE: using attributes are inappropriate due to inability to represent flags in consistent format
        self.config = config["DEFAULT"]
        
        required_keys = [
            "Model",
            "SystemPrompt",
            "ConversationFolder"
        ]
        for key in required_keys:
            if key not in self.config:
                # FIXME: raise appropriate exception
                raise Exception(f"{key} is not defined in {config_name}")

        if self.config['ConversationFolder'][0] == '~':
            self.config['ConversationFolder'] = os.path.join(Path.home(), self.config['ConversationFolder'][1:])

class ConversationManager:
    """Handles conversation state, storage and retrieval"""
    def __init__(self, config_manager):
        self.config_manager = config_manager
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
        if model == None: model = self.config_manager.config["Model"]
        conversation_path = f"{self.config_manager.config['ConversationFolder']}/{model}/conversations/{conversation_hash}/"
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
    cfg = ConfigManager("config.ini")
    msg = cfg.message
    config = cfg.config
    args = cfg.flags
    
    conversation_manager = ConversationManager(cfg)

    # we access info that we have to have access to
    #   immediately, for example latest conversation ID
    home_path = f"{config['ConversationFolder']}/"
    Path(home_path).mkdir(parents=True, exist_ok=True)
    if args["--continue"]:
        with open(os.path.join(home_path, "info.json"), "r") as f:
            try:
                info = json.load(f)
            except json.decoder.JSONDecodeError:
                print("Could not continue last conversation, error reading history file")
                quit()
        # TODO: exception handling
        ## FIXME: conversation_path is created twice
        conversation_manager.set_hash(info['last_hash'])
        conversation_manager.retrieve_conversation(config["Model"])
        # conversation_path = f"{config['ConversationFolder']}/{config["Model"]}/conversations/{info["last_hash"]}/"
        # with open(os.path.join(conversation_path, "data.json"), "r") as f:
        #     messages = json.load(f)

    # we have added messages to message queue if we had any already
    use_cache = not conversation_manager.retrieved

    # user input
    if "SystemPrompt" in config and not args["--no-sys"]:
        conversation_manager.append_message({
            "role": "system", 
            "content": config["SystemPrompt"]
            })

    conversation_manager.append_message({
                "role": "user",
                "content": msg
            })

    # we hash only first input, mostly because we expect user to rarely repeat the exact same two inputs more than once
    # hash_input = ""
    # for message in messages:
    #     hash_input += message["role"] + message["content"]
    # conversation_hash = info["last_hash"] if args["--continue"] else hashlib.sha1(hash_input.lower().encode()).hexdigest()
    conversation_manager.generate_hash()

    conversation_path = f"{config['ConversationFolder']}/{config["Model"]}/conversations/{conversation_manager.conversation_hash}/"
    # BUG: when we have a known conversation with multiple messages, we will print out the latest assistant's message, not 
    #   assistant's response to the first message. 
    if (use_cache and os.path.isdir(conversation_path)):
        print("[CACHED]:")
        with open(os.path.join(conversation_path, "data.json"), "r") as f:
            conversation_manager.retrieve_conversation(model=config["Model"])
            # messages = json.load(f)
            print(conversation_manager.messages[-1]["content"])
            print("Conversation ID: " + conversation_manager.conversation_hash)
        return

    # nate output
    completion = client.chat.completions.create(
        model = config["Model"],
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
