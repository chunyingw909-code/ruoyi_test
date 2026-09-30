import allure
import pytest
from playwright.sync_api import expect

from common.utils import read_yaml
from common.xlsx_utils import xlsx_text_values


add_error_data = read_yaml('data/system/config_ui_errors.yaml')


@allure.feature('系统管理')
@allure.story('参数设置页面')
@allure.title('参数设置页展示查询、工具栏和列表核心元素')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_config_page_structure(config_page):
    # 断言：参数页具备查询、新增、导出、刷新缓存和主要列表字段
    expect(config_page.search_name_input).to_be_visible()
    expect(config_page.search_key_input).to_be_visible()
    expect(config_page.search_builtin_input).to_be_visible()
    expect(config_page.add_button).to_be_visible()
    expect(config_page.export_button).to_be_visible()
    expect(config_page.refresh_button).to_be_visible()
    expect(config_page.table_headers).to_contain_text('参数名称')
    expect(config_page.table_headers).to_contain_text('参数键名')
    expect(config_page.table_headers).to_contain_text('参数键值')
    expect(config_page.table_headers).to_contain_text('系统内置')
    expect(config_page.table_headers).to_contain_text('操作')


@allure.feature('系统管理')
@allure.story('参数设置页面')
@allure.title('按参数键名筛选后可以重置查询条件')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_search_and_reset_config(config_page, seeded_ui_config):
    config_page.search(seeded_ui_config['config_key'])

    # 断言：精确筛选只显示目标参数
    expect(config_page.row_by_key(seeded_ui_config['config_key'])).to_have_count(1)
    expect(config_page.pagination_total).to_contain_text('共 1 条')

    config_page.reset_search()

    # 断言：重置后参数键名查询框被清空
    expect(config_page.search_key_input).to_have_value('')


@allure.feature('系统管理')
@allure.story('参数设置页面')
@allure.title('通过页面新增非内置参数')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_add_config_success(config_page, unique_config_identity, track_test_config):
    identity = unique_config_identity
    config_page.add_config(identity['config_name'], identity['config_key'], 'ui-value')
    config_page.search(identity['config_key'])

    try:
        row = config_page.row_by_key(identity['config_key'])
        # 断言：新增后列表展示目标参数，并且不是系统内置
        expect(row).to_have_count(1)
        expect(row).to_contain_text(identity['config_name'])
        expect(row).to_contain_text('ui-value')
        expect(row).to_contain_text('否')
    finally:
        track_test_config(identity['config_name'])


@allure.feature('系统管理')
@allure.story('参数设置页面')
@allure.title('新增参数表单异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_config_validation(config_page, track_test_config, case):
    try:
        config_page.add_config(
            case['config_name'], case['config_key'], case['config_value']
        )
        # 断言：缺少必填字段时弹窗展示字段级校验提示
        expect(config_page.add_form_error).to_have_text(case['expect'])
    finally:
        if case['config_name'].startswith('AUTOTEST-config-'):
            track_test_config(case['config_name'])


@allure.feature('系统管理')
@allure.story('参数设置页面')
@allure.title('通过页面修改参数键值')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_edit_config(config_page, config_api, seeded_ui_config):
    config_key = seeded_ui_config['config_key']
    config_page.search(config_key)
    config_page.edit_value(config_key, 'ui-updated')
    config_page.search(config_key)
    detail = config_api.get_config(seeded_ui_config['config_id'])

    # 断言：列表显示新键值，接口详情也得到已落库的新值
    expect(config_page.row_by_key(config_key)).to_contain_text('ui-updated')
    assert detail['data']['configValue'] == 'ui-updated', detail


@allure.feature('系统管理')
@allure.story('参数设置页面')
@allure.title('通过页面确认删除非内置参数')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_delete_config(config_page, config_api, seeded_ui_config, oper_log_guard):
    config_key = seeded_ui_config['config_key']
    oper_log_guard.register_url(f"/system/config/{seeded_ui_config['config_id']}")
    config_page.search(config_key)
    config_page.delete_config(config_key)
    rows = [
        row for row in config_api.list_configs(configKey=config_key).get('rows', [])
        if row.get('configKey') == config_key
    ]

    # 断言：删除后页面和接口均不存在目标参数
    expect(config_page.row_by_key(config_key)).to_have_count(0)
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('参数设置页面')
@allure.title('通过页面按参数键名导出 Excel')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_export_config(config_page, seeded_ui_config):
    config_page.search(seeded_ui_config['config_key'])

    with config_page.page.expect_download() as download_info:
        config_page.export_button.click()
    download = download_info.value
    values = xlsx_text_values(download.path().read_bytes())

    # 断言：浏览器下载 XLSX，内容包含本次筛选的目标参数
    assert download.suggested_filename.endswith('.xlsx')
    assert seeded_ui_config['config_name'] in values, values
    assert seeded_ui_config['config_key'] in values, values


@allure.feature('系统管理')
@allure.story('参数设置页面')
@allure.title('刷新参数缓存后展示成功提示')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_refresh_config_cache(config_page):
    config_page.refresh_cache()

    # 断言：刷新缓存后页面提示成功
    expect(config_page.message).to_have_text('刷新成功')
