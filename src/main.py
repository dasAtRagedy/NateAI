"""NateAI

Usage: nate [options] [--] <message> ...

--continue  Continue the last conversation
--no-sys    Do not use system argument

"""
import os
from openai import OpenAI
from pathlib import Path
from docopt import docopt

from nate.config import Config, ConfigManager
from nate.storage import StorageManager
from nate.conversation import ConversationManager
from nate.client import AIClient, OpenAIClient

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
        storage = StorageManager(
            base_folder = config.conversation_folder,
            model = config.model
        )
        conversation_manager = ConversationManager(config, storage)

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
