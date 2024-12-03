"""NateAI

Usage: nate <message>

Options:
    -h --help           Show this screen.

"""
from openai import OpenAI
import configparser
from rich.console import Console
from rich.markdown import Markdown
from docopt import docopt

client = OpenAI()
config = configparser.ConfigParser()
config.read("config.ini")
if "DEFAULT" not in config:
    raise Exception("[DEFAULT] section does not exist in config file")
config = config["DEFAULT"]

def main(msg):
    messages = []
    if "SystemPrompt" in config:
        messages.append({
            "role": "system", 
            "content": config["SystemPrompt"]
            })

    messages.append({
                "role": "user",
                "content": msg
            })

    completion = client.chat.completions.create(
        model=config["Model"],
        messages=messages
    )
    
    print(completion.choices[0].message.content)

if __name__ == "__main__":
    args = docopt(__doc__)
    
    main(args["<message>"])