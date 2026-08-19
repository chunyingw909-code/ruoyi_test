import requests
from common.utils import read_yaml



class LoginApi():
    def __init__(self):
        config = read_yaml('config/config.yaml')
        self.base_url=config['base_url']


    def login(self,username,password):
        payload = {'username': username, 'password': password}
        r = requests.post(self.base_url+'/login',json=payload)

        return r.json()