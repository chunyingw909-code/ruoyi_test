from common.ui import click_and_wait_list, wait_dialog_settled


class DeptPage:
    """系统管理 / 部门管理页面对象。"""

    def __init__(self, page):
        self.page = page

        # 查询区
        self.search_form = page.locator('.el-form--inline')
        self.search_dept_name_input = self.search_form.get_by_placeholder(
            '请输入部门名称'
        )
        self.search_status_input = self.search_form.get_by_placeholder('部门状态')
        self.search_button = self.search_form.get_by_role('button', name='搜索')
        self.reset_button = self.search_form.get_by_role('button', name='重置')

        # 部门工具栏
        self.toolbar = page.locator('.el-row.mb8').first
        self.add_button = self.toolbar.get_by_role('button', name='新增')
        self.save_sort_button = self.toolbar.get_by_role('button', name='保存排序')
        self.toggle_expand_button = self.toolbar.get_by_role(
            'button', name='展开/折叠'
        )

        # 部门树形列表
        self.table = page.locator('.el-table')
        self.table_headers = self.table.locator('thead')
        self.table_body = self.table.locator('.el-table__body-wrapper tbody')
        self.loading_mask = page.locator('.el-table .el-loading-mask').first

        # 新增部门弹窗
        self.add_dialog = page.get_by_role('dialog', name='添加部门')
        self.add_dept_name_input = self.add_dialog.get_by_placeholder(
            '请输入部门名称'
        )
        self.add_order_input = self.add_dialog.get_by_role('spinbutton')
        self.add_leader_input = self.add_dialog.get_by_placeholder('请输入负责人')
        self.add_confirm_button = self.add_dialog.get_by_role(
            'button', name='确 定'
        )
        self.add_form_error = self.add_dialog.locator('.el-form-item__error')

        # 修改部门弹窗
        self.edit_dialog = page.get_by_role('dialog', name='修改部门')
        self.edit_dept_name_input = self.edit_dialog.get_by_placeholder(
            '请输入部门名称'
        )
        self.edit_confirm_button = self.edit_dialog.get_by_role(
            'button', name='确 定'
        )

        # 二次确认与全局反馈
        self.confirm_box = page.locator('.el-message-box')
        self.confirm_button = self.confirm_box.get_by_role('button', name='确定')
        self.message = page.locator('.el-message__content').last

    def row_by_dept_name(self, dept_name):
        return self.table_body.locator('tr').filter(has_text=dept_name)

    def edit_row_button(self, dept_name):
        return self.row_by_dept_name(dept_name).get_by_role(
            'button', name='修改'
        )

    def add_child_button(self, parent_name):
        return self.row_by_dept_name(parent_name).get_by_role(
            'button', name='新增'
        )

    def delete_row_button(self, dept_name):
        return self.row_by_dept_name(dept_name).get_by_role(
            'button', name='删除'
        )

    def search(self, dept_name):
        self.search_dept_name_input.fill(dept_name)
        click_and_wait_list(
            self.page,
            self.search_button,
            self.loading_mask,
            '/system/dept/list',
            {'deptName': dept_name},
        )

    def reset_search(self):
        click_and_wait_list(
            self.page,
            self.reset_button,
            self.loading_mask,
            '/system/dept/list',
            {'deptName': ''},
        )

    # 从目标父部门的行内入口新增子部门
    def add_department(self, parent_name, dept_name, order='10'):
        self.add_child_button(parent_name).click()
        self.add_dialog.wait_for(state='visible')
        self.add_dept_name_input.fill(dept_name)
        self.add_order_input.fill(order)
        self.add_leader_input.fill('自动化测试')
        self.add_confirm_button.click()
        wait_dialog_settled(
            self.page,
            self.add_dialog,
            self.add_form_error,
            self.message,
        )

    def edit_dept_name(self, dept_name, new_dept_name):
        self.edit_row_button(dept_name).click()
        self.edit_dialog.wait_for(state='visible')
        self.edit_dept_name_input.fill(new_dept_name)
        with self.page.expect_response(
            lambda response: (
                response.url.rstrip('/').endswith('/system/dept')
                and response.request.method == 'PUT'
            )
        ):
            self.edit_confirm_button.click()
        self.edit_dialog.wait_for(state='hidden')

    def delete_department(self, dept_name):
        self.delete_row_button(dept_name).click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: (
                '/system/dept/' in response.url
                and response.request.method == 'DELETE'
            )
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')
