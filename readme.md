# NateAI

Command-line AI tool

## Motivation

What I found does not suit my fancy, created with a couple of goals in mind:
- Saved and reusable conversation history
- Rich markdown support
- Does not rely on REPL
- Does not run as a service in the background

## Prerequisites

You have to have openai api key connected to an account with a valid balance
Installed Python 3.12.2
Installed Python module "venv"
Installed Git

## Setup

Open commandline with Git installed

Navigate to the directory where you want it installed

Clone the repository: `git clone https://github.com/dasAtRagedy/NateAI.git`

Navigate into the cloned repository

Create a virtual environment: `python -m venv venv`

Activate the virtual environment:
- On Windows, type: `venv\Scripts\activate`
- On Linux, type: `source venv/bin/activate`

Install packages from requirements.txt: `pip install -r requirements.txt`

Copy/rename `example_config.ini` to `config.ini`: `cp ./example_config.ini ./config.ini`

Change values in `config.ini` if necessary

Export openai api key:
- On Windows, type: `set OPENAI_API_KEY="EXAMPLE-API-KEY"`
- On Linux, type: `export OPENAI_API_KEY="EXAMPLE-API-KEY"`

## Usage

Use `python src/main.py 'Hey, nate, whats up?'`

For all available options, use `python src/main.py --help`

## Goals

- [x] save messages
- [x] save conversations
- [x] **use cached messages to respond to known prompts**
- [ ] retrieve a list of saved conversations
- [ ] change saved conversation directory from cli (optional)
- [ ] insert messages from specified conversation
- [ ] change model
- [ ] retrieve a list of possible models
- [ ] add flag to not save conversation
- [ ] add alias to conversations
- [ ] add simplified IDs to conversations
- [ ] add option token limit
- [ ] add logging
- [ ] allow for piping file contents into terminal-gpt
- [ ] allow for custom system prompt
- [ ] **display messages with `rich` formatting**
- [ ] interactive terminal (ambitious)
- [ ] give it a name, come on, call it Nate or something
- [ ] add system prompt reminders after some amount of tokens generated, we don't want it straying from conversation after some time
- [ ] add system prompt presets (as sumbodule?)
- [ ] custom system prompt presets (optional) <!-- https://github.com/mustvlad/ChatGPT-System-Prompts -->
- [ ] custom name cause why not
- [ ] math equations rendering? (ambitious)
- [ ] visual token by token generation (optional)
- [ ] continue conversation from n-th message