from common.ui import click_and_wait_list, wait_dialog_settled


class PostPage:
    """系统管理 / 岗位管理页面对象。"""

    def __init__(self, page):
        self.page = page

        # 查询区
        self.search_form = page.locator('.el-form--inline')
        self.search_post_code_input = self.search_form.get_by_placeholder(
            '请输入岗位编码'
        )
        self.search_post_name_input = self.search_form.get_by_placeholder(
            '请输入岗位名称'
        )
        self.search_status_input = self.search_form.get_by_placeholder('岗位状态')
        self.search_button = self.search_form.get_by_role('button', name='搜索')
        self.reset_button = self.search_form.get_by_role('button', name='重置')

        # 岗位列表工具栏
        self.toolbar = page.locator('.el-row.mb8').first
        self.add_button = self.toolbar.get_by_role('button', name='新增')
        self.edit_button = self.toolbar.get_by_role('button', name='修改')
        self.delete_button = self.toolbar.get_by_role('button', name='删除')
        self.export_button = self.toolbar.get_by_role('button', name='导出')

        # 岗位列表
        self.table = page.locator('.el-table')
        self.table_headers = self.table.locator('thead')
        self.table_body = self.table.locator('.el-table__body-wrapper tbody')
        self.pagination_total = page.locator('.el-pagination__total')
        self.loading_mask = page.locator('.el-table .el-loading-mask').first

        # 新增岗位弹窗
        self.add_dialog = page.get_by_role('dialog', name='添加岗位')
        self.add_post_name_input = self.add_dialog.get_by_placeholder(
            '请输入岗位名称'
        )
        self.add_post_code_input = self.add_dialog.get_by_placeholder(
            '请输入编码名称'
        )
        self.add_post_sort_input = self.add_dialog.get_by_role('spinbutton')
        self.add_disabled_radio = self.add_dialog.get_by_role(
            'radio', name='停用'
        )
        self.add_remark_input = self.add_dialog.get_by_placeholder('请输入内容')
        self.add_confirm_button = self.add_dialog.get_by_role(
            'button', name='确 定'
        )
        self.add_form_error = self.add_dialog.locator('.el-form-item__error')

        # 修改岗位弹窗
        self.edit_dialog = page.get_by_role('dialog', name='修改岗位')
        self.edit_post_name_input = self.edit_dialog.get_by_placeholder(
            '请输入岗位名称'
        )
        self.edit_disabled_radio = self.edit_dialog.get_by_role(
            'radio', name='停用'
        )
        self.edit_confirm_button = self.edit_dialog.get_by_role(
            'button', name='确 定'
        )

        # 二次确认与全局反馈
        self.confirm_box = page.locator('.el-message-box')
        self.confirm_button = self.confirm_box.get_by_role('button', name='确定')
        self.message = page.locator('.el-message__content').last

    def row_by_post_code(self, post_code):
        return self.table_body.locator('tr').filter(has_text=post_code)

    def edit_row_button(self, post_code):
        return self.row_by_post_code(post_code).get_by_role(
            'button', name='修改'
        )

    def delete_row_button(self, post_code):
        return self.row_by_post_code(post_code).get_by_role(
            'button', name='删除'
        )

    # 按岗位编码搜索并等待本次精确查询返回
    def search(self, post_code):
        self.search_post_code_input.fill(post_code)
        click_and_wait_list(
            self.page,
            self.search_button,
            self.loading_mask,
            '/system/post/list',
            {'postCode': post_code},
        )

    def reset_search(self):
        click_and_wait_list(
            self.page,
            self.reset_button,
            self.loading_mask,
            '/system/post/list',
            {'postCode': ''},
        )

    # 新增岗位并等待表单校验、业务提示或成功关闭弹窗
    def add_post(self, post_name, post_code, post_sort='10', status='0'):
        self.add_button.click()
        self.add_dialog.wait_for(state='visible')
        self.add_post_name_input.fill(post_name)
        self.add_post_code_input.fill(post_code)
        self.add_post_sort_input.fill(post_sort)
        if status == '1':
            self.add_disabled_radio.check()
        self.add_confirm_button.click()
        wait_dialog_settled(
            self.page,
            self.add_dialog,
            self.add_form_error,
            self.message,
        )

    def edit_name_and_disable(self, post_code, post_name):
        self.edit_row_button(post_code).click()
        self.edit_dialog.wait_for(state='visible')
        self.edit_post_name_input.fill(post_name)
        self.edit_disabled_radio.check()
        with self.page.expect_response(
            lambda response: (
                response.url.rstrip('/').endswith('/system/post')
                and response.request.method == 'PUT'
            )
        ):
            self.edit_confirm_button.click()
        self.edit_dialog.wait_for(state='hidden')

    def delete_post(self, post_code):
        self.delete_row_button(post_code).click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: (
                '/system/post/' in response.url
                and response.request.method == 'DELETE'
            )
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')
