import allure
import pytest
from playwright.sync_api import sync_playwright
from common.utils import read_yaml
from api.login_api import LoginApi
from pages.login_page import LoginPage
from pages.user_page import UserPage
from api.user_api import UserApi
import os
import time
import logging
logging.basicConfig(level=logging.INFO)
config = read_yaml('config/config.yaml')

@pytest.fixture(scope="session")
def login_token():
    api = LoginApi()
    data = api.login(config['admin']['username'],config['admin']['password'])
    assert data is not None, "登录接口返回为空"
    assert 'token' in data, f"登录失败，返回: {data}"
    yield data['token']


@pytest.fixture(scope='session')
def browser():
    pw = sync_playwright().start()
    try:
        headless = os.getenv('CI', '') != ''
        b = pw.chromium.launch(headless=headless)
        yield b
        b.close()
    finally:
        pw.stop()

@pytest.fixture
def page(browser):
    p = browser.new_page()
    yield p
    p.close()

@pytest.fixture
def login(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login(config['admin']['username'], config['admin']['password'])
    page.wait_for_url('**/index')
    return page

@pytest.fixture
def user_page(login):
    login.goto(config['ui_url'] + '/system/user')
    return UserPage(login)

@pytest.fixture
def cleanup_user(login_token):
    usernames = []
    yield usernames
    api = UserApi(login_token)
    for name in usernames:
        result = api.list_user(name)
        if result['rows']:
            api.delete_user(result['rows'][0]['userId'])

@pytest.fixture
def create_user(login_token):
    api = UserApi(login_token)
    username = f'del_test_{int(time.time())}'
    api.add_user(username, '待删除用户')
    result = api.list_user(username)
    user_id = result['rows'][0]['userId']
    yield {'username': username, 'user_id': user_id}
    check = api.list_user(username)
    if check['rows']:
        api.delete_user(user_id)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request):
    yield
    page = request.node.funcargs.get("page") or request.node.funcargs.get("login")
    if page and hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        allure.attach(page.screenshot(), name="失败截图", attachment_type=allure.attachment_type.PNG)











