import re

from common.utils import load_config


class LoginPage:
    """登录页面对象。"""

    def __init__(self, page):
        self.page = page
        config = load_config()
        self.url = config['ui_url']

        # 登录表单
        self.heading = page.get_by_role('heading', name='若依管理系统')
        self.username_input = page.get_by_placeholder('账号')
        self.password_input = page.get_by_placeholder('密码')
        self.remember_password_label = page.get_by_text('记住密码', exact=True)
        self.remember_password_checkbox = page.get_by_role('checkbox', name='记住密码')
        self.login_button = page.get_by_role('button', name='登 录')
        self.copyright = page.get_by_text(
            re.compile(r'Copyright © 2018-\d{4} RuoYi\. All Rights Reserved\.')
        )

        # 登录结果
        self.success_text = page.locator('.user-nickname')
        self.form_errors = page.locator('.el-form-item__error')
        self.msg_error = page.locator('.el-message__content')

    def open(self):
        self.page.goto(self.url)

    # 填写账号、密码并提交登录表单
    def login(self, username, password):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
