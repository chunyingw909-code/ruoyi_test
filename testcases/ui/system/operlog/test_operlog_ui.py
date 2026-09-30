import allure
import pytest
from playwright.sync_api import expect

from common.xlsx_utils import xlsx_text_values


def xlsx_has(values, text):
    return any(text in value for value in values)


@allure.feature('系统管理')
@allure.story('操作日志页面')
@allure.title('操作日志页展示查询、工具栏和列表核心元素')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_operlog_page_structure(operlog_page):
    # 断言：操作日志页具备查询条件、导出和主要列表字段；未勾选时不能删除
    expect(operlog_page.search_ip_input).to_be_visible()
    expect(operlog_page.search_title_input).to_be_visible()
    expect(operlog_page.search_operator_input).to_be_visible()
    expect(operlog_page.search_type_input).to_be_visible()
    expect(operlog_page.search_status_input).to_be_visible()
    expect(operlog_page.delete_button).to_be_disabled()
    expect(operlog_page.clean_button).to_be_visible()
    expect(operlog_page.export_button).to_be_visible()
    expect(operlog_page.table_headers).to_contain_text('日志编号')
    expect(operlog_page.table_headers).to_contain_text('系统模块')
    expect(operlog_page.table_headers).to_contain_text('操作类型')
    expect(operlog_page.table_headers).to_contain_text('操作人员')
    expect(operlog_page.table_headers).to_contain_text('操作状态')
    expect(operlog_page.table_headers).to_contain_text('操作')


@allure.feature('系统管理')
@allure.story('操作日志页面')
@allure.title('按系统模块筛选后可以重置查询条件')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_search_and_reset_oper_log(operlog_page, seeded_ui_oper_log):
    operlog_page.search('字典类型')
    row = operlog_page.row_by_oper_id(seeded_ui_oper_log['oper_id'])

    # 断言：筛选结果里能看到本次新增字典的日志，类型为新增且状态成功
    expect(row).to_have_count(1)
    expect(row).to_contain_text('字典类型')
    expect(row).to_contain_text('新增')
    expect(row).to_contain_text('成功')

    operlog_page.reset_search()

    # 断言：重置后系统模块查询框被清空
    expect(operlog_page.search_title_input).to_have_value('')


@allure.feature('系统管理')
@allure.story('操作日志页面')
@allure.title('操作日志详情展示本次请求参数')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_operlog_detail(operlog_page, seeded_ui_oper_log):
    operlog_page.search('字典类型')
    operlog_page.open_detail(seeded_ui_oper_log['oper_id'])

    # 断言：详情弹窗展示操作模块和这次新增字典的名称
    expect(operlog_page.detail_dialog).to_be_visible()
    expect(operlog_page.detail_dialog).to_contain_text('字典类型')
    expect(operlog_page.detail_dialog).to_contain_text(
        seeded_ui_oper_log['dict_name']
    )


@allure.feature('系统管理')
@allure.story('操作日志页面')
@allure.title('通过页面按系统模块导出 Excel')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_export_oper_log(operlog_page, seeded_ui_oper_log):
    operlog_page.search('字典类型')

    with operlog_page.page.expect_download() as download_info:
        operlog_page.export_button.click()
    download = download_info.value
    values = xlsx_text_values(download.path().read_bytes())

    # 断言：浏览器下载 XLSX，内容包含本次操作的字典名称
    assert download.suggested_filename.endswith('.xlsx')
    assert xlsx_has(values, seeded_ui_oper_log['dict_name']), values


@allure.feature('系统管理')
@allure.story('操作日志页面')
@allure.title('通过页面确认删除选中的操作日志')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_delete_oper_log(operlog_page, operlog_api, seeded_ui_oper_log):
    oper_id = seeded_ui_oper_log['oper_id']
    operlog_page.search('字典类型')
    operlog_page.delete_oper_log(oper_id)
    rows = [
        row for row in operlog_api.list_logs(
            title='字典类型', pageNum=1, pageSize=100
        ).get('rows', [])
        if row.get('operId') == oper_id
    ]

    # 断言：删除后页面和接口均不存在这条日志
    expect(operlog_page.row_by_oper_id(oper_id)).to_have_count(0)
    assert rows == [], rows
