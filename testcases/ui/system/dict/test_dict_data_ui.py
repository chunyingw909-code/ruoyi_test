import allure
import pytest
from playwright.sync_api import expect

from common.utils import read_yaml
from common.xlsx_utils import xlsx_text_values


add_error_data = read_yaml('data/system/dict_data_ui_errors.yaml')


@allure.feature('系统管理')
@allure.story('字典数据页面')
@allure.title('字典数据页展示查询、工具栏和列表核心元素')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_dict_data_page_structure(dict_data_page):
    # 断言：字典数据页具备查询、新增、导出、关闭和主要列表字段
    expect(dict_data_page.search_label_input).to_be_visible()
    expect(dict_data_page.search_status_input).to_be_visible()
    expect(dict_data_page.add_button).to_be_visible()
    expect(dict_data_page.export_button).to_be_visible()
    expect(dict_data_page.close_button).to_be_visible()
    expect(dict_data_page.table_headers).to_contain_text('字典编码')
    expect(dict_data_page.table_headers).to_contain_text('字典标签')
    expect(dict_data_page.table_headers).to_contain_text('字典键值')
    expect(dict_data_page.table_headers).to_contain_text('字典排序')
    expect(dict_data_page.table_headers).to_contain_text('状态')
    expect(dict_data_page.table_headers).to_contain_text('操作')


@allure.feature('系统管理')
@allure.story('字典数据页面')
@allure.title('按字典标签筛选后可以重置查询条件')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_search_and_reset_dict_data(dict_data_page, seeded_ui_dict_data):
    dict_data_page.search(seeded_ui_dict_data['dict_label'])

    # 断言：精确筛选只显示目标字典数据
    expect(dict_data_page.row_by_label(seeded_ui_dict_data['dict_label'])).to_have_count(1)
    expect(dict_data_page.pagination_total).to_contain_text('共 1 条')

    dict_data_page.reset_search()

    # 断言：重置后字典标签查询框被清空
    expect(dict_data_page.search_label_input).to_have_value('')


@allure.feature('系统管理')
@allure.story('字典数据页面')
@allure.title('通过页面正常新增字典数据')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_add_dict_data_success(
    dict_data_page,
    seeded_ui_dict_type,
    track_test_dict_data,
):
    label = f"AUTOTEST-label-{seeded_ui_dict_type['dict_type'][-8:]}"
    value = f"autotest_{seeded_ui_dict_type['dict_type'][-8:]}"
    dict_data_page.add_dict_data(label, value)
    dict_data_page.search(label)

    try:
        row = dict_data_page.row_by_label(label)
        # 断言：新增后列表展示目标标签和键值
        expect(row).to_have_count(1)
        expect(row).to_contain_text(value)
    finally:
        track_test_dict_data(seeded_ui_dict_type['dict_type'], label)


@allure.feature('系统管理')
@allure.story('字典数据页面')
@allure.title('新增字典数据表单异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_dict_data_validation(
    dict_data_page,
    seeded_ui_dict_type,
    track_test_dict_data,
    case,
):
    try:
        dict_data_page.add_dict_data(
            case['dict_label'], case['dict_value'], sort=case['sort']
        )
        # 断言：缺少必填字段时弹窗展示字段级校验提示
        expect(dict_data_page.add_form_error).to_have_text(case['expect'])
    finally:
        if str(case['dict_label']).startswith('AUTOTEST-'):
            track_test_dict_data(seeded_ui_dict_type['dict_type'], case['dict_label'])


@allure.feature('系统管理')
@allure.story('字典数据页面')
@allure.title('通过页面修改字典标签')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_edit_dict_data(dict_data_page, dict_data_api, seeded_ui_dict_data):
    old_label = seeded_ui_dict_data['dict_label']
    new_label = f'{old_label}-updated'
    dict_data_page.search(old_label)
    dict_data_page.edit_label(old_label, new_label)
    dict_data_page.search(new_label)
    detail = dict_data_api.get_dict_data(seeded_ui_dict_data['dict_code'])

    # 断言：列表显示新标签，接口详情也得到已落库的新值
    expect(dict_data_page.row_by_label(new_label)).to_have_count(1)
    assert detail['data']['dictLabel'] == new_label, detail


@allure.feature('系统管理')
@allure.story('字典数据页面')
@allure.title('通过页面确认删除字典数据')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_delete_dict_data(dict_data_page, dict_data_api, seeded_ui_dict_data, oper_log_guard):
    label = seeded_ui_dict_data['dict_label']
    oper_log_guard.register_url(f"/system/dict/data/{seeded_ui_dict_data['dict_code']}")
    dict_data_page.search(label)
    dict_data_page.delete_dict_data(label)
    rows = [
        row for row in dict_data_api.list_dict_data(
            dictType=seeded_ui_dict_data['dict_type'], dictLabel=label
        ).get('rows', [])
        if row.get('dictLabel') == label
    ]

    # 断言：删除后页面和接口均不存在目标字典数据
    expect(dict_data_page.row_by_label(label)).to_have_count(0)
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('字典数据页面')
@allure.title('通过页面按当前字典类型导出 Excel')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_export_dict_data(dict_data_page, seeded_ui_dict_data, oper_log_guard):
    dict_data_page.search(seeded_ui_dict_data['dict_label'])
    oper_log_guard.register_marker(seeded_ui_dict_data['dict_type'])

    with dict_data_page.page.expect_download() as download_info:
        dict_data_page.export_button.click()
    download = download_info.value
    values = xlsx_text_values(download.path().read_bytes())

    # 断言：浏览器下载 XLSX，内容包含本次筛选的目标字典数据
    assert download.suggested_filename.endswith('.xlsx')
    assert seeded_ui_dict_data['dict_label'] in values, values
    assert seeded_ui_dict_data['dict_value'] in values, values
