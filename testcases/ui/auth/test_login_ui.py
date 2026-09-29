import re

import allure
import pytest
from playwright.sync_api import expect

from common.utils import load_config, read_yaml
from pages.auth.login_page import LoginPage


config = load_config()
error_data = read_yaml('data/auth/login_ui.yaml')


@allure.feature('认证模块')
@allure.story('登录页面')
@allure.title('登录页展示完整表单且密码使用掩码输入')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_login_page_elements(page):
    login_page = LoginPage(page)
    login_page.open()

    # 断言：页面身份、表单控件和版权信息完整可见
    expect(page).to_have_title('若依管理系统')
    expect(page).to_have_url(re.compile(r'/login(?:\?|$)'))
    expect(login_page.heading).to_be_visible()
    expect(login_page.username_input).to_be_visible()
    expect(login_page.password_input).to_be_visible()
    expect(login_page.remember_password_label).to_be_visible()
    expect(login_page.login_button).to_be_visible()
    expect(login_page.copyright).to_be_visible()
    # 断言：密码输入框使用 password 类型，避免明文展示
    expect(login_page.password_input).to_have_attribute('type', 'password')


@allure.feature('认证模块')
@allure.story('登录页面')
@allure.title('记住密码选项可以勾选和取消')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_remember_password_can_toggle(page):
    login_page = LoginPage(page)
    login_page.open()

    # 断言：默认未勾选，点击后选中，再次点击后取消
    expect(login_page.remember_password_checkbox).not_to_be_checked()
    login_page.remember_password_label.click()
    expect(login_page.remember_password_checkbox).to_be_checked()
    login_page.remember_password_label.click()
    expect(login_page.remember_password_checkbox).not_to_be_checked()


@allure.feature('认证模块')
@allure.story('登录页面')
@allure.title('正确账号密码登录后进入首页')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_login_success(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login(
        config['admin']['username'],
        config['admin']['password'],
    )

    # 断言：导航到首页，并显示当前登录用户
    expect(page).to_have_url(re.compile(r'/index$'))
    expect(login_page.success_text).to_contain_text('若依')


@allure.feature('认证模块')
@allure.story('登录页面')
@allure.title('登录页面异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
@pytest.mark.parametrize('case', error_data, ids=lambda x: x['desc'])
def test_login_validation(page, case):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login(case['username'], case['password'])

    if case['error_type'] == 'message':
        # 断言：服务端拒绝凭据时展示明确业务错误
        expect(login_page.msg_error).to_have_text(case['expect'])
    else:
        # 断言：空字段逐项展示前端表单校验错误
        expect(login_page.form_errors).to_have_text(case['expect'])
    # 断言：登录失败后仍停留在登录页
    expect(page).to_have_url(re.compile(r'/login(?:\?|$)'))
