from common.ui import click_and_wait_list, wait_dialog_settled


class DictPage:
    """系统管理 / 字典管理页面对象。"""

    def __init__(self, page):
        self.page = page

        # 查询区
        self.search_form = page.locator('.el-form--inline')
        self.search_dict_name_input = self.search_form.get_by_placeholder(
            '请输入字典名称'
        )
        self.search_dict_type_input = self.search_form.get_by_placeholder(
            '请输入字典类型'
        )
        self.search_status_input = self.search_form.get_by_placeholder('字典状态')
        self.search_button = self.search_form.get_by_role('button', name='搜索')
        self.reset_button = self.search_form.get_by_role('button', name='重置')

        # 字典类型工具栏
        self.toolbar = page.locator('.el-row.mb8').first
        self.add_button = self.toolbar.get_by_role('button', name='新增')
        self.export_button = self.toolbar.get_by_role('button', name='导出')
        self.refresh_button = self.toolbar.get_by_role('button', name='刷新缓存')

        # 字典类型列表
        self.table = page.locator('.el-table')
        self.table_headers = self.table.locator('thead')
        self.table_body = self.table.locator('.el-table__body-wrapper tbody')
        self.pagination_total = page.locator('.el-pagination__total')
        self.loading_mask = page.locator('.el-table .el-loading-mask').first

        # 新增字典类型弹窗
        self.add_dialog = page.get_by_role('dialog', name='添加字典类型')
        self.add_dict_name_input = self.add_dialog.get_by_placeholder(
            '请输入字典名称'
        )
        self.add_dict_type_input = self.add_dialog.get_by_placeholder(
            '请输入字典类型'
        )
        self.add_confirm_button = self.add_dialog.get_by_role(
            'button', name='确 定'
        )
        self.add_form_error = self.add_dialog.locator('.el-form-item__error')

        # 修改字典类型弹窗
        self.edit_dialog = page.get_by_role('dialog', name='修改字典类型')
        self.edit_dict_name_input = self.edit_dialog.get_by_placeholder(
            '请输入字典名称'
        )
        self.edit_confirm_button = self.edit_dialog.get_by_role(
            'button', name='确 定'
        )

        # 二次确认与全局反馈
        self.confirm_box = page.locator('.el-message-box')
        self.confirm_button = self.confirm_box.get_by_role('button', name='确定')
        self.message = page.locator('.el-message__content').last

    def row_by_dict_type(self, dict_type):
        return self.table_body.locator('tr').filter(has_text=dict_type)

    def edit_row_button(self, dict_type):
        return self.row_by_dict_type(dict_type).get_by_role('button', name='修改')

    def data_list_button(self, dict_type):
        return self.row_by_dict_type(dict_type).get_by_role('button', name='列表')

    def delete_row_button(self, dict_type):
        return self.row_by_dict_type(dict_type).get_by_role('button', name='删除')

    # 按字典类型搜索并等待本次精确查询返回
    def search(self, dict_type):
        self.search_dict_type_input.fill(dict_type)
        click_and_wait_list(
            self.page,
            self.search_button,
            self.loading_mask,
            '/system/dict/type/list',
            {'dictType': dict_type},
        )

    def reset_search(self):
        click_and_wait_list(
            self.page,
            self.reset_button,
            self.loading_mask,
            '/system/dict/type/list',
            {'dictType': ''},
        )

    # 新增字典类型并等待表单校验、业务提示或成功关闭弹窗
    def add_dict_type(self, dict_name, dict_type):
        self.add_button.click()
        self.add_dialog.wait_for(state='visible')
        self.add_dict_name_input.fill(dict_name)
        self.add_dict_type_input.fill(dict_type)
        self.add_confirm_button.click()
        wait_dialog_settled(
            self.page,
            self.add_dialog,
            self.add_form_error,
            self.message,
        )

    def edit_dict_name(self, dict_type, dict_name):
        self.edit_row_button(dict_type).click()
        self.edit_dialog.wait_for(state='visible')
        self.edit_dict_name_input.fill(dict_name)
        with self.page.expect_response(
            lambda response: (
                response.url.rstrip('/').endswith('/system/dict/type')
                and response.request.method == 'PUT'
            )
        ):
            self.edit_confirm_button.click()
        self.edit_dialog.wait_for(state='hidden')

    def delete_dict_type(self, dict_type):
        self.delete_row_button(dict_type).click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: (
                '/system/dict/type/' in response.url
                and response.request.method == 'DELETE'
                and not response.url.rstrip('/').endswith('/refreshCache')
            )
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')

    # 从字典类型行进入字典数据页，并等数据列表返回
    def open_data_list(self, dict_type):
        with self.page.expect_response(
            lambda response: response.url.find('/system/dict/data/list') >= 0
            and response.request.method == 'GET'
        ):
            self.data_list_button(dict_type).click()

    def refresh_cache(self):
        with self.page.expect_response(
            lambda response: (
                response.url.rstrip('/').endswith('/system/dict/type/refreshCache')
                and response.request.method == 'DELETE'
            )
        ):
            self.refresh_button.click()
