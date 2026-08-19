import requests
from common.utils import read_yaml


class UserApi():
    def __init__(self,token):
        config = read_yaml('config/config.yaml')
        self.base_url = config['base_url']
        self.headers = {'Authorization': f'Bearer {token}'}


    def add_user(self,username,nickname,**kwargs):
        add_url = self.base_url+'/system/user'
        payload = {'userName':username,'nickName':nickname}
        payload.update(kwargs)
        r = requests.post(add_url ,headers=self.headers, json=payload)
        return r.json()

    def list_user(self,username):
        list_url = self.base_url+'/system/user/list'
        params = {'userName':username}
        r = requests.get(list_url,headers=self.headers,params=params)
        return r.json()

    def delete_user(self,user_id):
        delete_url=f'{self.base_url}/system/user/{user_id}'
        r = requests.delete(delete_url,headers=self.headers)
        return r.json()









