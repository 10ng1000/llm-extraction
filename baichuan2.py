import timeout_decorator
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation.utils import GenerationConfig

class Baichuan2():
    def __init__(self, path: str = "../baichuan-inc/Baichuan2-13B-Chat-4bits"):
        self.tokenizer = AutoTokenizer.from_pretrained(path, use_fast=False, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(path, device_map="auto", torch_dtype=torch.bfloat16, trust_remote_code=True)
        self.model.generation_config = GenerationConfig.from_pretrained(path)
        self.index = 0

    @timeout_decorator.timeout(300)
    def get_response(self, prompt: str):
        messages = [{"role": "user", "content": prompt}]
        response = self.model.chat(self.tokenizer, messages)
        return response
