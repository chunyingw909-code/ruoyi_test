class UserPage:
    def __init__(self, page):
        self.page = page

        self.add_button = self.page.get_by_role('button', name='新增')

        self.dialog = self.page.get_by_role('dialog', name='添加用户')
        self.dialog_nickname = self.dialog.get_by_placeholder('请输入用户昵称')
        self.dialog_username = self.dialog.get_by_placeholder('请输入用户名称')
        self.dialog_confirm = self.dialog.get_by_role('button', name='确 定')

        self.search_input = self.page.locator('.el-form--inline').get_by_placeholder('请输入用户名称')
        self.search_button = self.page.get_by_role('button', name='搜索')

        self.table_username = self.page.locator('.link-type')

        self.delete_confirm = self.page.locator('.el-message-box__btns').get_by_role('button', name='确定')

    def user_link(self, username):
            return self.page.locator('.link-type').get_by_text(username,exact=True)

    def search(self, username):
        self.search_input.fill(username)
        self.search_button.click()
        self.page.locator('.el-loading-mask').wait_for(state='hidden', timeout=5000)

    def add_user(self, username, nickname):
        self.add_button.click()
        self.dialog_nickname.fill(nickname)
        self.dialog_username.fill(username)
        self.dialog_confirm.click()
        # self.page.wait_for_timeout(1000)

    def delete_user(self, username):
        self.search(username)
        self.page.locator('.link-type', has_text=username).locator('xpath=ancestor::tr').get_by_text('删除').click()
        self.delete_confirm.click()