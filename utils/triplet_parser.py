'''
    使用LLM进行关系抽取
    输出完成后还需要手动将输出文件的最后一个逗号去掉，然后在开始和末尾加上中括号
'''
import re
from typing import List
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser,BaseGenerationOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.outputs import Generation
from utils.zhipu_llm import ZhipuLLM
from icecream import ic

class TripletParser(BaseGenerationOutputParser):
    def __init__(self):
        super().__init__()

    def parse_result(self, result: List[Generation]) -> str:
        text = result[0].text
        relations = re.findall(r'(\{\s*?\n\s*?"subject":.*?",\s*?"subject_type":.*?",\s*?"relation":.*?",\s*?"object":.*?",\s*?"object_type":.*?"\s*?\})', text)
        if relations.__len__() == 0:
            return ""
        response = ""
        for relation in relations:
            response += relation + ",\n"
        response = response.strip(",\n")
        # 去除多余的逗号，使用正则表达式找到所有的逗号，然后去除掉
        return re.sub(r",\s*?\n?\s*?\}", "\n}", response)
        

if __name__ == "__main__":
    '''
    model = baichuan2.Baichuan2()
    extrator = Extractor(model)
    extrator.run(r'./data/data_0.txt', r'./data/output_0.json', "降膜机组使用说明书")'''
    model = ZhipuLLM()
    parser = TripletParser()
    prompt = PromptTemplate(
        template='''假设你是一个实体关系抽取模型，你需要抽取出接下来用三重反引号限定的句子中成对的关系实体。
        该句子来源于降膜机组使用说明书中。
        主体类型、联系和客体类型的值都必须是中文，且主体和客体必须完整摘自句子中，主体和客体越长、越完整越好。
        抽取出的每个关系需要完全符合{{"subject":"主体", "subject_type":"主体类型", "relation":"联系", "object":"客体", "object_type":"客体类型"}}的JSON格式
        最后只输出符合JSON格式的结果。
        ```
        {sentence}
        ```
        ''',
        input_variables=['sentence']
    )
    chain = prompt | model | parser
    print(chain.invoke({"sentence": "降膜式半封闭螺杆冷媒机组轻微漏氟处理建议只要机组在现场已安装就位，不用等现场水电条件具备，在调试前就可以先到用户现场查看机组是否有泄漏，如果检查到机组有泄漏，提前处理可最大限度的避免因机组迟迟不能正常运行对用户造成不良影响。"}))
    

