import time

from celery import shared_task
from celery import Celery
import extraction.to_doccano as to_doccano
#import llm_relation_extraction.llm_extraction as llm_extraction
import multiprocessing
import os
import sys
from mysite.celery import app
from celery.utils.log import get_task_logger
from celery.contrib.abortable import AbortableTask
logger = get_task_logger(__name__)

#追踪开始状态
@shared_task(track_started=True)
def extraction_task(file_name):
    #在当前目录打开一个文件，并写入ceshi
    #print("current path is ", os.getcwd())
    #llm_extraction.start_extraction(file_name,file_name,file_name)
    #llm_extraction.start_extraction(file_name,file_name,file_name)
    #time.sleep(10000000)
    #从上一级目录导入llm_extraction
    sys.path.append("..")
    #回到上一级目录
    import llm_extraction
    llm_extraction.start_extraction(file_name,file_name,file_name)


@shared_task(track_started=True )
def to_doccano_task(file_name, project_id, doc_id, spliter, base_path, post_labels):
    to_doccano.start(article_name=f'{file_name}.txt', output_name=f'{file_name}_output.json', post_labels=post_labels,
                     project_id=project_id, doc_id=doc_id, spliter=spliter, base_path=base_path)