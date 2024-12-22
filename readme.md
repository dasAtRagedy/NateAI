# NateAI

Command-line AI tool

## Motivation

What I found does not suit my fancy, created with a couple of goals in mind:
- Saved and reusable conversation history
- Rich markdown support
- Does not rely on REPL
- Does not run as a service in the background

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
<!-- https://github.com/mustvlad/ChatGPT-System-Prompts -->
- [ ] custom system prompt presets
- [ ] custom name cause why not
- [ ] math equations rendering? (ambitious)
- [ ] visual token by token generation (optional)
- [ ] continue conversation from n-th message