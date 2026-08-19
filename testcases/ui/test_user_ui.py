import allure
import time
from playwright.sync_api import expect
import pytest
from common.utils import read_yaml


@allure.feature('用户管理模块')
@allure.story('新增用户-正向')
@allure.title('正常新增用户')
def test_add_user_success(user_page, cleanup_user):
    username = f'test_{int(time.time())}'
    cleanup_user.append(username)

    with allure.step('新增用户'):
        user_page.add_user(username, '测试001')

    with allure.step('搜索确认用户存在'):
        user_page.search(username)
        expect(user_page.user_link(username)).to_have_count(1)


add_error_data = read_yaml('data/user_add_ui_error.yaml')


@allure.feature('用户管理模块')
@allure.story('新增用户-异常')
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_user_error(user_page, case):
    user_page.add_user(case['username'], case['nickname'])
    if case['error_type'] == 'form':
        expect(user_page.dialog_form_error).to_have_text(case['expect'])
    else:
        expect(user_page.msg_error).to_have_text(case['expect'])