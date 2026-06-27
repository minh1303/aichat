import json

class FileHandler:
    def __init__(self, file_dir: str = "conversation.json"):
        self.file_dir = file_dir
    def save_conversation(self, conversation: list):
        with open(self.file_dir, "w") as f:
            json.dump(conversation, f, indent=4)
            
    def open_conversation(self):
        try:
            with open(self.file_dir, "r") as f:
                conversation = json.load(f)
            return conversation
        except FileNotFoundError:
            return []