import allure
import pytest
from playwright.sync_api import expect

from common.utils import read_yaml


add_error_data = read_yaml('data/system/notice_ui_errors.yaml')


@allure.feature('系统管理')
@allure.story('通知公告页面')
@allure.title('通知公告页展示查询、工具栏和列表核心元素')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_notice_page_structure(notice_page):
    # 断言：公告页具备查询、新增和主要列表字段
    expect(notice_page.search_title_input).to_be_visible()
    expect(notice_page.search_creator_input).to_be_visible()
    expect(notice_page.search_type_input).to_be_visible()
    expect(notice_page.add_button).to_be_visible()
    expect(notice_page.table_headers).to_contain_text('公告标题')
    expect(notice_page.table_headers).to_contain_text('公告类型')
    expect(notice_page.table_headers).to_contain_text('状态')
    expect(notice_page.table_headers).to_contain_text('创建者')
    expect(notice_page.table_headers).to_contain_text('操作')


@allure.feature('系统管理')
@allure.story('通知公告页面')
@allure.title('按公告标题筛选后可以重置查询条件')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_search_and_reset_notice(notice_page, seeded_ui_notice):
    notice_page.search(seeded_ui_notice['notice_title'])

    # 断言：精确筛选只显示目标公告
    expect(notice_page.row_by_title(seeded_ui_notice['notice_title'])).to_have_count(1)
    expect(notice_page.pagination_total).to_contain_text('共 1 条')

    notice_page.reset_search()

    # 断言：重置后公告标题查询框被清空
    expect(notice_page.search_title_input).to_have_value('')


@allure.feature('系统管理')
@allure.story('通知公告页面')
@allure.title('通过页面正常新增通知')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_add_notice_success(notice_page, unique_notice_title, track_test_notice):
    notice_page.add_notice(unique_notice_title, '通知')
    notice_page.search(unique_notice_title)

    try:
        row = notice_page.row_by_title(unique_notice_title)
        # 断言：新增后列表展示目标标题，类型为通知
        expect(row).to_have_count(1)
        expect(row).to_contain_text('通知')
    finally:
        track_test_notice(unique_notice_title)


@allure.feature('系统管理')
@allure.story('通知公告页面')
@allure.title('新增公告表单异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_notice_validation(notice_page, track_test_notice, case):
    try:
        notice_page.add_notice(case['notice_title'], case['notice_type'])
        # 断言：缺少必填字段时弹窗展示字段级校验提示
        expect(notice_page.add_form_error).to_have_text(case['expect'])
    finally:
        if case['notice_title'].startswith('AUTOTEST-notice-'):
            track_test_notice(case['notice_title'])


@allure.feature('系统管理')
@allure.story('通知公告页面')
@allure.title('通过页面修改公告标题并关闭公告')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_edit_notice(notice_page, notice_api, seeded_ui_notice, track_test_notice):
    old_title = seeded_ui_notice['notice_title']
    new_title = f'{old_title}-updated'
    notice_page.search(old_title)
    notice_page.edit_title_and_close(old_title, new_title)
    track_test_notice(new_title)
    notice_page.search(new_title)
    detail = notice_api.get_notice(seeded_ui_notice['notice_id'])

    # 断言：列表显示新标题和关闭状态，接口详情也得到已落库的新值
    row = notice_page.row_by_title(new_title)
    expect(row).to_have_count(1)
    expect(row).to_contain_text('关闭')
    assert detail['data']['noticeTitle'] == new_title, detail
    assert detail['data']['status'] == '1', detail


@allure.feature('系统管理')
@allure.story('通知公告页面')
@allure.title('通过页面确认删除公告')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_delete_notice(notice_page, notice_api, seeded_ui_notice, oper_log_guard):
    title = seeded_ui_notice['notice_title']
    oper_log_guard.register_url(f"/system/notice/{seeded_ui_notice['notice_id']}")
    notice_page.search(title)
    notice_page.delete_notice(title)
    rows = [
        row for row in notice_api.list_notices(noticeTitle=title).get('rows', [])
        if row.get('noticeTitle') == title
    ]

    # 断言：删除后页面和接口均不存在目标公告
    expect(notice_page.row_by_title(title)).to_have_count(0)
    assert rows == [], rows
