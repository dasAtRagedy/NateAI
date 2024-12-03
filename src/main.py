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

client = OpenAI()
config = configparser.ConfigParser()

config.read(os.path.join(os.path.dirname(__file__), "../config.ini"))
if "DEFAULT" not in config:
    raise Exception("[DEFAULT] section does not exist in config file")
config = config["DEFAULT"]
if config['ConversationFolder'][0] == '~':
    config['ConversationFolder'] = os.path.join(Path.home(), config['ConversationFolder'][1:])

args = docopt(__doc__)

def main(msg):
    messages = []

    home_path = f"{config['ConversationFolder']}/"
    Path(home_path).mkdir(parents=True, exist_ok=True)
    if args["--continue"]:
        with open(os.path.join(home_path, "info.json"), "r") as f:
            try:
                info = json.load(f)
            except json.decoder.JSONDecodeError:
                print("Could not continue last conversation, error reading history file")
                quit()
        conversation_path = f"{config['ConversationFolder']}/{config["Model"]}/conversations/{info["last_hash"]}/"
        with open(os.path.join(conversation_path, "data.json"), "r") as f:
            messages = json.load(f)

    use_cache = False if messages else True

    if "SystemPrompt" in config and not args["--no-sys"]:
        messages.append({
            "role": "system", 
            "content": config["SystemPrompt"]
            })

    messages.append({
                "role": "user",
                "content": msg
            })

    hash_input = ""
    for message in messages:
        hash_input += message["role"] + message["content"]
    conversation_hash = info["last_hash"] if args["--continue"] else hashlib.sha1(hash_input.lower().encode()).hexdigest()

    conversation_path = f"{config['ConversationFolder']}/{config["Model"]}/conversations/{conversation_hash}/"
    if (use_cache and os.path.isdir(conversation_path)):
        print("[CACHED]:")
        with open(os.path.join(conversation_path, "data.json"), "r") as f:
            messages = json.load(f)
            print(messages[-1]["content"])
            print("Conversation ID: " + conversation_hash)
        return

    completion = client.chat.completions.create(
        model = config["Model"],
        messages = messages
    )
    messages.append({
        "role": "assistant",
        "content": completion.choices[0].message.content,
        "completion": serialize_completion(completion)
        })

    print(messages[-1]["content"])
    print("Conversation ID: " + conversation_hash)

    conversation_contents_md = ""
    for msg in messages:
        conversation_contents_md += f"**{msg["role"].title()}**:\n{msg["content"]}\n"
        if msg["role"] == "assistant": conversation_contents_md += "\n"

    Path(conversation_path).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(conversation_path, "conversation.md"), "w+") as f:
        f.write(conversation_contents_md)

    with open(os.path.join(conversation_path, "data.json"), "w+", encoding="utf-8") as f:
        json.dump(messages, f, indent=4)

    with open(os.path.join(home_path, "info.json"), "w") as f:
        json.dump({
            "last_hash": conversation_hash
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
    # pass
    main(' '.join(args["<message>"]))