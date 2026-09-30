from common.ui import click_and_wait_list, row_operation_button, wait_dialog_settled


class RolePage:
    """系统管理 / 角色管理页面对象。"""

    def __init__(self, page):
        self.page = page

        # 查询区
        self.search_form = page.locator('.el-form--inline')
        self.search_role_name_input = self.search_form.get_by_placeholder(
            '请输入角色名称'
        )
        self.search_role_key_input = self.search_form.get_by_placeholder(
            '请输入权限字符'
        )
        self.search_status_input = self.search_form.get_by_placeholder('角色状态')
        self.search_button = self.search_form.get_by_role('button', name='搜索')
        self.reset_button = self.search_form.get_by_role('button', name='重置')

        # 角色列表工具栏
        self.toolbar = page.locator('.el-row.mb8').first
        self.add_button = self.toolbar.get_by_role('button', name='新增')
        self.edit_button = self.toolbar.get_by_role('button', name='修改')
        self.delete_button = self.toolbar.get_by_role('button', name='删除')
        self.export_button = self.toolbar.get_by_role('button', name='导出')

        # 角色列表
        self.table = page.locator('.el-table')
        self.table_headers = self.table.locator('thead')
        self.table_body = self.table.locator('.el-table__body-wrapper tbody')
        self.pagination_total = page.locator('.el-pagination__total')
        self.loading_mask = page.locator('.el-table .el-loading-mask').first

        # 新增角色弹窗
        self.add_dialog = page.get_by_role('dialog', name='添加角色')
        self.add_role_name_input = self.add_dialog.get_by_placeholder(
            '请输入角色名称'
        )
        self.add_role_key_input = self.add_dialog.get_by_placeholder(
            '请输入权限字符'
        )
        self.add_role_sort_input = self.add_dialog.locator(
            '.el-input-number input'
        )
        self.add_confirm_button = self.add_dialog.get_by_role(
            'button', name='确 定'
        )
        self.add_form_error = self.add_dialog.locator('.el-form-item__error')

        # 修改角色弹窗
        self.edit_dialog = page.get_by_role('dialog', name='修改角色')
        self.edit_role_name_input = self.edit_dialog.get_by_placeholder(
            '请输入角色名称'
        )
        self.edit_confirm_button = self.edit_dialog.get_by_role(
            'button', name='确 定'
        )

        # 更多操作菜单
        self.data_scope_menu_item = page.get_by_text(
            '数据权限', exact=True
        ).filter(visible=True)
        self.assign_user_menu_item = page.get_by_text(
            '分配用户', exact=True
        ).filter(visible=True)

        # 分配数据权限弹窗。权限范围下拉没有 placeholder，按表单项标签定位。
        self.data_scope_dialog = page.get_by_role('dialog', name='分配数据权限')
        self.data_scope_select = self.data_scope_dialog.locator(
            '.el-form-item'
        ).filter(
            has=page.get_by_text('权限范围', exact=True)
        ).locator('.el-select')
        self.self_data_scope_option = page.get_by_text(
            '仅本人数据权限', exact=True
        ).filter(visible=True)
        self.data_scope_confirm_button = self.data_scope_dialog.get_by_role(
            'button', name='确 定'
        )

        # 二次确认与全局反馈
        self.confirm_box = page.locator('.el-message-box')
        self.confirm_button = self.confirm_box.get_by_role('button', name='确定')
        self.message = page.locator('.el-message__content').last

    def row_by_role_name(self, role_name):
        return self.table_body.locator('tr').filter(has_text=role_name)

    def status_switch(self, role_name):
        return self.row_by_role_name(role_name).locator('.el-switch')

    # .el-switch 容器自身就是可访问 switch，直接用于状态断言和点击
    def status_checkbox(self, role_name):
        return self.status_switch(role_name)

    # 行内是修改、删除和更多三个图标按钮
    def edit_row_button(self, role_name):
        return row_operation_button(self.row_by_role_name(role_name), 0)

    def delete_row_button(self, role_name):
        return row_operation_button(self.row_by_role_name(role_name), 1)

    def more_row_button(self, role_name):
        return row_operation_button(self.row_by_role_name(role_name), 2)

    # 只接受带上本次角色名的列表响应，避免吃到进页时的未筛选请求
    def search(self, role_name):
        self.search_role_name_input.fill(role_name)
        click_and_wait_list(
            self.page,
            self.search_button,
            self.loading_mask,
            '/system/role/list',
            {'roleName': role_name},
        )

    def reset_search(self):
        click_and_wait_list(
            self.page,
            self.reset_button,
            self.loading_mask,
            '/system/role/list',
            {'roleName': ''},
        )

    # 填写新增角色的必填字段并提交
    def add_role(self, role_name, role_key, role_sort='10'):
        self.add_button.click()
        self.add_dialog.wait_for(state='visible')
        self.add_role_name_input.fill(role_name)
        self.add_role_key_input.fill(role_key)
        self.add_role_sort_input.fill(role_sort)
        self.add_confirm_button.click()
        wait_dialog_settled(
            self.page,
            self.add_dialog,
            self.add_form_error,
            self.message,
        )

    def edit_role_name(self, role_name, new_role_name):
        self.edit_row_button(role_name).click()
        self.edit_dialog.wait_for(state='visible')
        self.edit_role_name_input.fill(new_role_name)
        with self.page.expect_response(
            lambda response: (
                response.url.rstrip('/').endswith('/system/role')
                and response.request.method == 'PUT'
            )
        ):
            self.edit_confirm_button.click()
        self.edit_dialog.wait_for(state='hidden')

    def change_status(self, role_name):
        self.status_switch(role_name).click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: '/system/role/changeStatus' in response.url
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')

    def delete_role(self, role_name):
        self.delete_row_button(role_name).click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: (
                '/system/role/' in response.url
                and response.request.method == 'DELETE'
            )
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')

    # 展开目标角色的更多操作菜单
    def open_more_actions(self, role_name):
        self.more_row_button(role_name).click()
        self.data_scope_menu_item.wait_for(state='visible')
