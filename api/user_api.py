from common.http_client import HttpClient

class UserApi:
    def __init__(self, token):
        self.client = HttpClient(token)

    def add_user(self, username, nickname, **kwargs):
        payload = {'userName': username, 'nickName': nickname}
        payload.update(kwargs)
        return self.client.post('/system/user', json=payload)

    def list_user(self, username):
        return self.client.get('/system/user/list', params={'userName': username})

    def delete_user(self, user_id):
        return self.client.delete(f'/system/user/{user_id}')