import json
from typing import Protocol, List, Dict
from openai import OpenAI

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
