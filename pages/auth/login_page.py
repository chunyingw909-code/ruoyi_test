import re

from common.captcha import recognize_captcha
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
        self.captcha_input = page.get_by_placeholder('验证码')
        self.captcha_image = page.locator('.login-code-img')
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

    # 等验证码接口返回后再看表单，避免开关还没决定输入框是否渲染
    def open(self):
        with self.page.expect_response(
            lambda response: (
                response.request.method == 'GET'
                and 'captchaImage' in response.url
            )
        ) as response_info:
            self.page.goto(self.url)
        if response_info.value.json().get('captchaEnabled'):
            self.captcha_input.wait_for(state='visible')

    # 验证码开着时先识别当前图片。识别错了会换图重试，其它错误留给用例断言。
    def login(self, username, password):
        self.username_input.fill(username)
        self.password_input.fill(password)
        for _ in range(3):
            previous_src = self._fill_captcha()
            self.login_button.click()
            outcome = self._wait_login_outcome()
            if outcome != 'captcha':
                return
            self._wait_next_captcha(previous_src)
            self.msg_error.first.wait_for(state='hidden', timeout=5000)

    def _fill_captcha(self):
        if self.captcha_input.count() == 0 or not self.captcha_input.is_visible():
            return None
        self.captcha_image.wait_for(state='visible')
        previous_src = self.captcha_image.get_attribute('src')
        self.captcha_input.fill(recognize_captcha(self.captcha_image.screenshot()))
        return previous_src

    def _wait_next_captcha(self, previous_src):
        if not previous_src:
            return
        self.page.wait_for_function(
            """(previous) => {
                const img = document.querySelector('.login-code-img');
                return img && img.src && img.src !== previous;
            }""",
            arg=previous_src,
            timeout=5000,
        )

    def _wait_login_outcome(self, timeout_ms=8000):
        deadline_ms = timeout_ms
        elapsed = 0
        while elapsed < deadline_ms:
            if '/login' not in self.page.url:
                return 'success'
            if self.form_errors.count() and self.form_errors.first.is_visible():
                return 'form'
            if self.msg_error.count() and self.msg_error.first.is_visible():
                text = self.msg_error.first.inner_text()
                if '验证码' in text:
                    return 'captcha'
                return 'message'
            self.page.wait_for_timeout(100)
            elapsed += 100
        return 'timeout'
