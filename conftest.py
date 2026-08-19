import pytest
from playwright.sync_api import sync_playwright
from common.utils import read_yaml
from api.login_api import LoginApi
from pages.login_page import LoginPage
from pages.user_page import UserPage
from api.user_api import UserApi
import os
config = read_yaml('config/config.yaml')

@pytest.fixture(scope="session")
def login_token():
    api = LoginApi()
    data = api.login(config['admin']['username'],config['admin']['password'])
    yield data['token']


@pytest.fixture(scope='session')
def browser():
    pw = sync_playwright().start()
    headless = os.getenv('CI', '') != ''
    b = pw.chromium.launch(headless=headless)
    yield b
    b.close()
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











