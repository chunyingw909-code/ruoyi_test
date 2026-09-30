import allure
import pytest
from playwright.sync_api import expect

from common.utils import read_yaml
from common.xlsx_utils import xlsx_text_values


add_error_data = read_yaml('data/system/role_ui_errors.yaml')


@allure.feature('系统管理')
@allure.story('角色管理页面')
@allure.title('角色管理页展示查询、工具栏和列表核心元素')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_role_page_structure(role_page):
    # 断言：角色页具备查询、增删改、导出和主要列表字段
    expect(role_page.search_role_name_input).to_be_visible()
    expect(role_page.search_role_key_input).to_be_visible()
    expect(role_page.search_status_input).to_be_visible()
    expect(role_page.add_button).to_be_visible()
    expect(role_page.edit_button).to_be_visible()
    expect(role_page.delete_button).to_be_visible()
    expect(role_page.export_button).to_be_visible()
    expect(role_page.table_headers).to_contain_text('角色名称')
    expect(role_page.table_headers).to_contain_text('权限字符')
    expect(role_page.table_headers).to_contain_text('显示顺序')
    expect(role_page.table_headers).to_contain_text('状态')
    expect(role_page.table_headers).to_contain_text('操作')


@allure.feature('系统管理')
@allure.story('角色管理页面')
@allure.title('按角色名称筛选后可以重置查询条件')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_search_and_reset_role(role_page, seeded_ui_role):
    role_page.search(seeded_ui_role['role_name'])

    # 断言：精确筛选只显示目标角色
    expect(role_page.row_by_role_name(seeded_ui_role['role_name'])).to_have_count(1)
    expect(role_page.pagination_total).to_contain_text('共 1 条')

    role_page.reset_search()

    # 断言：重置后角色名称查询框被清空
    expect(role_page.search_role_name_input).to_have_value('')


@allure.feature('系统管理')
@allure.story('角色管理页面')
@allure.title('通过页面正常新增角色')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_add_role_success(
    role_page,
    unique_role_identity,
    track_test_role,
):
    identity = unique_role_identity
    role_page.add_role(identity['role_name'], identity['role_key'])
    role_page.search(identity['role_name'])

    try:
        # 断言：新增后列表展示目标角色及其权限字符
        row = role_page.row_by_role_name(identity['role_name'])
        expect(row).to_have_count(1)
        expect(row).to_contain_text(identity['role_key'])
    finally:
        track_test_role(identity['role_name'])


@allure.feature('系统管理')
@allure.story('角色管理页面')
@allure.title('新增角色表单异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_role_validation(role_page, track_test_role, case):
    try:
        role_page.add_role(case['role_name'], case['role_key'])

        # 断言：缺少必填字段时弹窗展示字段级校验提示
        expect(role_page.add_form_error).to_have_text(case['expect'])
    finally:
        if case['role_name'].startswith('AUTOTEST-role-'):
            track_test_role(case['role_name'])


@allure.feature('系统管理')
@allure.story('角色管理页面')
@allure.title('通过页面修改角色名称')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_edit_role(role_page, role_api, seeded_ui_role):
    old_name = seeded_ui_role['role_name']
    new_name = f'{old_name}-updated'
    role_page.search(old_name)
    role_page.edit_role_name(old_name, new_name)
    role_page.search(new_name)
    detail = role_api.get_role(seeded_ui_role['role_id'])

    # 断言：列表显示新名称，接口详情也得到已落库的新值
    expect(role_page.row_by_role_name(new_name)).to_have_count(1)
    assert detail['data']['roleName'] == new_name, detail


@allure.feature('系统管理')
@allure.story('角色管理页面')
@allure.title('通过页面停用后重新启用角色')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_change_role_status(role_page, role_api, seeded_ui_role):
    role_name = seeded_ui_role['role_name']
    role_page.search(role_name)
    expect(role_page.status_checkbox(role_name)).to_be_checked()

    role_page.change_status(role_name)
    disabled = role_api.get_role(seeded_ui_role['role_id'])

    # 断言：页面开关和接口状态都变为停用
    expect(role_page.status_checkbox(role_name)).not_to_be_checked()
    assert disabled['data']['status'] == '1', disabled

    role_page.change_status(role_name)
    enabled = role_api.get_role(seeded_ui_role['role_id'])

    # 断言：页面开关和接口状态恢复为正常
    expect(role_page.status_checkbox(role_name)).to_be_checked()
    assert enabled['data']['status'] == '0', enabled


@allure.feature('系统管理')
@allure.story('角色数据权限页面')
@allure.title('更多菜单提供分配用户并可设置仅本人数据权限')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_change_role_data_scope(role_page, role_api, seeded_ui_role):
    role_name = seeded_ui_role['role_name']
    role_page.search(role_name)
    role_page.open_more_actions(role_name)

    # 断言：更多菜单包含角色管理特有的两个业务入口
    expect(role_page.data_scope_menu_item).to_be_visible()
    expect(role_page.assign_user_menu_item).to_be_visible()

    role_page.data_scope_menu_item.click()
    expect(role_page.data_scope_dialog).to_be_visible()
    role_page.data_scope_select.click()
    role_page.self_data_scope_option.click()
    with role_page.page.expect_response(
        lambda response: '/system/role/dataScope' in response.url
    ):
        role_page.data_scope_confirm_button.click()
    role_page.data_scope_dialog.wait_for(state='hidden')
    detail = role_api.get_role(seeded_ui_role['role_id'])

    # 断言：接口详情确认数据范围已落库为“仅本人”
    assert detail['data']['dataScope'] == '5', detail


@allure.feature('系统管理')
@allure.story('角色管理页面')
@allure.title('通过页面确认删除角色')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_delete_role(role_page, role_api, seeded_ui_role):
    role_name = seeded_ui_role['role_name']
    role_page.search(role_name)
    role_page.delete_role(role_name)
    rows = [
        row for row in role_api.list_roles(roleName=role_name).get('rows', [])
        if row.get('roleName') == role_name
    ]

    # 断言：删除后页面和接口均不存在目标角色
    expect(role_page.row_by_role_name(role_name)).to_have_count(0)
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('角色管理页面')
@allure.title('通过页面按角色名称导出 Excel')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_export_role(role_page, seeded_ui_role):
    role_name = seeded_ui_role['role_name']
    role_page.search(role_name)

    with role_page.page.expect_download() as download_info:
        role_page.export_button.click()
    download = download_info.value
    values = xlsx_text_values(download.path().read_bytes())

    # 断言：浏览器下载 XLSX，内容包含本次筛选的目标角色
    assert download.suggested_filename.endswith('.xlsx')
    assert role_name in values, values
    assert seeded_ui_role['role_key'] in values, values
