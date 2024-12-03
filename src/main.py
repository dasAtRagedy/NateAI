# import os
import sys
from openai import OpenAI
import configparser
from rich.console import Console
from rich.markdown import Markdown

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
    # main()
    if len(sys.argv) != 2:
        raise Exception("No message has been provided")
    main(sys.argv[1])