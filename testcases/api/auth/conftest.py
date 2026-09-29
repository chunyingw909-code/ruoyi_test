import pytest

from api.auth.login_api import LoginApi


# 登录接口 - 无认证客户端
@pytest.fixture
def login_api():
    api = LoginApi()
    yield api
    api.close()


# 认证资源 - 已携带有效 token 的客户端
@pytest.fixture
def authenticated_login_api(login_token):
    api = LoginApi(login_token)
    yield api
    api.close()
