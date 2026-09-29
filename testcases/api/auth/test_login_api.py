import allure
import pytest

from api.auth.login_api import LoginApi
from common.utils import load_config, read_yaml


config = load_config()
invalid_login_data = read_yaml('data/auth/login_api.yaml')


@allure.feature('认证模块')
@allure.story('登录接口')
@allure.title('正确账号密码登录后返回 token')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_login_success(login_api):
    result = login_api.login(
        config['admin']['username'],
        config['admin']['password'],
    )

    # 断言：HTTP 与业务状态均成功，并返回非空 token
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['msg'] == '操作成功', result
    assert isinstance(result.get('token'), str) and result['token'], result


@allure.feature('认证模块')
@allure.story('登录接口')
@allure.title('异常登录：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.parametrize('case', invalid_login_data, ids=lambda x: x['desc'])
def test_login_rejected(login_api, case):
    result = login_api.login_payload(case['payload'])

    # 断言：若依以 HTTP 200 返回业务失败，且失败响应不能包含 token
    assert result.status_code == 200, result
    assert result['code'] == case['expected_code'], result
    assert result['msg'] == case['expected_message'], result
    assert not result.get('token'), result


@allure.feature('认证模块')
@allure.story('登录配置')
@allure.title('验证码接口返回与开关一致的数据结构')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.api
def test_captcha_contract(login_api):
    result = login_api.captcha()

    # 断言：验证码配置接口可用，并明确返回布尔开关
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert isinstance(result.get('captchaEnabled'), bool), result
    if result['captchaEnabled']:
        assert result.get('uuid'), result
        assert result.get('img'), result


@allure.feature('认证模块')
@allure.story('认证信息')
@allure.title('有效 token 可以获取当前管理员信息')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_get_info_with_valid_token(authenticated_login_api):
    result = authenticated_login_api.get_info()

    # 断言：有效 token 返回当前账号、角色和权限
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['user']['userName'] == config['admin']['username'], result
    assert 'admin' in result['roles'], result
    assert result['permissions'], result


@allure.feature('认证模块')
@allure.story('认证信息')
@allure.title('{desc}不能获取当前用户信息')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.parametrize(
    'desc,token',
    [('不携带token', None), ('伪造token', 'invalid-token')],
    ids=['不携带token', '伪造token'],
)
def test_get_info_requires_valid_token(desc, token):
    api = LoginApi(token)
    try:
        result = api.get_info()
    finally:
        api.close()

    # 断言：HTTP 请求可达，但业务鉴权明确返回 401
    assert result.status_code == 200, result
    assert result['code'] == 401, result
    assert '认证失败' in result['msg'], result


@allure.feature('认证模块')
@allure.story('认证信息')
@allure.title('有效 token 可以获取当前账号的菜单路由')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_get_routers_with_valid_token(authenticated_login_api):
    result = authenticated_login_api.get_routers()

    # 断言：返回非空路由列表，顶层路由包含名称和路径
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert isinstance(result['data'], list) and result['data'], result
    assert all('name' in route and 'path' in route for route in result['data']), result


@allure.feature('认证模块')
@allure.story('退出登录')
@allure.title('退出登录后原 token 立即失效')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_logout_invalidates_token(login_api):
    login_result = login_api.login(
        config['admin']['username'],
        config['admin']['password'],
    )
    authenticated_api = LoginApi(login_result['token'])
    try:
        logout_result = authenticated_api.logout()
        after_logout = authenticated_api.get_info()
    finally:
        authenticated_api.close()

    # 断言：退出成功，且同一 token 再访问认证资源时被拒绝
    assert logout_result.status_code == 200, logout_result
    assert logout_result['code'] == 200, logout_result
    assert logout_result['msg'] == '退出成功', logout_result
    assert after_logout.status_code == 200, after_logout
    assert after_logout['code'] == 401, after_logout
