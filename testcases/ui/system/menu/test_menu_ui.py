import allure
import pytest
from playwright.sync_api import expect

from common.utils import read_yaml


add_error_data = read_yaml('data/system/menu_ui_errors.yaml')


@allure.feature('系统管理')
@allure.story('菜单管理页面')
@allure.title('菜单管理页展示查询、工具栏和树形列表核心元素')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_menu_page_structure(menu_page):
    # 断言：菜单页具备查询、新增、排序、折叠和主要列表字段
    expect(menu_page.search_menu_name_input).to_be_visible()
    expect(menu_page.search_status_input).to_be_visible()
    expect(menu_page.add_button).to_be_visible()
    expect(menu_page.save_sort_button).to_be_visible()
    expect(menu_page.toggle_expand_button).to_be_visible()
    expect(menu_page.table_headers).to_contain_text('菜单名称')
    expect(menu_page.table_headers).to_contain_text('类型')
    expect(menu_page.table_headers).to_contain_text('排序')
    expect(menu_page.table_headers).to_contain_text('权限标识')
    expect(menu_page.table_headers).to_contain_text('状态')
    expect(menu_page.table_headers).to_contain_text('操作')


@allure.feature('系统管理')
@allure.story('菜单管理页面')
@allure.title('按菜单名称筛选后可以重置查询条件')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_search_and_reset_menu(menu_page, seeded_ui_menu):
    menu_page.search(seeded_ui_menu['menu_name'])

    # 断言：筛选后树形列表只展示目标菜单
    expect(menu_page.row_by_menu_name(seeded_ui_menu['menu_name'])).to_have_count(1)

    menu_page.reset_search()

    # 断言：重置后菜单名称查询框被清空
    expect(menu_page.search_menu_name_input).to_have_value('')


@allure.feature('系统管理')
@allure.story('菜单管理页面')
@allure.title('通过页面正常新增顶级目录菜单')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_add_menu_success(menu_page, unique_menu_identity, track_test_menu):
    identity = unique_menu_identity
    menu_page.add_menu(identity['menu_name'], identity['path'])
    menu_page.search(identity['menu_name'])

    try:
        # 断言：新增后列表展示目标目录及其路由
        row = menu_page.row_by_menu_name(identity['menu_name'])
        expect(row).to_have_count(1)
        expect(row).to_contain_text('目录')
    finally:
        track_test_menu(identity['menu_name'])


@allure.feature('系统管理')
@allure.story('菜单管理页面')
@allure.title('新增菜单表单异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_menu_validation(menu_page, track_test_menu, case):
    try:
        menu_page.add_menu(case['menu_name'], case['path'])

        # 断言：缺少菜单名称时弹窗展示字段级校验提示
        expect(menu_page.add_form_error).to_have_text(case['expect'])
    finally:
        if case['menu_name'].startswith('AUTOTEST-menu-'):
            track_test_menu(case['menu_name'])


@allure.feature('系统管理')
@allure.story('菜单管理页面')
@allure.title('通过页面修改菜单名称')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_edit_menu(menu_page, menu_api, seeded_ui_menu):
    old_name = seeded_ui_menu['menu_name']
    new_name = f'{old_name}-updated'
    menu_page.search(old_name)
    menu_page.edit_menu_name(old_name, new_name)
    menu_page.search(new_name)
    detail = menu_api.get_menu(seeded_ui_menu['menu_id'])

    # 断言：列表显示新名称，接口详情也得到已落库的新值
    expect(menu_page.row_by_menu_name(new_name)).to_have_count(1)
    assert detail['data']['menuName'] == new_name, detail


@allure.feature('系统管理')
@allure.story('菜单管理页面')
@allure.title('通过页面确认删除菜单')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_delete_menu(menu_page, menu_api, seeded_ui_menu):
    menu_name = seeded_ui_menu['menu_name']
    menu_page.search(menu_name)
    menu_page.delete_menu(menu_name)
    rows = [
        row for row in menu_api.list_menus(menuName=menu_name).get('data', [])
        if row.get('menuName') == menu_name
    ]

    # 断言：删除后页面和接口均不存在目标菜单
    expect(menu_page.row_by_menu_name(menu_name)).to_have_count(0)
    assert rows == [], rows
