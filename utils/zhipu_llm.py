import zhipuai
from icecream import ic
from langchain.llms.base import LLM 
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema.output import GenerationChunk
from langchain.embeddings.base import Embeddings
from typing import Optional, List, Any, Mapping, Iterator, Callable
from http import HTTPStatus  
import re
import json
#import pretty_errors

# 请在这里填写你的API_KEY
zhipuai.api_key = 'api_key' 

class ZhipuLLM(LLM):
    model: str = 'chatglm_turbo'

    @property
    def _llm_type(self) -> str:
        return 'zhipu-api'
    
    def _stream(  
            self,  
            prompt: str,  
            stop: Optional[List[str]] = None,  
            run_manager: Optional[CallbackManagerForLLMRun] = None,  
            **kwargs: Any,  
    ) -> Iterator[GenerationChunk]:  
        response = zhipuai.model_api.sse_invoke(
            model=self.model,  
            prompt=prompt
        )
        for event in response.events():  
            if event.event == "add":
                yield GenerationChunk(
                    text=event.data
                )
            elif event.event == "finish":
                yield GenerationChunk(
                    text='\n',
                    #generation_info=event.meta
                )
            else:  
                yield GenerationChunk(  
                    text=f"响应失败,失败信息为: {event.event}",
                )  

    def _call(
        self,  
        prompt: str,  
        stop: Optional[List[str]] = None,  
        run_manager: Optional[CallbackManagerForLLMRun] = None,  
        **kwargs: Any,  
    ) -> str:
        if stop is not None:  
            raise ValueError("stop kwargs are not permitted.")  
        response = zhipuai.model_api.invoke(  
            model=self.model,  
            prompt=prompt  
        )
        if response['code'] != HTTPStatus.OK:  
            raise RuntimeError(  
                f"Zhipu API returned an error: {response['code']} {response['msg']}"  
            )
        content = response['data']['choices'][0]['content']
        r1 = re.sub(r'\\"', '"',content)
        r2 = r1.replace("\\n", "\n")
        r3 = r2.replace('"，', '",')
        return r3
    
    @property  
    def _identifying_params(self) -> Mapping[str, Any]:  
        """Get the identifying parameters."""  
        return {"model": self.model}  