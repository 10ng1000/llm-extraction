from dataclasses import dataclass
from utils.request_doccano import Client
import json
import argparse

@dataclass
class Span:
    label: int
    start_offset: int
    end_offset: int

@dataclass
class Relation:
    from_id: int
    to_id: int
    type: int

# 计算出实体在文章中的位置，注意，可能两个输出的response的index之间有跳过句子
def post_annotation(client: Client, output: list, article: list, span_dict: dict, relation_dict: dict, project_id: int, doc_id: int):
    print("---上传标注---")

    # 找到实体在文章中的位置
    def find_position_label_type(line:str, response: dict, entity: str, global_offset: int, least_length_to_match=1):
        start_offset = line.find(response[entity])
        if start_offset == -1 and least_length_to_match != -1:
            for i in range(least_length_to_match, len(response[entity])):
                start_offset = line.find(response[entity][:i])
                if start_offset != -1:
                    print(f"以{response[entity][:i]}匹配{response[entity]}")
                    break
            if start_offset == -1:
                print(f"句子[{line}]找不到{response[entity]}")
                return -1, -1, -1, -1
        start_offset = global_offset + start_offset
        label = response[entity + "_type"]
        type = response["relation"]
        end_offset = start_offset + len(response[entity])
        return start_offset, end_offset, label, type

    # 上传一个实体，如果已经存在，那么就不上传；如果上传成功，那么就返回id，如果上传失败，那么就抛出异常
    def post_if_not_exist(local_span, existing_spans, project_id, doc_id):
        for span in existing_spans:
            if span["start_offset"] == local_span["start_offset"] and span["end_offset"] == local_span["end_offset"] and span["label"] == local_span["label"]:
                print(f"已经存在{local_span}")
                return -1
        post = client.post_span(project_id, doc_id, local_span)
        if post.status_code == 201:
            existing_spans.append(local_span) #加入到已经存在的span中
            return post.json()["id"]
        else:
            raise print(f"上传失败{local_span}, {post.status_code}, {post.text}")
    
    # 检查所有的实体和关系是否都能在文章中找到
    def check_all_can_found_in_article(article: list, output: list):
        print("----检查所有的实体和关系是否都能在文章中找到----")
        for out in output:
            index = out["index"] # 记录实际的句子index
            for response in out["response"]:
                line = article[index]
                find_position_label_type(line, response, "subject", 0)
                find_position_label_type(line, response, "object", 0)
        print("检查无误")

    check_all_can_found_in_article(article, output)
    global_offset = 0 # 记录文章中的位置
    existing_spans = client.fetch_spans(project_id, doc_id).json()
    last_index = -1
    for out in output:
        index = out["index"] # 记录实际的句子index
        line = article[index] # 记录实际的句子
        for i in range(last_index + 1, index):
            global_offset += len(article[i])
        
        for response in out["response"]:
            # 找到实体在文章中的位置，如果找不到，那么就跳过，如果找到了，那么就上传
            start_offset, end_offset, label, type = find_position_label_type(line, response, "subject", global_offset = global_offset)
            # 如果找不到，那么就跳过
            if start_offset == -1 or label is None:
                continue
            subject_span = Span(label=span_dict[label], start_offset=start_offset, end_offset=end_offset)
            start_offset, end_offset, label, type = find_position_label_type(line, response, "object", global_offset = global_offset)
            if start_offset == -1 or label is None:
                continue
            object_span = Span(label=span_dict[label], start_offset=start_offset, end_offset=end_offset)

            # 判断该标注是否已经存在
            try:
                subject_id = post_if_not_exist(subject_span.__dict__, existing_spans, project_id, doc_id)
                object_id = post_if_not_exist(object_span.__dict__, existing_spans, project_id, doc_id)
            except:
                continue

            relation = Relation(from_id=subject_id, to_id=object_id, type=relation_dict[type])
            client.post_relation(project_id=project_id, doc_id=doc_id, data=relation.__dict__)
        # 因为有可能跳过了句子，所以要计算出跳过的句子的长度
        global_offset += len(line)
        last_index = index
        print(f"句子{index}处理完毕")

def post_realations_spans(output: list, client: Client, project_id: int):
    print("---上传实体类型和关系类型---")
    for rs in output:
        for response in rs["response"]:
            print(response)
            client.add_span_type(project_id=project_id, text=response["subject_type"])
            client.add_span_type(project_id=project_id, text=response["object_type"])
            client.add_relation_type(project_id=project_id, text=response["relation"])

def check_format_and_delete(output: list, is_strict: bool = False) -> list:
    print("---检查输出的格式是否正确---")
    has_null = False
    incorrect_response = []
    checked_output = output
    for out,i in zip(output, range(len(output))):
        if "index" not in out or "response" not in out:
            print(f'''{out["index"]}缺少关键字''')
            checked_output.remove(out)
            has_null = True
            continue
        for response,j in zip(out["response"], range(len(out["response"]))):
            if "subject_type" not in response or "object_type" not in response or "relation" not in response or "subject" not in response or "object" not in response:
                print(f'''{out["index"]}缺少关键字''')
                incorrect_response.append([i, response])
                has_null = True
                continue
            if type(response["subject_type"]) != str or type(response["object_type"]) != str or type(response["relation"]) != str or type(response["subject"]) != str or type(response["object"]) != str:
                print(f'''{out["index"]}类型不对''')
                incorrect_response.append([i, response])
                has_null = True
                continue
            if response["subject_type"] == "" or response["object_type"] == "" or response["relation"] == "" or response["subject"] == "" or response["object"] == "":
                print(f'''{out["index"]}有空值''')
                incorrect_response.append([i, response])
                has_null = True
            if is_strict:
                for key in response:
                    if key not in ["subject_type", "object_type", "relation", "subject", "object"]:
                        print(f'''{out["index"]}多余的关键字{key}''')
                        incorrect_response.append([i, response])
                        has_null = True
                        break
    if has_null:
        for response in incorrect_response:
            checked_output[response[0]].get("response").remove(response[1])
            print(f"移除")
    if not has_null:
        print("没有空值")
    return checked_output

def get_label_dict(client: Client, project_id: int):
    span_dict = {}
    relation_dict = {}
    span_response = client.get_span_types(project_id=project_id).json()
    relation_response = client.get_relation_types(project_id=project_id).json()
    for span in span_response:
        span_dict[span["text"]] = span["id"]
    for relation in relation_response:
        relation_dict[relation["text"]] = relation["id"]
    return span_dict, relation_dict

def start(article_name, output_name, post_labels, project_id, doc_id, spliter, base_path):
    # 初始化doccano客户端
    client = Client()
    # 打开文档
    original_article_file = open(f"{base_path}{article_name}", "r", encoding="utf-8")
    # 读取原始的文档，用于上传标注。
    raw_article = original_article_file.read()
    split_article = raw_article.split(spliter)
    print(raw_article.__len__())
    # 用于上传标注的文档，每一句话后面加上分隔符，因为换行符也计入了句子的长度
    article = [line + spliter for line in split_article]
    original_article_file.close()
    # 读取输出的文档
    output_file = open(f"{base_path}{output_name}", "r", encoding="utf-8")
    output = json.load(output_file)
    output_file.close()
    # 删除空值
    output = check_format_and_delete(output)
    # 上传实体类型和关系类型，只需要上传一次
    if post_labels:
        post_realations_spans(output = output, client=client, project_id=project_id)
    dict_span, dict_relation = get_label_dict(client=client, project_id=project_id)
    # 上传标注
    post_annotation(client=client, output=output, article=article, span_dict=dict_span, relation_dict=dict_relation, project_id=project_id, doc_id=doc_id)