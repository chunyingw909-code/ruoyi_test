import allure
import pytest
from playwright.sync_api import expect

from common.utils import read_yaml


add_error_data = read_yaml('data/system/dept_ui_errors.yaml')


@allure.feature('系统管理')
@allure.story('部门管理页面')
@allure.title('部门管理页展示查询、工具栏和树形列表核心元素')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_dept_page_structure(dept_page):
    # 断言：部门页具备查询、新增、排序、折叠和主要列表字段
    expect(dept_page.search_dept_name_input).to_be_visible()
    expect(dept_page.search_status_input).to_be_visible()
    expect(dept_page.add_button).to_be_visible()
    expect(dept_page.save_sort_button).to_be_visible()
    expect(dept_page.toggle_expand_button).to_be_visible()
    expect(dept_page.table_headers).to_contain_text('部门名称')
    expect(dept_page.table_headers).to_contain_text('排序')
    expect(dept_page.table_headers).to_contain_text('状态')
    expect(dept_page.table_headers).to_contain_text('创建时间')
    expect(dept_page.table_headers).to_contain_text('操作')


@allure.feature('系统管理')
@allure.story('部门管理页面')
@allure.title('按部门名称筛选后可以重置查询条件')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_search_and_reset_dept(dept_page, seeded_ui_dept):
    dept_page.search(seeded_ui_dept['dept_name'])
    # 断言：筛选后树形列表只展示目标部门
    expect(dept_page.row_by_dept_name(seeded_ui_dept['dept_name'])).to_have_count(1)

    dept_page.reset_search()
    # 断言：重置后部门名称查询框被清空
    expect(dept_page.search_dept_name_input).to_have_value('')


@allure.feature('系统管理')
@allure.story('部门管理页面')
@allure.title('通过父部门行内入口新增子部门')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_add_dept_success(dept_page, unique_dept_name, track_test_dept):
    dept_page.add_department('若依科技', unique_dept_name)
    dept_page.search(unique_dept_name)

    try:
        # 断言：新增后列表展示目标子部门
        expect(dept_page.row_by_dept_name(unique_dept_name)).to_have_count(1)
    finally:
        track_test_dept(unique_dept_name)


@allure.feature('系统管理')
@allure.story('部门管理页面')
@allure.title('新增部门表单异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_dept_validation(dept_page, case):
    dept_page.add_department('若依科技', case['dept_name'])
    # 断言：缺少部门名称时弹窗展示字段级校验提示
    expect(dept_page.add_form_error).to_have_text(case['expect'])


@allure.feature('系统管理')
@allure.story('部门管理页面')
@allure.title('通过页面修改部门名称')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_edit_dept(dept_page, dept_api, seeded_ui_dept):
    old_name = seeded_ui_dept['dept_name']
    new_name = f'{old_name}-updated'
    dept_page.search(old_name)
    dept_page.edit_dept_name(old_name, new_name)
    dept_page.search(new_name)
    detail = dept_api.get_dept(seeded_ui_dept['dept_id'])

    # 断言：列表显示新名称，接口详情也得到已落库的新值
    expect(dept_page.row_by_dept_name(new_name)).to_have_count(1)
    assert detail['data']['deptName'] == new_name, detail


@allure.feature('系统管理')
@allure.story('部门管理页面')
@allure.title('通过页面确认删除部门')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_delete_dept(dept_page, dept_api, seeded_ui_dept):
    dept_name = seeded_ui_dept['dept_name']
    dept_page.search(dept_name)
    dept_page.delete_department(dept_name)
    rows = [
        row for row in dept_api.list_depts(deptName=dept_name).get('data', [])
        if row.get('deptName') == dept_name
    ]

    # 断言：删除后页面和接口均不存在目标部门
    expect(dept_page.row_by_dept_name(dept_name)).to_have_count(0)
    assert rows == [], rows
