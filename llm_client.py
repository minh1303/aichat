from file_handler import FileHandler

filehandler = FileHandler()

class LLMClient:
    def __init__(self, base_url="http://localhost:1234", model=""):
        self.base_url = base_url
        self.model = model
        self.chat_url = f"{base_url}/v1/chat/completions"
        self.models_url = f"{base_url}/v1/models"
        self.conversation_history = filehandler.open_conversation()  
    async def send_message(self, message):
        self.conversation_history.append({"role": "user", "content": message})
        payload = {
            "model": self.model,
            "messages": self.conversation_history
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.chat_url, json=payload)
            response.raise_for_status()
            data = response.json()
            reply = data['choices'][0]['message']['content']
            self.conversation_history.append({"role": "assistant", "content": reply})
            filehandler.save_conversation(self.conversation_history)
            return reply
