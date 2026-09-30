import allure
import pytest
from playwright.sync_api import expect

from common.xlsx_utils import xlsx_text_values


@allure.feature('系统管理')
@allure.story('登录日志页面')
@allure.title('登录日志页展示查询、工具栏和列表核心元素')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_logininfor_page_structure(logininfor_page):
    # 断言：登录日志页具备查询条件、导出和主要列表字段；未勾选时不能删除或解锁
    expect(logininfor_page.search_ip_input).to_be_visible()
    expect(logininfor_page.search_username_input).to_be_visible()
    expect(logininfor_page.search_status_input).to_be_visible()
    expect(logininfor_page.delete_button).to_be_disabled()
    expect(logininfor_page.clean_button).to_be_visible()
    expect(logininfor_page.unlock_button).to_be_disabled()
    expect(logininfor_page.export_button).to_be_visible()
    expect(logininfor_page.table_headers).to_contain_text('访问编号')
    expect(logininfor_page.table_headers).to_contain_text('用户名称')
    expect(logininfor_page.table_headers).to_contain_text('登录地址')
    expect(logininfor_page.table_headers).to_contain_text('登录状态')
    expect(logininfor_page.table_headers).to_contain_text('操作信息')
    expect(logininfor_page.table_headers).to_contain_text('登录日期')


@allure.feature('系统管理')
@allure.story('登录日志页面')
@allure.title('按用户名称筛选后可以重置查询条件')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_search_and_reset_login_log(logininfor_page, seeded_ui_login_log):
    username = seeded_ui_login_log['username']
    logininfor_page.search(username)
    row = logininfor_page.row_by_username(username)

    # 断言：精确筛选只显示该账号的失败登录
    expect(row).to_have_count(len(seeded_ui_login_log['rows']))
    expect(logininfor_page.pagination_total).to_contain_text(
        f"共 {len(seeded_ui_login_log['rows'])} 条"
    )
    expect(row.first).to_contain_text('失败')
    expect(row.first).to_contain_text('用户不存在/密码错误')

    logininfor_page.reset_search()

    # 断言：重置后用户名称查询框被清空
    expect(logininfor_page.search_username_input).to_have_value('')


@allure.feature('系统管理')
@allure.story('登录日志页面')
@allure.title('通过页面解锁选中的登录账号')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_unlock_login_user(logininfor_page, seeded_ui_login_log):
    username = seeded_ui_login_log['username']
    logininfor_page.search(username)
    logininfor_page.unlock_user(username)

    # 断言：页面提示该账号已解锁，失败登录记录仍在
    expect(logininfor_page.message).to_contain_text('解锁成功')
    expect(logininfor_page.message).to_contain_text(username)
    expect(logininfor_page.row_by_username(username).first).to_be_visible()


@allure.feature('系统管理')
@allure.story('登录日志页面')
@allure.title('通过页面按用户名称导出 Excel')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_export_login_log(logininfor_page, seeded_ui_login_log, oper_log_guard):
    logininfor_page.search(seeded_ui_login_log['username'])
    oper_log_guard.register_marker(seeded_ui_login_log['username'])

    with logininfor_page.page.expect_download() as download_info:
        logininfor_page.export_button.click()
    download = download_info.value
    values = xlsx_text_values(download.path().read_bytes())

    # 断言：浏览器下载 XLSX，内容包含该账号和失败原因
    assert download.suggested_filename.endswith('.xlsx')
    assert seeded_ui_login_log['username'] in values, values
    assert '用户不存在/密码错误' in values, values


@allure.feature('系统管理')
@allure.story('登录日志页面')
@allure.title('通过页面确认删除选中的登录日志')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_delete_login_log(logininfor_page, logininfor_api, seeded_ui_login_log):
    username = seeded_ui_login_log['username']
    info_id = seeded_ui_login_log['info_id']
    logininfor_page.search(username)
    logininfor_page.delete_login_log(username)
    rows = [
        row for row in logininfor_api.list_logs(userName=username).get('rows', [])
        if row.get('infoId') == info_id
    ]

    # 断言：删除后页面和接口均不存在这条访问编号
    expect(logininfor_page.message).to_have_text('删除成功')
    expect(logininfor_page.row_by_info_id(info_id)).to_have_count(0)
    assert rows == [], rows
