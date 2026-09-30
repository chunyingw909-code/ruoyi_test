from common.ui import click_and_wait_list, row_operation_button, wait_dialog_settled


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
        self.loading_mask = page.locator('.el-table .el-loading-mask').first

        # 添加用户弹窗
        self.add_dialog = page.get_by_role('dialog', name='添加用户')
        self.add_nickname_input = self.add_dialog.get_by_placeholder('请输入用户昵称')
        self.add_username_input = self.add_dialog.get_by_placeholder('请输入用户名称')
        self.add_password_input = self.add_dialog.get_by_placeholder('请输入用户密码')
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

    # .el-switch 容器自身就是可访问 switch，直接用于状态断言和点击
    def status_checkbox(self, username):
        return self.status_switch(username)

    # 行内修改、删除是图标按钮，顺序与用户管理模板一致
    def edit_row_button(self, username):
        return row_operation_button(self.row_by_username(username), 0)

    def delete_row_button(self, username):
        return row_operation_button(self.row_by_username(username), 1)

    # 只接受带上本次用户名的列表响应，避免吃到进页时的未筛选请求
    def search(self, username):
        self.search_username_input.fill(username)
        click_and_wait_list(
            self.page,
            self.search_button,
            self.loading_mask,
            '/system/user/list',
            {'userName': username},
        )

    def reset_search(self):
        click_and_wait_list(
            self.page,
            self.reset_button,
            self.loading_mask,
            '/system/user/list',
            {'userName': ''},
        )

    # 密码是必填项，而且初始密码是异步填入的，提交前写死一个已知密码
    def add_user(self, username, nickname, password='AutoTest123'):
        self.add_button.click()
        self.add_dialog.wait_for(state='visible')
        self.add_nickname_input.fill(nickname)
        self.add_username_input.fill(username)
        if password is not None:
            self.add_password_input.fill(password)
        self.add_confirm_button.click()
        wait_dialog_settled(
            self.page,
            self.add_dialog,
            self.add_form_error,
            self.message,
        )

    def edit_nickname(self, username, nickname):
        self.edit_row_button(username).click()
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
        self.delete_row_button(username).click()
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
