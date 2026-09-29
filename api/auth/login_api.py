from common.http_client import HttpClient


class LoginApi:
    """认证模块 API。"""

    def __init__(self, token=None):
        self.client = HttpClient(token)

    def login(self, username, password):
        return self.login_payload({'username': username, 'password': password})

    def login_payload(self, payload):
        """按原始 JSON 发送登录请求，供缺失字段等协议场景使用。"""
        return self.client.post('/login', json=payload)

    def captcha(self):
        return self.client.get('/captchaImage')

    def get_info(self):
        return self.client.get('/getInfo')

    def get_routers(self):
        return self.client.get('/getRouters')

    def logout(self):
        return self.client.post('/logout')

    def close(self):
        self.client.close()
