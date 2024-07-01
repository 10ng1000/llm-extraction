import json
from celery.result import AsyncResult
from extraction.tasks import extraction_task, to_doccano_task
from extraction.models import Project
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, HttpResponseServerError, HttpResponseForbidden
from django.views import View
import os
from utils.request_doccano import Client

BASE_DIR = '../data'

class ProjectView(View):
    def post(self, request, project_id):
        client = Client()
        # 创建用于存储处理的文件的文件夹，并将文件存储在该文件夹中
        data = json.loads(request.body)
        file_name = data.get('file_name')
        document = client.fetch_documents(project_id).json()['results']
        if len(document) == 0:
            return HttpResponseNotFound('项目中没有文档')
        import_message = '' if len(document) == 1 else '请注意，项目中有多个文档，只会处理第一个文档,'
        content = document[0]['text']
        # 将content写入文件
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, f'{BASE_DIR}/{file_name}')
        if not os.path.exists(path):
            os.mkdir(path)
            print('创建文件夹')
        path = os.path.join(path, f'{file_name}.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            print('创建文本文件')
        # 如果没有project对象，则创建project对象
        if not Project.objects.filter(id=project_id).exists():
            project = Project(id=project_id, name=file_name, task_id=None)
            project.save()
        else:
            project = Project.objects.get(id=project_id)
        # 执行提取
        task = extraction_task.delay(file_name)
        project.task_id = task.id
        project.save()
        message = import_message + '任务已经开始执行'
        return HttpResponse(json.dumps({'task_id': task.id, 'message': message}))


class TaskView(View):
    def get(self, request, project_id):
        # 从url中获取project_id
        try:
            task_id = Project.objects.get(id=project_id).task_id
        except Exception as e:
            return HttpResponseNotFound('项目不存在')
        if task_id is None:
            return HttpResponseNotFound('任务不存在')
        result = AsyncResult(task_id)
        task_status = result.state
        file_name = Project.objects.get(id=project_id).name
        # 检测是否执行完毕
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, f'{BASE_DIR}/{file_name}/check_point')
        if not os.path.exists(path):
            return HttpResponseServerError('文件不存在，可能需要重置任务')
        else:
            with open(path, 'r', encoding='utf-8') as f:
                check_point = int(f.read())
        # 获得用句号分割的句子总数，用作进度
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, f'{BASE_DIR}/{file_name}/{file_name}.txt')
        with open(path, 'r', encoding='utf-8') as f:
            sentences = f.read().split('。')
            print(sentences)
            total = len(sentences)
            # 如果最后一个句子为空，则句子计算也要减一
            if sentences[-1] == '':
                total -= 1
        return HttpResponse(json.dumps({'status': task_status, 'check_point': check_point, 'total_lines': total}))
    
    def post(self, request, project_id):
        method = json.loads(request.body).get('method')
        try:
            project = Project.objects.get(id=project_id)
            file_name = Project.objects.get(id=project_id).name
            task_id = Project.objects.get(id=project_id).task_id
        except Exception as e:
            return HttpResponseNotFound('项目不存在')
        if task_id is None: 
            HttpResponseNotFound('任务不存在')
        if method == 'reset':
            project.delete()
            if task_id is not None:
                AsyncResult(task_id).revoke(terminate=True)
            path = os.path.abspath(os.path.dirname(__file__))
            path = os.path.join(path, f'{BASE_DIR}/{file_name}')
            if os.path.exists(path):
                os.system(f'rm -rf {path}')
            return HttpResponse(json.dumps({'message': '已重置'}))
        elif method == 'revoke':
            AsyncResult(task_id).revoke(terminate=True)
            return HttpResponse(json.dumps({'message': '已终止任务'}))
        else:
            return HttpResponseBadRequest('method错误')


class OutputView(View):
    def get(self, request, project_id):
        try:
            file_name = Project.objects.get(id=project_id).name
        except Exception as e:
            response = HttpResponse('项目不存在')
            response.status_code = 404
            return response
        # 读取{BASE_DIR}/file_name/output的内容
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, f'{BASE_DIR}/{file_name}/{file_name}_output.json')
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

class DoccanoView(View):
    def post(self, request, project_id):
        data = json.loads(request.body).get('data')
        # 确定doccano里是否有且只有一个文档，获得文档id
        client = Client()
        document = client.fetch_documents(project_id).json()['results']
        if len(document) == 0:
            return HttpResponseNotFound('项目中没有文档')
        try:
            project = Project.objects.get(id=project_id)
        except Exception as e:
            return HttpResponseNotFound('项目不存在')
        file_name = project.name
        # 获取文件位置
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, f'{BASE_DIR}/{file_name}/')
        # 上传任务
        task = to_doccano_task.delay(file_name=file_name, project_id=project_id, post_labels=True,
                                     doc_id=document[0]['id'], spliter='。', base_path=path)
        # 将任务id存储到数据库
        project.doccano_task_id = task.id
        project.save()
        return HttpResponse(json.dumps({'task_id': task.id, 'message': '任务已经开始执行'}, ensure_ascii=False))
    
    def get(self, request, project_id):
        try:
            task_id = Project.objects.get(id=project_id).doccano_task_id
        except Exception as e:
            return HttpResponseNotFound('项目不存在')
        if task_id is None:
            return HttpResponseNotFound('任务不存在')
        task_status = to_doccano_task.AsyncResult(task_id).state
        trace = to_doccano_task.AsyncResult(task_id).traceback
        ret = str(to_doccano_task.AsyncResult(task_id).result)
        return HttpResponse(json.dumps({'status': task_status}))
