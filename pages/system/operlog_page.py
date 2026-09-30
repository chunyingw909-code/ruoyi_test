from common.ui import click_and_wait_list


class OperlogPage:
    """系统管理 / 操作日志页面对象。"""

    def __init__(self, page):
        self.page = page

        # 查询区
        self.search_form = page.locator('.el-form--inline')
        self.search_ip_input = self.search_form.get_by_placeholder('请输入操作地址')
        self.search_title_input = self.search_form.get_by_placeholder('请输入系统模块')
        self.search_operator_input = self.search_form.get_by_placeholder(
            '请输入操作人员'
        )
        self.search_type_input = self.search_form.get_by_placeholder('操作类型')
        self.search_status_input = self.search_form.get_by_placeholder('操作状态')
        self.search_button = self.search_form.get_by_role('button', name='搜索')
        self.reset_button = self.search_form.get_by_role('button', name='重置')

        # 工具栏。删除要先勾选；清空会删掉全部日志，用例不要点
        self.toolbar = page.locator('.el-row.mb8').first
        self.delete_button = self.toolbar.get_by_role('button', name='删除')
        self.clean_button = self.toolbar.get_by_role('button', name='清空')
        self.export_button = self.toolbar.get_by_role('button', name='导出')

        # 日志列表
        self.table = page.locator('.el-table')
        self.table_headers = self.table.locator('thead')
        self.table_body = self.table.locator('.el-table__body-wrapper tbody')
        self.pagination_total = page.locator('.el-pagination__total')
        self.loading_mask = page.locator('.el-table .el-loading-mask').first

        # 详情与二次确认
        self.detail_dialog = page.get_by_role('dialog', name='操作日志详细')
        self.confirm_box = page.locator('.el-message-box')
        self.confirm_button = self.confirm_box.get_by_role('button', name='确定')
        self.message = page.locator('.el-message__content').last

    def row_by_oper_id(self, oper_id):
        return self.table_body.locator('tr').filter(
            has=self.page.locator('.cell').get_by_text(str(oper_id), exact=True)
        )

    def detail_button(self, oper_id):
        return self.row_by_oper_id(oper_id).get_by_role('button', name='详细')

    # 按系统模块搜索并等待本次查询返回
    def search(self, title):
        self.search_title_input.fill(title)
        click_and_wait_list(
            self.page,
            self.search_button,
            self.loading_mask,
            '/monitor/operlog/list',
            {'title': title},
        )

    def reset_search(self):
        click_and_wait_list(
            self.page,
            self.reset_button,
            self.loading_mask,
            '/monitor/operlog/list',
            {'title': ''},
        )

    # 详情取自当前行，不会再请求接口
    def open_detail(self, oper_id):
        self.detail_button(oper_id).click()
        self.detail_dialog.wait_for(state='visible')

    # 勾选指定日志编号后删除。只删这一条，不点清空
    def delete_oper_log(self, oper_id):
        self.row_by_oper_id(oper_id).locator('.el-checkbox__inner').click()
        self.delete_button.click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: (
                '/monitor/operlog/' in response.url
                and response.request.method == 'DELETE'
                and not response.url.rstrip('/').endswith('/clean')
            )
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')
        self.loading_mask.wait_for(state='hidden')
