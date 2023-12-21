import pytest
import requests
import json
base_url ='http://210.30.97.207:8000/llm_relation_extraction/'


def test_import_data():
    url = base_url + 'import_data'
    #使用utf-8编码
    #data = {'file_name': 'test1', 'content': '这个文件是一个测试文件夹'.encode('utf-8').decode('utf-8')}
    data = {'project_id': 11, 'file_name': '测试降膜机组'}
    res = requests.post(url, data=json.dumps(data))
    print(res.text)

#需要异步调用
def test_execute_extraction():
    url = base_url + 'execute_extraction'
    data = {'file_name': '测试降膜机组'}
    res = requests.post(url, data=json.dumps(data))
    print(res.text)

def test_get_task_status():
    url = base_url + 'get_task_status'
    data = {'task_id': '27d29c64-cd26-4d6d-9c2a-3c8cb8bd6565'}
    res = requests.get(url, data=json.dumps(data))
    print(res.text)

def test_get_checkpoint():
    url = base_url + 'get_checkpoint'
    data = {'file_name': '测试降膜机组'}
    res = requests.get(url, data=json.dumps(data))
    print(res.text)

def test_get_output():
    url = base_url + 'get_output'
    data = {'file_name': 'test1'}
    res = requests.get(url, data=json.dumps(data))
    out = res.json()['output']
    print(out)