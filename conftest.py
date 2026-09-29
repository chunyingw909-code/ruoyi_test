import os
import logging
import uuid

import pytest
from playwright.sync_api import sync_playwright

from api.auth.login_api import LoginApi
from api.system.role_api import RoleApi
from api.system.user_api import UserApi
from common.utils import load_config
from pages.auth.login_page import LoginPage

logging.basicConfig(level=logging.INFO)
config = load_config()


# 全局认证 - API 登录令牌
@pytest.fixture(scope="session")
def login_token():
    api = LoginApi()
    try:
        data = api.login(config['admin']['username'], config['admin']['password'])
        assert data is not None, "登录接口返回为空"
        assert data.get('code') == 200, f"登录失败，返回: {data}"
        assert data.get('token'), f"登录成功响应中没有 token: {data}"
        yield data['token']
    finally:
        api.close()


# 跨 API/UI - 生成隔离的用户管理测试账号
@pytest.fixture
def unique_username():
    """生成只属于当前用例的测试用户名。"""
    return f'AUTOTEST-{uuid.uuid4().hex[:8]}'


# 跨 API/UI - 用户管理接口客户端
@pytest.fixture
def user_api(login_token):
    """提供用户管理 API，并在用例结束后关闭 Session。"""
    api = UserApi(login_token)
    yield api
    api.close()


# 跨 API/UI - 角色管理接口客户端
@pytest.fixture
def role_api(login_token):
    """提供角色管理 API，并在用例结束后关闭 Session。"""
    api = RoleApi(login_token)
    yield api
    api.close()


# 跨 API/UI - 生成隔离的角色名称和权限字符
@pytest.fixture
def unique_role_identity():
    suffix = uuid.uuid4().hex[:8]
    return {
        'role_name': f'AUTOTEST-role-{suffix}',
        'role_key': f'autotest_{suffix}',
    }


# 跨 API/UI - 角色登记与安全清理
@pytest.fixture
def track_test_role(role_api):
    """只登记 AUTOTEST 角色，teardown 按精确 roleId 清理。"""
    tracked = {}

    def _track(role_name):
        if not role_name.startswith('AUTOTEST-role-'):
            raise ValueError(f'只允许登记 AUTOTEST 测试角色，收到: {role_name!r}')
        result = role_api.list_roles(roleName=role_name)
        rows = [
            row for row in result.get('rows', [])
            if row.get('roleName') == role_name
        ]
        for row in rows:
            tracked[row['roleId']] = role_name
        return rows

    yield _track

    for role_id, role_name in reversed(list(tracked.items())):
        try:
            result = role_api.list_roles(
                roleName='AUTOTEST-role-',
                pageNum=1,
                pageSize=1000,
            )
            current = next(
                (
                    row for row in result.get('rows', [])
                    if row.get('roleId') == role_id
                ),
                {},
            )
            safe_to_delete = (
                current.get('roleId') == role_id
                and current.get('roleName', '').startswith('AUTOTEST-role-')
                and current.get('roleKey', '').startswith('autotest_')
            )
            if safe_to_delete:
                role_api.delete_role(role_id)
        except Exception as exc:
            logging.warning(
                '清理测试角色失败: roleName=%s, roleId=%s, error=%s',
                role_name,
                role_id,
                exc,
            )


# 跨 API/UI - 通过接口创建并自动登记测试角色
@pytest.fixture
def create_test_role(role_api, track_test_role):
    def _create(role_name=None, role_key=None, **kwargs):
        suffix = uuid.uuid4().hex[:8]
        role_name = role_name or f'AUTOTEST-role-{suffix}'
        role_key = role_key or f'autotest_{suffix}'
        result = role_api.add_role(role_name, role_key, **kwargs)
        assert result.status_code == 200, result
        assert result.get('code') == 200, f'测试角色创建失败: {result}'

        rows = track_test_role(role_name)
        assert len(rows) == 1, f'未找到唯一测试角色: {rows}'
        return {
            'role_name': role_name,
            'role_key': role_key,
            'role_id': rows[0]['roleId'],
            'row': rows[0],
        }

    return _create


# 跨 API/UI - 测试用户登记与安全清理
@pytest.fixture
def track_test_user(user_api):
    """按精确用户名登记 AUTOTEST 用户，teardown 仅按其 userId 清理。

    该入口拒绝登记空用户名或固定业务账号，从机制上避免模糊查询后误删真实数据。
    """
    tracked = {}

    def _track(username):
        if not username.startswith('AUTOTEST-'):
            raise ValueError(f'只允许登记 AUTOTEST 测试用户，收到: {username!r}')
        result = user_api.list_user(username)
        rows = [
            row for row in result.get('rows', [])
            if row.get('userName') == username
        ]
        for row in rows:
            tracked[row['userId']] = username
        return rows

    yield _track

    for user_id, username in reversed(list(tracked.items())):
        try:
            result = user_api.list_user(username)
            still_exists = any(
                row.get('userName') == username and row.get('userId') == user_id
                for row in result.get('rows', [])
            )
            if still_exists:
                user_api.delete_user(user_id)
        except Exception as exc:
            logging.warning(
                '清理测试用户失败: username=%s, userId=%s, error=%s',
                username,
                user_id,
                exc,
            )


# 跨 API/UI - 通过接口创建并自动登记测试用户
@pytest.fixture
def create_test_user(user_api, track_test_user):
    def _create(username=None, nickname='自动化测试用户', **kwargs):
        username = username or f'AUTOTEST-{uuid.uuid4().hex[:8]}'
        payload = {'password': 'AutoTest123', 'status': '0'}
        payload.update(kwargs)
        result = user_api.add_user(username, nickname, **payload)
        assert result.status_code == 200, result
        assert result.get('code') == 200, f'测试用户创建失败: {result}'

        rows = track_test_user(username)
        assert len(rows) == 1, f'未找到唯一测试用户: {rows}'
        return {
            'username': username,
            'user_id': rows[0]['userId'],
            'password': payload['password'],
            'row': rows[0],
        }

    return _create


# 跨 API/UI - 导入用固定测试账号的前置清理与事后登记
@pytest.fixture
def import_test_username(user_api, track_test_user):
    username = 'AUTOTEST-import-fixture'
    stale_rows = [
        row for row in user_api.list_user(username).get('rows', [])
        if row.get('userName') == username
    ]
    for row in stale_rows:
        user_api.delete_user(row['userId'])

    yield username
    track_test_user(username)


# 全局浏览器 - CI 环境无头，本地默认有头
@pytest.fixture(scope='session')
def browser():
    pw = sync_playwright().start()
    b = None
    try:
        headless = os.getenv('CI', '') != ''
        b = pw.chromium.launch(headless=headless)
        yield b
    finally:
        if b is not None:
            b.close()
        pw.stop()


# 每条 UI 用例使用独立页面，避免登录态和页面状态互相污染
@pytest.fixture
def page(browser):
    p = browser.new_page(viewport={'width': 1440, 'height': 900})
    yield p
    p.close()


# 已登录页面 - 非登录模块复用，不重复验证登录表单
@pytest.fixture
def authenticated_page(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login(config['admin']['username'], config['admin']['password'])
    page.wait_for_url('**/index')
    return page


# 将用例执行结果暴露给失败截图 Fixture
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)





