import pytest
from common.utils import read_yaml
from pages.login_page import LoginPage
from playwright.sync_api import expect

data = read_yaml('data/login_ui_data.yaml')

@pytest.mark.parametrize('case',data,ids=lambda x: x['desc'] )
def test_login(page,case):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login(case['username'],case['password'])

    if case['scene'] == 'success':
        expect(login_page.success_text).to_have_text(case['expect'])
    elif case['scene'] == 'msg_error':
        expect(login_page.msg_error).to_have_text(case['expect'])
    else:
        expect(login_page.form_error).to_have_text(case['expect'])

