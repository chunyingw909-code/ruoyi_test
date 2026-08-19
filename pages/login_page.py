from common.utils import read_yaml


class LoginPage():
    def __init__(self,page):
        self.page = page
        config = read_yaml('config/config.yaml')
        self.url = config['ui_url']

        self.username_input = self.page.get_by_placeholder('账号')
        self.password_input = self.page.get_by_placeholder('密码')
        self.login_button = self.page.get_by_role('button',name='登 录')

        self.success_text = self.page.locator('.user-nickname')
        self.form_error = self.page.locator('.el-form-item__error')
        self.msg_error = self.page.locator('.el-message__content')


    def open(self):
        self.page.goto(self.url)

    def login(self, username, password):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()




