from common.ui import click_and_wait_list, wait_dialog_settled


class NoticePage:
    """系统管理 / 通知公告页面对象。"""

    def __init__(self, page):
        self.page = page

        # 查询区
        self.search_form = page.locator('.el-form--inline')
        self.search_title_input = self.search_form.get_by_placeholder('请输入公告标题')
        self.search_creator_input = self.search_form.get_by_placeholder(
            '请输入操作人员'
        )
        self.search_type_input = self.search_form.get_by_placeholder('公告类型')
        self.search_button = self.search_form.get_by_role('button', name='搜索')
        self.reset_button = self.search_form.get_by_role('button', name='重置')

        # 公告工具栏
        self.toolbar = page.locator('.el-row.mb8').first
        self.add_button = self.toolbar.get_by_role('button', name='新增')

        # 公告列表
        self.table = page.locator('.el-table')
        self.table_headers = self.table.locator('thead')
        self.table_body = self.table.locator('.el-table__body-wrapper tbody')
        self.pagination_total = page.locator('.el-pagination__total')
        self.loading_mask = page.locator('.el-table .el-loading-mask').first

        # 新增公告弹窗
        self.add_dialog = page.get_by_role('dialog', name='添加公告')
        self.add_title_input = self.add_dialog.get_by_placeholder('请输入公告标题')
        self.add_type_select = self.add_dialog.locator('.el-form-item').filter(
            has=page.get_by_text('公告类型', exact=True)
        ).locator('.el-select')
        self.add_confirm_button = self.add_dialog.get_by_role(
            'button', name='确 定'
        )
        self.add_form_error = self.add_dialog.locator('.el-form-item__error')

        # 修改公告弹窗
        self.edit_dialog = page.get_by_role('dialog', name='修改公告')
        self.edit_title_input = self.edit_dialog.get_by_placeholder('请输入公告标题')
        self.edit_closed_radio = self.edit_dialog.get_by_role('radio', name='关闭')
        self.edit_confirm_button = self.edit_dialog.get_by_role(
            'button', name='确 定'
        )

        # 二次确认与全局反馈
        self.confirm_box = page.locator('.el-message-box')
        self.confirm_button = self.confirm_box.get_by_role('button', name='确定')
        self.message = page.locator('.el-message__content').last

    def row_by_title(self, notice_title):
        return self.table_body.locator('tr').filter(has_text=notice_title)

    def edit_row_button(self, notice_title):
        return self.row_by_title(notice_title).get_by_role('button', name='修改')

    def delete_row_button(self, notice_title):
        return self.row_by_title(notice_title).get_by_role('button', name='删除')

    # 下拉层挂在 body 上，只点当前可见的选项
    def _choose_visible_option(self, select, label):
        select.click()
        self.page.locator('.el-select-dropdown__item:visible').filter(
            has_text=label
        ).first.click()

    # 按公告标题搜索并等待本次精确查询返回
    def search(self, notice_title):
        self.search_title_input.fill(notice_title)
        click_and_wait_list(
            self.page,
            self.search_button,
            self.loading_mask,
            '/system/notice/list',
            {'noticeTitle': notice_title},
        )

    def reset_search(self):
        click_and_wait_list(
            self.page,
            self.reset_button,
            self.loading_mask,
            '/system/notice/list',
            {'noticeTitle': ''},
        )

    # 新增公告。notice_type 为空时不选类型，用来触发前端必填校验
    def add_notice(self, notice_title, notice_type='通知'):
        self.add_button.click()
        self.add_dialog.wait_for(state='visible')
        self.add_title_input.fill(notice_title)
        if notice_type:
            self._choose_visible_option(self.add_type_select, notice_type)
        self.add_confirm_button.click()
        wait_dialog_settled(
            self.page,
            self.add_dialog,
            self.add_form_error,
            self.message,
        )

    def edit_title_and_close(self, notice_title, new_title):
        self.edit_row_button(notice_title).click()
        self.edit_dialog.wait_for(state='visible')
        self.edit_title_input.fill(new_title)
        self.edit_closed_radio.check()
        with self.page.expect_response(
            lambda response: (
                response.url.rstrip('/').endswith('/system/notice')
                and response.request.method == 'PUT'
            )
        ):
            self.edit_confirm_button.click()
        self.edit_dialog.wait_for(state='hidden')

    def delete_notice(self, notice_title):
        self.delete_row_button(notice_title).click()
        self.confirm_box.wait_for(state='visible')
        with self.page.expect_response(
            lambda response: (
                '/system/notice/' in response.url
                and response.request.method == 'DELETE'
            )
        ):
            self.confirm_button.click()
        self.confirm_box.wait_for(state='hidden')
