import json

import mysite
from celery.result import AsyncResult
import celery.app.control
from . import models
from llm_relation_extraction.tasks import extraction_task, to_doccano_task
from llm_relation_extraction.models import Project
from django.http import HttpResponse
from django.views import View
import os
from celery import Celery
from llm_relation_extraction.request_client import Client


class ImportData(View):
    def post(self, request, *args, **kwargs):
        client = Client()
        # 创建用于存储处理的文件的文件夹，并将文件存储在该文件夹中
        data = json.loads(request.body, encoding='utf-8')
        project_id = data.get('project_id')
        file_name = data.get('file_name')
        # print(client.fetch_documents(project_id).json())
        document = client.fetch_documents(project_id).json()['results']
        if len(document) == 0:
            res = HttpResponse('项目中没有文档')
            res.status_code = 400
            return res
        # 如果没有project对象，则创建project对象
        if not Project.objects.filter(id=project_id).exists():
            project = Project(id=project_id, name=file_name, task_id=None)
            project.save()
        if len(document) > 1:
            res = HttpResponse('注意，项目中有多个文档，默认上传第一个文档')
        else:
            res = HttpResponse('ok')
        content = document[0]['text']
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, f'../data/{file_name}')
        if not os.path.exists(path):
            os.mkdir(path)
            print('创建文件夹')
        path = os.path.join(path, f'{file_name}.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            print('写入文件')
        return res


class ExecuteExtraction(View):
    def post(self, request):
        data = json.loads(request.body, encoding='utf-8')
        file_name = data.get('file_name')
        print(f"file_name is {file_name}")
        # 执行异步任务
        task = extraction_task.delay(file_name)
        # 将任务id存储到数据库中
        project_id = data.get('project_id')
        project = Project.objects.get(id=project_id)
        print(f"former task id is {project.task_id}, now task id is {task.id}")
        project.task_id = task.id
        project.save()
        # 返回任务id
        return HttpResponse(json.dumps({'task_id': task.id}))


class GetTaskStatus(View):
    def get(self, request):
        # 从url中获取project_id
        project_id = request.GET.get('project_id')
        try:
            task_id = Project.objects.get(id=project_id).task_id
        except Exception as e:
            response = HttpResponse('项目不存在')
            response.status_code = 404
            return response
        if task_id is None:
            response = HttpResponse('任务不存在')
            response.status_code = 404
            return response
        result = AsyncResult(task_id)
        task_status = result.state
        print(task_id)
        print(task_status)
        file_name = Project.objects.get(id=project_id).name
        # 检测是否执行完毕
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, f'../data/{file_name}/check_point')
        if not os.path.exists(path):
            check_point = '0'
        else:
            with open(path, 'r', encoding='utf-8') as f:
                check_point = f.read()
        # 获得用句号分割的句子总数
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, f'../data/{file_name}/{file_name}.txt')
        with open(path, 'r', encoding='utf-8') as f:
            sentences = f.read().split('。')
            print(sentences)
            total = len(sentences)
            print(total)
        return HttpResponse(json.dumps({'status': task_status, 'check_point': check_point, 'total_lines': total}))


class RevokeTask(View):
    def post(self, request):
        # 从url中获取project_id
        project_id = json.loads(request.body, encoding='utf-8').get('project_id')
        try:
            task_id = Project.objects.get(id=project_id).task_id
        except Exception as e:
            response = HttpResponse('项目不存在')
            response.status_code = 404
            return response
        if task_id is None:
            response = HttpResponse('任务不存在')
            response.status_code = 404
            return response
        AsyncResult(task_id).revoke(terminate=True)
        #ctrl = celery.app.control.Control(mysite.celery_app)
        #ctrl.revoke(task_id = str(task_id), terminate=True, signal='SIGKILL')
        print(f"revoke task {task_id}")
        return HttpResponse()


class GetOutput(View):
    def get(self, request):
        project_id = request.GET.get('project_id')
        try:
            file_name = Project.objects.get(id=project_id).name
        except Exception as e:
            response = HttpResponse('项目不存在')
            response.status_code = 404
            return response
        # 读取../data/file_name/output的内容
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, f'../data/{file_name}/{file_name}_output.json')
        print(path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                output = f.read()
        except Exception as e:
            response = HttpResponse('文件不存在，可能是任务正在启动')
            response.status_code = 404
            return response
        # 去除换行符，并把引号前的反斜杠去掉
        # output = output.replace('\n', '').replace('\"', '"')
        return HttpResponse(json.dumps({'output': output}, ensure_ascii=False))


class Reset(View):
    def post(self, request):
        # 从url中获取project_id
        project_id = json.loads(request.body, encoding='utf-8').get('project_id')
        try:
            project = Project.objects.get(id=project_id)
            # 删除这个project记录
            file_name = Project.objects.get(id=project_id).name
        except Exception as e:
            response = HttpResponse('项目不存在')
            response.status_code = 404
            return response
        task_id = Project.objects.get(id=project_id).task_id
        project.delete()
        if task_id is not None:
            AsyncResult(task_id).revoke(terminate=True)
        # 删除../data/file_name文件夹
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, f'../data/{file_name}')
        if os.path.exists(path):
            os.system(f'rm -rf {path}')
        return HttpResponse('ok')


class ToDoccano(View):
    def post(self, request):
        project_id = json.loads(request.body, encoding='utf-8').get('project_id')
        data = json.loads(request.body, encoding='utf-8').get('data')
        # 确定doccano里是否有且只有一个文档，获得文档id
        client = Client()
        document = client.fetch_documents(project_id).json()['results']
        if len(document) == 0:
            res = HttpResponse('项目中没有文档')
            res.status_code = 400
            return res
        try:
            project = Project.objects.get(id=project_id)
        except Exception as e:
            response = HttpResponse('项目不存在')
            response.status_code = 404
            return response
        file_name = project.name
        # 获取文件位置
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, f'../data/{file_name}/')
        # 上传任务
        task = to_doccano_task.delay(file_name=file_name, project_id=project_id, post_labels=True,
                                     doc_id=document[0]['id'], spliter='。', base_path=path)
        # 将任务id存储到数据库
        project.doccano_task_id = task.id
        project.save()
        return HttpResponse(json.dumps({'task_id': task.id}))


class GetDoccanoStatus(View):
    def get(self, request):
        project_id = request.GET.get('project_id')
        try:
            task_id = Project.objects.get(id=project_id).doccano_task_id
        except Exception as e:
            response = HttpResponse('项目不存在')
            response.status_code = 404
            return response
        if task_id is None:
            response = HttpResponse('任务不存在')
            response.status_code = 404
            return response
        task_status = to_doccano_task.AsyncResult(task_id).state
        trace = to_doccano_task.AsyncResult(task_id).traceback
        ret = str(to_doccano_task.AsyncResult(task_id).result)
        print(task_id)
        print(trace)
        print(ret)
        return HttpResponse(json.dumps({'status': task_status, 'traceback': trace, 'result': ret}))
