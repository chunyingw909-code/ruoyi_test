class UserPage:
    """系统管理 / 用户管理页面对象。"""

    def __init__(self, page):
        self.page = page

        # 查询区
        self.search_form = page.locator('.el-form--inline')
        self.search_username_input = self.search_form.get_by_placeholder(
            '请输入用户名称'
        )
        self.search_phone_input = self.search_form.get_by_placeholder(
            '请输入手机号码'
        )
        self.search_button = self.search_form.get_by_role('button', name='搜索')
        self.reset_button = self.search_form.get_by_role('button', name='重置')

        # 用户列表工具栏
        self.toolbar = page.locator('.el-row.mb8').first
        self.add_button = self.toolbar.get_by_role('button', name='新增')
        self.edit_button = self.toolbar.get_by_role('button', name='修改')
        self.delete_button = self.toolbar.get_by_role('button', name='删除')
        self.import_button = self.toolbar.get_by_role('button', name='导入')
        self.export_button = self.toolbar.get_by_role('button', name='导出')

        # 用户列表
        self.table = page.locator('.el-table')
        self.table_headers = self.table.locator('thead')
        self.table_body = self.table.locator('.el-table__body-wrapper tbody')
        self.table_usernames = self.table.locator('.link-type')
        self.pagination_total = page.locator('.el-pagination__total')
        self.loading_mask = page.locator('.el-loading-mask')

        # 添加用户弹窗
        self.add_dialog = page.get_by_role('dialog', name='添加用户')
        self.add_nickname_input = self.add_dialog.get_by_placeholder('请输入用户昵称')
        self.add_username_input = self.add_dialog.get_by_placeholder('请输入用户名称')
        self.add_confirm_button = self.add_dialog.get_by_role('button', name='确 定')
        self.add_form_error = self.add_dialog.locator('.el-form-item__error')

        # 修改用户弹窗
        self.edit_dialog = page.get_by_role('dialog', name='修改用户')
        self.edit_nickname_input = self.edit_dialog.get_by_placeholder('请输入用户昵称')
        self.edit_confirm_button = self.edit_dialog.get_by_role('button', name='确 定')

        # 用户导入弹窗
        self.import_dialog = page.get_by_role('dialog', name='用户导入')
        self.import_file_input = self.import_dialog.locator('input[type="file"]')
        self.import_update_checkbox = self.import_dialog.get_by_role('checkbox')
        self.import_template_link = self.import_dialog.get_by_text('下载模板')
        self.import_confirm_button = self.import_dialog.get_by_role(
            'button', name='确 定'
        )
        self.import_result_box = page.get_by_role('dialog', name='导入结果')
        self.import_result_confirm_button = self.import_result_box.get_by_role(
            'button', name='确定'
        )

        # 二次确认与全局反馈
        self.confirm_box = page.locator('.el-message-box')
        self.confirm_button = self.confirm_box.get_by_role('button', name='确定')
        self.message = page.locator('.el-message__content').last

    # 用户名依赖运行时参数，因此保留为动态定位方法
    def user_link(self, username):
        return self.table_usernames.get_by_text(username, exact=True)

    def row_by_username(self, username):
        return self.table_body.locator('tr').filter(has_text=username)

    def status_switch(self, username):
        return self.row_by_username(username).locator('.el-switch')

    def status_checkbox(self, username):
        return self.status_switch(username).get_by_role('checkbox')

    # 搜索并等待用户列表接口完成
    def search(self, username):
        self.search_username_input.fill(username)
        with self.page.expect_response(
            lambda response: '/system/user/list' in response.url
        ):
            self.search_button.click()
        self.loading_mask.wait_for(state='hidden', timeout=5000)

    def reset_search(self):
        with self.page.expect_response(
            lambda response: '/system/user/list' in response.url
        ):
            self.reset_button.click()
        self.loading_mask.wait_for(state='hidden', timeout=5000)

    # 打开新增弹窗，填写必填字段并提交
    def add_user(self, username, nickname):
        self.add_button.click()
        self.add_nickname_input.fill(nickname)
        self.add_username_input.fill(username)
        self.add_confirm_button.click()

    def edit_nickname(self, username, nickname):
        self.row_by_username(username).get_by_role(
            'button', name='修改'
        ).click()
        self.edit_dialog.wait_for(state='visible')
        self.edit_nickname_input.fill(nickname)
        with self.page.expect_response(
            lambda response: (
                response.url.rstrip('/').endswith('/system/user')
                and response.request.method == 'PUT'
            )
        ):
            self.edit_confirm_button.click()
        self.edit_dialog.wait_for(state='hidden')

    def change_status(self, username):
        self.status_switch(username).click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: '/system/user/changeStatus' in response.url
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')

    def delete_user(self, username):
        self.row_by_username(username).get_by_role(
            'button', name='删除'
        ).click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: (
                '/system/user/' in response.url
                and response.request.method == 'DELETE'
            )
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')

    def import_users(self, file_path):
        self.import_button.click()
        self.import_dialog.wait_for(state='visible')
        self.import_file_input.set_input_files(file_path)
        with self.page.expect_response(
            lambda response: '/system/user/importData' in response.url
        ):
            self.import_confirm_button.click()
        self.import_dialog.wait_for(state='hidden')
        self.import_result_box.wait_for(state='visible')
        self.import_result_confirm_button.click()
        self.import_result_box.wait_for(state='hidden')
