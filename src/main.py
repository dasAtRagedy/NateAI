import os
from openai import OpenAI
from pathlib import Path
from docopt import docopt
from typing_extensions import Annotated
import typer
import sys

from nate.config import ConfigManager
from nate.storage import StorageManager
from nate.conversation import ConversationManager
from nate.client import OpenAIClient

from nate.app import NateAI

def main(
    message: str,
    continue_flag: Annotated[bool, typer.Option("--continue", help="Continue the last conversation")] = False,
    no_sys_flag: Annotated[bool, typer.Option("--no-sys", help="Do not use system prompt")] = False
):
    args = {(key if not key.endswith("_flag") else "--"+key[:-len("_flag")]).replace('_', '-'): value for key, value in locals().items()}
    args["<message>"] = args["message"]

    try:
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
    typer.run(main)
