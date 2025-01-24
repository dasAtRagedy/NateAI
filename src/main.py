"""NateAI

Usage: nate [options] [--] <message> ...

--continue  Continue the last conversation
--no-sys    Do not use system argument

"""
import os
from openai import OpenAI
from pathlib import Path
from docopt import docopt

from nate.config import ConfigManager
from nate.storage import StorageManager
from nate.conversation import ConversationManager
from nate.client import OpenAIClient

from nate.app import NateAI

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
