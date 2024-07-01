from icecream import ic
from langchain.llms.base import LLM 
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema.output import GenerationChunk
from langchain.embeddings.base import Embeddings
from typing import Optional, List, Any, Mapping, Iterator, Callable
from http import HTTPStatus  
from utils.request_chatchat import ChatChatClient
import re
import json
#import pretty_errors

class Chatglm(LLM):
    model: str = 'chatglm3_6b_32k'
    client: ChatChatClient = ChatChatClient()

    @property
    def _llm_type(self) -> str:
        return 'chatglm3-local'

    def _call(
        self,  
        prompt: str,  
        stop: Optional[List[str]] = None,  
        run_manager: Optional[CallbackManagerForLLMRun] = None,  
        **kwargs: Any,  
    ) -> str:
        response = self.client.chat(prompt)
        r1 = re.sub(r'\\"', '"',response)
        r2 = r1.replace("\\n", "\n")
        r3 = r2.replace('"，', '",')
        return r3
    
    @property  
    def _identifying_params(self) -> Mapping[str, Any]:  
        """Get the identifying parameters."""  
        return {"model": self.model}  


# 测试
if __name__ == "__main__":
    chatglm = Chatglm()
    ic(chatglm.invoke("你好"))