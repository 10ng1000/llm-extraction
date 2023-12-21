import requests

class Client(object):
    '''
        用于连接doccano的客户端
    '''

    def __init__(self, entrypoint='http://82.157.118.175:8098', username='bingshan@datalabel.com', password='bingshan'):
        self.entrypoint = entrypoint
        self.client = requests.Session()
        self.client.auth = (username, password)
        token = self.client.request("POST",f'{self.entrypoint}/v1/auth/login/', json={'username': username, 'password': password}).cookies['csrftoken']
        self.client.headers.update({'X-CSRFToken': token})
        
        '''token = response['token']
        self.client.headers.update({'Authorization': f'Token {token}',
                                     'Accept': 'application/json'})'''

    def fetch_projects(self):
        url = f'{self.entrypoint}/v1/projects'
        response = self.client.get(url)
        return response

    def create_project(self, name, description, project_type = 'SequenceLabeling'):
        mapping = {'SequenceLabeling': 'SequenceLabelingProject',
                   'DocumentClassification': 'TextClassificationProject',
                   'Seq2seq': 'Seq2seqProject'}
        data = {
            'name': name,
            'project_type': project_type,
            'description': description,
            'guideline': 'Hello',
            'allow_overlapping': 'true',
            'use_relation': 'true',
            'resourcetype': mapping[project_type]
        }
        url = f'{self.entrypoint}/v1/projects'
        response = self.client.post(url, json=data)
        return response

    def fetch_documents(self, project_id):
        url = f'{self.entrypoint}/v1/projects/{project_id}/examples'
        response = self.client.get(url)
        return response

    def fetch_labels(self, project_id):
        '''
            获取所有的标签
        '''
        url = f'{self.entrypoint}/v1/projects/{project_id}/labels'
        response = self.client.get(url)
        return response

    def add_span_type(self, project_id, text):
        '''
            添加一个实体类型
        '''
        data = {
            'text': text,
        }
        url = f'{self.entrypoint}/v1/projects/{project_id}/span-types'
        response = self.client.post(url, json=data)
        return response
    
    def add_relation_type(self, project_id, text):
        '''
            添加一个关系类型
        '''
        data = {
            'text': text,
        }
        url = f'{self.entrypoint}/v1/projects/{project_id}/relation-types'
        response = self.client.post(url, json=data)
        return response

    def fetch_spans(self, project_id, doc_id):
        '''
            提取文章中所有的实体
        '''
        url = f'{self.entrypoint}/v1/projects/{project_id}/examples/{doc_id}/spans'
        response = self.client.get(url)
        return response
    
    def fetch_relations(self, project_id, doc_id):
        '''
            提取文章中所有的关系
        '''
        url = f'{self.entrypoint}/v1/projects/{project_id}/examples/{doc_id}/relations'
        response = self.client.get(url)
        return response

    def post_span(self, project_id, doc_id, data):
        '''
            提交一个实体
        '''
        url = f'{self.entrypoint}/v1/projects/{project_id}/examples/{doc_id}/spans'
        response = self.client.post(url, json=data)
        return response
    
    def post_relation(self, project_id, doc_id, data):
        '''
            提交一个关系
        '''
        url = f'{self.entrypoint}/v1/projects/{project_id}/examples/{doc_id}/relations'
        response = self.client.post(url, json=data)
        return response

    def get_span_types(self, project_id):
        '''
            获取所有的实体类型
        '''
        url = f'{self.entrypoint}/v1/projects/{project_id}/span-types'
        response = self.client.get(url)
        return response
    
    def get_relation_types(self, project_id):
        '''
            获取所有的关系类型
        '''
        url = f'{self.entrypoint}/v1/projects/{project_id}/relation-types'
        response = self.client.get(url)
        return response

    def __delete_span(self, project_id, doc_id, span_id):
        url = f'{self.entrypoint}/v1/projects/{project_id}/examples/{doc_id}/spans/{span_id}'
        response = self.client.delete(url)
        return response

    def __delete_relation(self, project_id, doc_id, relation_id):
        url = f'{self.entrypoint}/v1/projects/{project_id}/examples/{doc_id}/relations/{relation_id}'
        response = self.client.delete(url)
        return response
    
    def delete_all_spans_and_relations(self, project_id):
        all_spans = self.fetch_spans(project_id, 8).json()
        for span in all_spans:
            self.__delete_span(project_id, 8, span['id'])
        all_relations = self.fetch_relations(project_id, 8).json()
        for relation in all_relations:
            self.__delete_relation(project_id, 8, relation['id'])

if __name__ == '__main__':
    client = Client(username='bingshan@datalabel.com', password='bingshan')
    '''
    data = {
        'label': 972,
        'start_offset': 0,
        'end_offset': 12,
    }
    client.delete_all_spans_and_relations(5)'''
    #print(client.create_project('test', 'test').json())
    print(client.fetch_documents(11).json())