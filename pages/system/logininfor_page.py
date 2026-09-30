from common.ui import click_and_wait_list


class LogininforPage:
    """系统管理 / 登录日志页面对象。"""

    def __init__(self, page):
        self.page = page

        # 查询区
        self.search_form = page.locator('.el-form--inline')
        self.search_ip_input = self.search_form.get_by_placeholder('请输入登录地址')
        self.search_username_input = self.search_form.get_by_placeholder(
            '请输入用户名称'
        )
        self.search_status_input = self.search_form.get_by_placeholder('登录状态')
        self.search_button = self.search_form.get_by_role('button', name='搜索')
        self.reset_button = self.search_form.get_by_role('button', name='重置')

        # 工具栏。删除和要解锁的账号都要先勾选；清空会删掉全部登录日志
        self.toolbar = page.locator('.el-row.mb8').first
        self.delete_button = self.toolbar.get_by_role('button', name='删除')
        self.clean_button = self.toolbar.get_by_role('button', name='清空')
        self.unlock_button = self.toolbar.get_by_role('button', name='解锁')
        self.export_button = self.toolbar.get_by_role('button', name='导出')

        # 日志列表
        self.table = page.locator('.el-table')
        self.table_headers = self.table.locator('thead')
        self.table_body = self.table.locator('.el-table__body-wrapper tbody')
        self.pagination_total = page.locator('.el-pagination__total')
        self.loading_mask = page.locator('.el-table .el-loading-mask').first

        # 二次确认与全局反馈
        self.confirm_box = page.locator('.el-message-box')
        self.confirm_button = self.confirm_box.get_by_role('button', name='确定')
        self.message = page.locator('.el-message__content').last

    def row_by_username(self, username):
        return self.table_body.locator('tr').filter(has_text=username)

    def row_by_info_id(self, info_id):
        return self.table_body.locator('tr').filter(
            has=self.page.locator('.cell').get_by_text(str(info_id), exact=True)
        )

    # 按用户名称搜索并等待本次查询返回
    def search(self, username):
        self.search_username_input.fill(username)
        click_and_wait_list(
            self.page,
            self.search_button,
            self.loading_mask,
            '/monitor/logininfor/list',
            {'userName': username},
        )

    def reset_search(self):
        click_and_wait_list(
            self.page,
            self.reset_button,
            self.loading_mask,
            '/monitor/logininfor/list',
            {'userName': ''},
        )

    def _select_row(self, username):
        self.row_by_username(username).first.locator('.el-checkbox__inner').click()

    # 勾选该账号的一条失败登录后解锁。解锁只清缓存，不删日志
    def unlock_user(self, username):
        self._select_row(username)
        self.unlock_button.click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: (
                '/monitor/logininfor/unlock/' in response.url
                and response.request.method == 'GET'
            )
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')

    # 勾选该账号的一条记录后删除。只删这一条，不点清空
    def delete_login_log(self, username):
        self._select_row(username)
        self.delete_button.click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: (
                '/monitor/logininfor/' in response.url
                and response.request.method == 'DELETE'
                and '/unlock/' not in response.url
                and not response.url.rstrip('/').endswith('/clean')
            )
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')
        self.loading_mask.wait_for(state='hidden')
