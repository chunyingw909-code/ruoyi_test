from common.ui import click_and_wait_list, wait_dialog_settled


class DictDataPage:
    """系统管理 / 字典数据页面对象。"""

    def __init__(self, page):
        self.page = page

        # 查询区
        self.search_form = page.locator('.el-form--inline')
        self.search_label_input = self.search_form.get_by_placeholder(
            '请输入字典标签'
        )
        self.search_status_input = self.search_form.get_by_placeholder('数据状态')
        self.search_button = self.search_form.get_by_role('button', name='搜索')
        self.reset_button = self.search_form.get_by_role('button', name='重置')

        # 字典数据工具栏
        self.toolbar = page.locator('.el-row.mb8').first
        self.add_button = self.toolbar.get_by_role('button', name='新增')
        self.export_button = self.toolbar.get_by_role('button', name='导出')
        self.close_button = self.toolbar.get_by_role('button', name='关闭')

        # 字典数据列表
        self.table = page.locator('.el-table')
        self.table_headers = self.table.locator('thead')
        self.table_body = self.table.locator('.el-table__body-wrapper tbody')
        self.pagination_total = page.locator('.el-pagination__total')
        self.loading_mask = page.locator('.el-table .el-loading-mask').first

        # 新增字典数据弹窗
        self.add_dialog = page.get_by_role('dialog', name='添加字典数据')
        self.add_label_input = self.add_dialog.get_by_placeholder('请输入数据标签')
        self.add_value_input = self.add_dialog.get_by_placeholder('请输入数据键值')
        self.add_sort_input = self.add_dialog.locator('.el-input-number input')
        self.add_confirm_button = self.add_dialog.get_by_role(
            'button', name='确 定'
        )
        self.add_form_error = self.add_dialog.locator('.el-form-item__error')

        # 修改字典数据弹窗
        self.edit_dialog = page.get_by_role('dialog', name='修改字典数据')
        self.edit_label_input = self.edit_dialog.get_by_placeholder('请输入数据标签')
        self.edit_confirm_button = self.edit_dialog.get_by_role(
            'button', name='确 定'
        )

        # 二次确认与全局反馈
        self.confirm_box = page.locator('.el-message-box')
        self.confirm_button = self.confirm_box.get_by_role('button', name='确定')
        self.message = page.locator('.el-message__content').last

    def row_by_label(self, dict_label):
        return self.table_body.locator('tr').filter(has_text=dict_label)

    def edit_row_button(self, dict_label):
        return self.row_by_label(dict_label).get_by_role('button', name='修改')

    def delete_row_button(self, dict_label):
        return self.row_by_label(dict_label).get_by_role('button', name='删除')

    # 按字典标签搜索并等待本次精确查询返回
    def search(self, dict_label):
        self.search_label_input.fill(dict_label)
        click_and_wait_list(
            self.page,
            self.search_button,
            self.loading_mask,
            '/system/dict/data/list',
            {'dictLabel': dict_label},
        )

    def reset_search(self):
        click_and_wait_list(
            self.page,
            self.reset_button,
            self.loading_mask,
            '/system/dict/data/list',
            {'dictLabel': ''},
        )

    # 新增字典数据。sort 为空时清空排序，用来触发前端必填校验
    def add_dict_data(self, dict_label, dict_value, sort='1'):
        self.add_button.click()
        self.add_dialog.wait_for(state='visible')
        self.add_label_input.fill(dict_label)
        self.add_value_input.fill(dict_value)
        self.add_sort_input.fill(sort)
        self.add_confirm_button.click()
        wait_dialog_settled(
            self.page,
            self.add_dialog,
            self.add_form_error,
            self.message,
        )

    def edit_label(self, dict_label, new_label):
        self.edit_row_button(dict_label).click()
        self.edit_dialog.wait_for(state='visible')
        self.edit_label_input.fill(new_label)
        with self.page.expect_response(
            lambda response: (
                response.url.rstrip('/').endswith('/system/dict/data')
                and response.request.method == 'PUT'
            )
        ):
            self.edit_confirm_button.click()
        self.edit_dialog.wait_for(state='hidden')

    def delete_dict_data(self, dict_label):
        self.delete_row_button(dict_label).click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: (
                '/system/dict/data/' in response.url
                and response.request.method == 'DELETE'
            )
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')
