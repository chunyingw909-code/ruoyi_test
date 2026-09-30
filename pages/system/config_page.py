from common.ui import click_and_wait_list, wait_dialog_settled


class ConfigPage:
    """系统管理 / 参数设置页面对象。"""

    def __init__(self, page):
        self.page = page

        # 查询区
        self.search_form = page.locator('.el-form--inline')
        self.search_name_input = self.search_form.get_by_placeholder('请输入参数名称')
        self.search_key_input = self.search_form.get_by_placeholder('请输入参数键名')
        self.search_builtin_input = self.search_form.get_by_placeholder('系统内置')
        self.search_button = self.search_form.get_by_role('button', name='搜索')
        self.reset_button = self.search_form.get_by_role('button', name='重置')

        # 参数工具栏
        self.toolbar = page.locator('.el-row.mb8').first
        self.add_button = self.toolbar.get_by_role('button', name='新增')
        self.export_button = self.toolbar.get_by_role('button', name='导出')
        self.refresh_button = self.toolbar.get_by_role('button', name='刷新缓存')

        # 参数列表
        self.table = page.locator('.el-table')
        self.table_headers = self.table.locator('thead')
        self.table_body = self.table.locator('.el-table__body-wrapper tbody')
        self.pagination_total = page.locator('.el-pagination__total')
        self.loading_mask = page.locator('.el-table .el-loading-mask').first

        # 新增参数弹窗。默认「系统内置=是」删不掉，提交前改成否
        self.add_dialog = page.get_by_role('dialog', name='添加参数')
        self.add_name_input = self.add_dialog.get_by_placeholder('请输入参数名称')
        self.add_key_input = self.add_dialog.get_by_placeholder('请输入参数键名')
        self.add_value_input = self.add_dialog.get_by_placeholder('请输入参数键值')
        self.add_not_builtin_radio = self.add_dialog.get_by_role('radio', name='否')
        self.add_confirm_button = self.add_dialog.get_by_role(
            'button', name='确 定'
        )
        self.add_form_error = self.add_dialog.locator('.el-form-item__error')

        # 修改参数弹窗
        self.edit_dialog = page.get_by_role('dialog', name='修改参数')
        self.edit_value_input = self.edit_dialog.get_by_placeholder('请输入参数键值')
        self.edit_confirm_button = self.edit_dialog.get_by_role(
            'button', name='确 定'
        )

        # 二次确认与全局反馈
        self.confirm_box = page.locator('.el-message-box')
        self.confirm_button = self.confirm_box.get_by_role('button', name='确定')
        self.message = page.locator('.el-message__content').last

    def row_by_key(self, config_key):
        return self.table_body.locator('tr').filter(has_text=config_key)

    def edit_row_button(self, config_key):
        return self.row_by_key(config_key).get_by_role('button', name='修改')

    def delete_row_button(self, config_key):
        return self.row_by_key(config_key).get_by_role('button', name='删除')

    # 按参数键名搜索并等待本次精确查询返回
    def search(self, config_key):
        self.search_key_input.fill(config_key)
        click_and_wait_list(
            self.page,
            self.search_button,
            self.loading_mask,
            '/system/config/list',
            {'configKey': config_key},
        )

    def reset_search(self):
        click_and_wait_list(
            self.page,
            self.reset_button,
            self.loading_mask,
            '/system/config/list',
            {'configKey': ''},
        )

    # 新增非内置参数，避免内置参数无法删除
    def add_config(self, config_name, config_key, config_value):
        self.add_button.click()
        self.add_dialog.wait_for(state='visible')
        self.add_name_input.fill(config_name)
        self.add_key_input.fill(config_key)
        self.add_value_input.fill(config_value)
        self.add_not_builtin_radio.check()
        self.add_confirm_button.click()
        wait_dialog_settled(
            self.page,
            self.add_dialog,
            self.add_form_error,
            self.message,
        )

    def edit_value(self, config_key, config_value):
        self.edit_row_button(config_key).click()
        self.edit_dialog.wait_for(state='visible')
        self.edit_value_input.fill(config_value)
        with self.page.expect_response(
            lambda response: (
                response.url.rstrip('/').endswith('/system/config')
                and response.request.method == 'PUT'
            )
        ):
            self.edit_confirm_button.click()
        self.edit_dialog.wait_for(state='hidden')

    def delete_config(self, config_key):
        self.delete_row_button(config_key).click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: (
                '/system/config/' in response.url
                and response.request.method == 'DELETE'
                and not response.url.rstrip('/').endswith('/refreshCache')
            )
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')

    def refresh_cache(self):
        with self.page.expect_response(
            lambda response: (
                response.url.rstrip('/').endswith('/system/config/refreshCache')
                and response.request.method == 'DELETE'
            )
        ):
            self.refresh_button.click()
