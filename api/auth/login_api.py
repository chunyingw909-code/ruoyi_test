import base64

from common.captcha import recognize_captcha
from common.http_client import HttpClient


class LoginApi:
    """认证模块 API。"""

    def __init__(self, token=None):
        self.client = HttpClient(token)

    def login(self, username, password):
        return self.login_payload({'username': username, 'password': password})

    def login_payload(self, payload):
        """按原始 JSON 发送登录请求，供缺失字段等协议场景使用。

        验证码开启时补上当次的 code 和 uuid，否则后端在校验账号之前就返回验证码错误。
        """
        last = None
        for _ in range(3):
            body = self._attach_captcha(payload)
            last = self.client.post('/login', json=body)
            if '验证码' not in str(last.get('msg', '')):
                return last
        return last

    def _attach_captcha(self, payload):
        captcha = self.captcha()
        if not captcha.get('captchaEnabled'):
            return dict(payload)
        body = dict(payload)
        body['uuid'] = captcha['uuid']
        body['code'] = recognize_captcha(base64.b64decode(captcha['img']))
        return body

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
