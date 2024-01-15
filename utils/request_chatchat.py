import requests

class ChatChatClient(object):
    def __init__(self, entrypoint='http://82.157.118.175:43360'):
        self.entrypoint = entrypoint
        self.client = requests.Session()
    
    def chat(self, message: str):
        url = f'{self.entrypoint}/chat/chat'
        response = self.client.post(url, json={
                "query": message,
                "history": [],
                "stream": False,
                "model_name": "chatglm3-6b-32k",
                "temperature": 0.7,
                "prompt_name": "default"
            }
            )
        return response.json()['text']
    
if __name__ == '__main__':
    client = ChatChatClient()
    print(client.chat('你好'))
