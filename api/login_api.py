from common.http_client import HttpClient

class LoginApi:
    def __init__(self):
        self.client = HttpClient()

    def login(self, username, password):
        return self.client.post('/login', json={'username': username, 'password': password})