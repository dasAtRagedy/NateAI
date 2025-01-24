from .config import Config
from .conversation import ConversationManager
from .client import AIClient

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
