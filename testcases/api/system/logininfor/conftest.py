import pytest


# 登录日志接口 - 预置一条失败登录日志
@pytest.fixture
def seeded_login_log(create_failed_login):
    return create_failed_login()


# 登录日志接口 - 预置两条失败登录日志供批量删除使用
@pytest.fixture
def seeded_login_logs(create_failed_login):
    return [create_failed_login(), create_failed_login()]
