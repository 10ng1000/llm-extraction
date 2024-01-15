'''
    使用LLM进行关系抽取
    输出完成后还需要手动将输出文件的最后一个逗号去掉，然后在开始和末尾加上中括号
'''
from langchain.prompts import PromptTemplate
from langchain.llms.base import LLM
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.document_loaders import TextLoader
from utils.triplet_parser import TripletParser
from utils.chatglm_llm import Chatglm
from utils.zhipu_llm import ZhipuLLM
import argparse


class Extraction():
    def __init__(self, file_name: str, context: str = None, model: LLM = Chatglm()):
        '''模型默认为Chatglm，如果效果一般可以换为zhipu的api'''
        self.file_name = file_name
        self.model = model
        self.name = file_name
        if context is None:
            context = file_name
        self.context = context
        # 这里不能设置chunk_size，因为之后要匹配到原文中
        self.parser = TripletParser()
        tool_kit = FileManagementToolkit(
            root_dir=(f"./data/{self.file_name}"),
            selected_tools=["read_file", "write_file", "list_directory"]
        )
        self.read_tool, self.write_tool, self.list_tool = tool_kit.get_tools()
        self.output_file = f'{file_name}_output.json'

    def run(self, separator: str = "。"):
        '''从给定的文档中提取三元组。首先进行分块（始终一致），然后对于每个分块，提取出其中的三元组（可能多个），然后加上index写入文件中'''
        '''中途可能被中断，因此从文件里读写记录点，并且实时把输出写入文件'''
        
        # 从文件中读取需要提取的三元组源输入，分块，并去掉split可能生成的空块
        data = TextLoader(f'./data/{self.file_name}/{self.file_name}.txt').load()[0].page_content.split(separator)
        if data[-1] == '':
            data = data[:-1]
        print(data)
        # 从文件中读取记录点，如果没有记录点，就从头开始，记录点表示需要从哪个块开始提取
        check_point = self.read_tool.run({"file_path" : f"check_point"})
        try:
            check_point = int(check_point)
        except:
            check_point = 0
            self.write_tool.run({"file_path" : f"check_point", "text" : "0", "append" : False})
        print(f"读取记录点{check_point}")
        if check_point == 0:
            self.write_tool.run({"file_path" : f"{self.output_file}", "text" : "[", "append" : False})
        # data从记录点开始
        data = data[check_point:]
        prompt = PromptTemplate(
                input_variables=["context", "sentence"],
                template="""
                 假设你是一个实体关系抽取模型，你需要抽取出接下来用三重反引号限定的句子中成对的关系实体。该句子来源于{context}中。
                抽取出的每个关系需要完全符合{{"subject":"主体", "subject_type":"主体类型", "relation":"联系", "object":"客体", "object_type":"客体类型"}}的JSON格式，主体类型、联系和客体类型的值都必须是中文，
                且主体和客体必须完整摘自句子中，主体和客体越长、越完整越好。最后只输出符合JSON格式的结果。
                ```{sentence}```"""
            )
        chain = prompt | self.model | self.parser
        index = check_point
        for chunk in data:
            # 得到每一个块由LLM提取出的关系
            response = chain.invoke({"context": self.context, "sentence": chunk})
            print(f"第{index}个块的输出为{response}")
            chunk_output = f'''{{"index": {index}, "response": \n[{response}]}}'''
            if response != "":
                self.write_tool.run({"file_path" : f"{self.output_file}", "text" : f"{chunk_output},\n", "append" : True})
            index += 1
            check_point = index
            # 更新记录点
            self.write_tool.run({"file_path" : f"check_point", "text" : str(check_point), "append" : False})

        # 把最后一个逗号去掉，然后在开始和末尾加上中括号，以符合JSON格式
        processed_output = self.read_tool.run({"file_path" : f"{self.output_file}"}).strip()[:-1] + "]"
        self.write_tool.run({"file_path" : f"{self.output_file}", "text" : f"{processed_output}", "append" : False})
        print("写入文件完成")