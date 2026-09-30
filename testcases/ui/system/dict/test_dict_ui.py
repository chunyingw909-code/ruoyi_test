import re

import allure
import pytest
from playwright.sync_api import expect

from common.utils import read_yaml
from common.xlsx_utils import xlsx_text_values
from pages.system.dict_data_page import DictDataPage


add_error_data = read_yaml('data/system/dict_ui_errors.yaml')


@allure.feature('系统管理')
@allure.story('字典管理页面')
@allure.title('字典管理页展示查询、工具栏和列表核心元素')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_dict_page_structure(dict_page):
    # 断言：字典类型页具备查询、新增、导出、刷新缓存和主要列表字段
    expect(dict_page.search_dict_name_input).to_be_visible()
    expect(dict_page.search_dict_type_input).to_be_visible()
    expect(dict_page.search_status_input).to_be_visible()
    expect(dict_page.add_button).to_be_visible()
    expect(dict_page.export_button).to_be_visible()
    expect(dict_page.refresh_button).to_be_visible()
    expect(dict_page.table_headers).to_contain_text('字典编号')
    expect(dict_page.table_headers).to_contain_text('字典名称')
    expect(dict_page.table_headers).to_contain_text('字典类型')
    expect(dict_page.table_headers).to_contain_text('状态')
    expect(dict_page.table_headers).to_contain_text('操作')


@allure.feature('系统管理')
@allure.story('字典管理页面')
@allure.title('按字典类型筛选后可以重置查询条件')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_search_and_reset_dict_type(dict_page, seeded_ui_dict_type):
    dict_page.search(seeded_ui_dict_type['dict_type'])

    # 断言：精确筛选只显示目标字典类型
    expect(dict_page.row_by_dict_type(seeded_ui_dict_type['dict_type'])).to_have_count(1)
    expect(dict_page.pagination_total).to_contain_text('共 1 条')

    dict_page.reset_search()

    # 断言：重置后字典类型查询框被清空
    expect(dict_page.search_dict_type_input).to_have_value('')


@allure.feature('系统管理')
@allure.story('字典管理页面')
@allure.title('通过页面正常新增字典类型')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_add_dict_type_success(dict_page, unique_dict_identity, track_test_dict_type):
    identity = unique_dict_identity
    dict_page.add_dict_type(identity['dict_name'], identity['dict_type'])
    dict_page.search(identity['dict_type'])

    try:
        row = dict_page.row_by_dict_type(identity['dict_type'])
        # 断言：新增后列表展示目标字典名称和类型
        expect(row).to_have_count(1)
        expect(row).to_contain_text(identity['dict_name'])
    finally:
        track_test_dict_type(identity['dict_name'])


@allure.feature('系统管理')
@allure.story('字典管理页面')
@allure.title('新增字典类型表单异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_dict_type_validation(dict_page, track_test_dict_type, case):
    try:
        dict_page.add_dict_type(case['dict_name'], case['dict_type'])
        if case['error_type'] == 'form':
            # 断言：缺少必填字段时弹窗展示字段级校验提示
            expect(dict_page.add_form_error).to_have_text(case['expect'])
        else:
            # 断言：字典类型格式不合法时展示服务端拒绝原因
            expect(dict_page.message).to_have_text(case['expect'])
    finally:
        if case['dict_name'].startswith('AUTOTEST-dict-'):
            track_test_dict_type(case['dict_name'])


@allure.feature('系统管理')
@allure.story('字典管理页面')
@allure.title('通过页面修改字典名称')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_edit_dict_type(dict_page, dict_type_api, seeded_ui_dict_type):
    dict_type = seeded_ui_dict_type['dict_type']
    new_name = f"{seeded_ui_dict_type['dict_name']}-updated"
    dict_page.search(dict_type)
    dict_page.edit_dict_name(dict_type, new_name)
    dict_page.search(dict_type)
    detail = dict_type_api.get_dict_type(seeded_ui_dict_type['dict_id'])

    # 断言：列表显示新名称，接口详情也得到已落库的新值
    expect(dict_page.row_by_dict_type(dict_type)).to_contain_text(new_name)
    assert detail['data']['dictName'] == new_name, detail


@allure.feature('系统管理')
@allure.story('字典管理页面')
@allure.title('通过页面确认删除字典类型')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_delete_dict_type(dict_page, dict_type_api, seeded_ui_dict_type, oper_log_guard):
    dict_type = seeded_ui_dict_type['dict_type']
    oper_log_guard.register_url(f"/system/dict/type/{seeded_ui_dict_type['dict_id']}")
    dict_page.search(dict_type)
    dict_page.delete_dict_type(dict_type)
    rows = [
        row for row in dict_type_api.list_dict_types(dictType=dict_type).get('rows', [])
        if row.get('dictType') == dict_type
    ]

    # 断言：删除后页面和接口均不存在目标字典类型
    expect(dict_page.row_by_dict_type(dict_type)).to_have_count(0)
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('字典管理页面')
@allure.title('通过页面按字典类型导出 Excel')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_export_dict_type(dict_page, seeded_ui_dict_type):
    dict_page.search(seeded_ui_dict_type['dict_type'])

    with dict_page.page.expect_download() as download_info:
        dict_page.export_button.click()
    download = download_info.value
    values = xlsx_text_values(download.path().read_bytes())

    # 断言：浏览器下载 XLSX，内容包含本次筛选的目标字典
    assert download.suggested_filename.endswith('.xlsx')
    assert seeded_ui_dict_type['dict_name'] in values, values
    assert seeded_ui_dict_type['dict_type'] in values, values


@allure.feature('系统管理')
@allure.story('字典管理页面')
@allure.title('刷新字典缓存后展示成功提示')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_refresh_dict_cache(dict_page):
    dict_page.refresh_cache()

    # 断言：刷新缓存后页面提示成功
    expect(dict_page.message).to_have_text('刷新成功')


@allure.feature('系统管理')
@allure.story('字典管理页面')
@allure.title('从字典类型行进入对应的字典数据页')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_open_dict_data_from_row(dict_page, seeded_ui_dict_type):
    dict_page.search(seeded_ui_dict_type['dict_type'])
    dict_page.open_data_list(seeded_ui_dict_type['dict_type'])
    data_page = DictDataPage(dict_page.page)

    # 断言：进入该字典类型的数据页，并展示字典数据查询区
    expect(dict_page.page).to_have_url(
        re.compile(rf"/system/dict-data/index/{seeded_ui_dict_type['dict_id']}")
    )
    expect(data_page.search_label_input).to_be_visible()
    expect(data_page.add_button).to_be_visible()
