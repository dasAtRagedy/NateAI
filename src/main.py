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
import json
from typing import Dict, List
from typing import Protocol
from docopt import docopt

from nate.config import Config, ConfigManager
from nate.conversation import ConversationManager

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
