from celery import shared_task
from celery import Celery
import extraction.to_doccano as to_doccano
from mysite.celery import app
from celery.utils.log import get_task_logger
from celery.contrib.abortable import AbortableTask
from extraction.extraction import Extraction

#追踪开始状态
@shared_task(track_started=True)
def extraction_task(file_name):
    '''通过API执行提取任务'''
    extraction_task = Extraction(file_name)
    extraction_task.run()

@shared_task(track_started=True )
def to_doccano_task(file_name, project_id, doc_id, spliter, base_path, post_labels):
    to_doccano.start(article_name=f'{file_name}.txt', output_name=f'{file_name}_output.json', post_labels=post_labels,
                     project_id=project_id, doc_id=doc_id, spliter=spliter, base_path=base_path)