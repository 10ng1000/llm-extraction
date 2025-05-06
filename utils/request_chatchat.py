import requests

class ChatChatClient(object):
    def __init__(self, entrypoint='http://62.234.40.129:43360'):
        self.entrypoint = entrypoint
        self.client = requests.Session()
    
    def chat(self, message: str):
        url = f'{self.entrypoint}/chat/chat'
        response = self.client.post(url, json={
                "query": message,
                "history": [],
                "stream": false
            })
        print(response)
        return response.json()['choices'][0]['message']['content']
    
if __name__ == '__main__':
    client = ChatChatClient()
    print(client.chat('你好'))
