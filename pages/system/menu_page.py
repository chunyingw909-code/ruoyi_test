from common.ui import click_and_wait_list, wait_dialog_settled


class MenuPage:
    """系统管理 / 菜单管理页面对象。"""

    def __init__(self, page):
        self.page = page

        # 查询区
        self.search_form = page.locator('.el-form--inline')
        self.search_menu_name_input = self.search_form.get_by_placeholder(
            '请输入菜单名称'
        )
        self.search_status_input = self.search_form.get_by_placeholder('菜单状态')
        self.search_button = self.search_form.get_by_role('button', name='搜索')
        self.reset_button = self.search_form.get_by_role('button', name='重置')

        # 菜单工具栏
        self.toolbar = page.locator('.el-row.mb8').first
        self.add_button = self.toolbar.get_by_role('button', name='新增')
        self.save_sort_button = self.toolbar.get_by_role('button', name='保存排序')
        self.toggle_expand_button = self.toolbar.get_by_role(
            'button', name='展开/折叠'
        )

        # 菜单树形列表
        self.table = page.locator('.el-table')
        self.table_headers = self.table.locator('thead')
        self.table_body = self.table.locator('.el-table__body-wrapper tbody')
        self.loading_mask = page.locator('.el-table .el-loading-mask').first

        # 新增菜单弹窗
        self.add_dialog = page.get_by_role('dialog', name='添加菜单')
        self.add_menu_name_input = self.add_dialog.get_by_placeholder(
            '请输入菜单名称'
        )
        self.add_path_input = self.add_dialog.get_by_placeholder('请输入路由地址')
        self.add_order_input = self.add_dialog.get_by_role('spinbutton')
        self.add_confirm_button = self.add_dialog.get_by_role(
            'button', name='确 定'
        )
        self.add_form_error = self.add_dialog.locator('.el-form-item__error')

        # 修改菜单弹窗
        self.edit_dialog = page.get_by_role('dialog', name='修改菜单')
        self.edit_menu_name_input = self.edit_dialog.get_by_placeholder(
            '请输入菜单名称'
        )
        self.edit_confirm_button = self.edit_dialog.get_by_role(
            'button', name='确 定'
        )

        # 二次确认与全局反馈
        self.confirm_box = page.locator('.el-message-box')
        self.confirm_button = self.confirm_box.get_by_role('button', name='确定')
        self.message = page.locator('.el-message__content').last

    def row_by_menu_name(self, menu_name):
        return self.table_body.locator('tr').filter(has_text=menu_name)

    # 菜单行操作使用稳定的可访问名称
    def edit_row_button(self, menu_name):
        return self.row_by_menu_name(menu_name).get_by_role(
            'button', name='修改'
        )

    def delete_row_button(self, menu_name):
        return self.row_by_menu_name(menu_name).get_by_role(
            'button', name='删除'
        )

    # 按菜单名称搜索并等待本次精确查询返回
    def search(self, menu_name):
        self.search_menu_name_input.fill(menu_name)
        click_and_wait_list(
            self.page,
            self.search_button,
            self.loading_mask,
            '/system/menu/list',
            {'menuName': menu_name},
        )

    def reset_search(self):
        click_and_wait_list(
            self.page,
            self.reset_button,
            self.loading_mask,
            '/system/menu/list',
            {'menuName': ''},
        )

    # 新增一个顶级目录菜单并等待提交结果稳定
    def add_menu(self, menu_name, path, order='10'):
        self.add_button.click()
        self.add_dialog.wait_for(state='visible')
        self.add_menu_name_input.fill(menu_name)
        self.add_path_input.fill(path)
        self.add_order_input.fill(order)
        self.add_confirm_button.click()
        wait_dialog_settled(
            self.page,
            self.add_dialog,
            self.add_form_error,
            self.message,
        )

    def edit_menu_name(self, menu_name, new_menu_name):
        self.edit_row_button(menu_name).click()
        self.edit_dialog.wait_for(state='visible')
        self.edit_menu_name_input.fill(new_menu_name)
        with self.page.expect_response(
            lambda response: (
                response.url.rstrip('/').endswith('/system/menu')
                and response.request.method == 'PUT'
            )
        ):
            self.edit_confirm_button.click()
        self.edit_dialog.wait_for(state='hidden')

    def delete_menu(self, menu_name):
        self.delete_row_button(menu_name).click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: (
                '/system/menu/' in response.url
                and response.request.method == 'DELETE'
            )
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')
