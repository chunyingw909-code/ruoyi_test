import allure
import pytest
from playwright.sync_api import expect

from common.utils import project_path, read_yaml
from common.xlsx_utils import xlsx_text_values


add_error_data = read_yaml('data/system/user_ui_errors.yaml')


@allure.feature('系统管理')
@allure.story('用户管理页面')
@allure.title('用户管理页展示查询、工具栏和列表核心元素')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_user_page_structure(user_page):
    # 断言：用户管理页面具备查询、新增、导入导出和主要列表字段
    expect(user_page.search_username_input).to_be_visible()
    expect(user_page.search_phone_input).to_be_visible()
    expect(user_page.add_button).to_be_visible()
    expect(user_page.import_button).to_be_visible()
    expect(user_page.export_button).to_be_visible()
    expect(user_page.table_headers).to_contain_text('用户编号')
    expect(user_page.table_headers).to_contain_text('用户名称')
    expect(user_page.table_headers).to_contain_text('用户昵称')
    expect(user_page.table_headers).to_contain_text('状态')
    expect(user_page.table_headers).to_contain_text('操作')


@allure.feature('系统管理')
@allure.story('用户管理页面')
@allure.title('按用户名筛选后可以重置查询条件')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_search_and_reset_user(user_page, seeded_ui_user):
    user_page.search(seeded_ui_user['username'])

    # 断言：精确筛选只显示目标用户
    expect(user_page.user_link(seeded_ui_user['username'])).to_have_count(1)
    expect(user_page.pagination_total).to_contain_text('共 1 条')

    user_page.reset_search()

    # 断言：重置后用户名查询框被清空
    expect(user_page.search_username_input).to_have_value('')


@allure.feature('系统管理')
@allure.story('用户管理页面')
@allure.title('通过页面正常新增用户')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_add_user_success(user_page, unique_username, track_test_user):
    user_page.add_user(unique_username, 'UI 新增用户')
    user_page.search(unique_username)

    try:
        # 断言：新增后用户列表中出现唯一的目标账号
        expect(user_page.user_link(unique_username)).to_have_count(1)
    finally:
        track_test_user(unique_username)


@allure.feature('系统管理')
@allure.story('用户管理页面')
@allure.title('新增用户表单异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_user_validation(user_page, unique_username, track_test_user, case):
    username = unique_username if case['username'] == '__unique__' else case['username']
    try:
        user_page.add_user(username, case['nickname'])

        if case['error_type'] == 'form':
            # 断言：缺少必填字段时弹窗展示字段级校验提示
            expect(user_page.add_form_error).to_have_text(case['expect'])
        else:
            # 断言：服务端拒绝重复用户名时展示业务错误消息
            expect(user_page.message).to_have_text(case['expect'])
    finally:
        # 防止产品校验失效时遗留唯一测试数据；固定账号永远不会进入清理入口。
        if username.startswith('AUTOTEST-'):
            track_test_user(username)


@allure.feature('系统管理')
@allure.story('用户管理页面')
@allure.title('通过页面修改用户昵称')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_edit_user(user_page, user_api, seeded_ui_user):
    username = seeded_ui_user['username']
    user_page.search(username)
    user_page.edit_nickname(username, 'UI 修改用户')
    user_page.search(username)
    rows = [
        row for row in user_api.list_user(username).get('rows', [])
        if row.get('userName') == username
    ]

    # 断言：页面展示新昵称，接口查询也得到已落库的新值
    expect(user_page.row_by_username(username)).to_contain_text('UI 修改用户')
    assert len(rows) == 1, rows
    assert rows[0]['nickName'] == 'UI 修改用户', rows[0]


@allure.feature('系统管理')
@allure.story('用户管理页面')
@allure.title('通过页面停用后重新启用用户')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_change_user_status(user_page, user_api, seeded_ui_user):
    username = seeded_ui_user['username']
    user_page.search(username)
    expect(user_page.status_checkbox(username)).to_be_checked()

    user_page.change_status(username)
    disabled = user_api.list_user(username)['rows'][0]

    # 断言：页面开关和接口状态都变为停用
    expect(user_page.status_checkbox(username)).not_to_be_checked()
    assert disabled['status'] == '1', disabled

    user_page.change_status(username)
    enabled = user_api.list_user(username)['rows'][0]

    # 断言：页面开关和接口状态恢复为正常
    expect(user_page.status_checkbox(username)).to_be_checked()
    assert enabled['status'] == '0', enabled


@allure.feature('系统管理')
@allure.story('用户管理页面')
@allure.title('通过页面确认删除用户')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_delete_user(user_page, user_api, seeded_ui_user):
    username = seeded_ui_user['username']
    user_page.search(username)
    user_page.delete_user(username)
    rows = [
        row for row in user_api.list_user(username).get('rows', [])
        if row.get('userName') == username
    ]

    # 断言：删除后页面不再展示该用户，接口也查询不到目标数据
    expect(user_page.user_link(username)).to_have_count(0)
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('用户导入导出页面')
@allure.title('通过页面上传 Excel 导入用户')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_import_user(user_page, user_api, import_test_username):
    user_page.import_users(project_path('data', 'system', 'user_import.xlsx'))
    user_page.search(import_test_username)
    rows = [
        row for row in user_api.list_user(import_test_username).get('rows', [])
        if row.get('userName') == import_test_username
    ]

    # 断言：页面能查询到导入账号，且接口中的昵称与工作簿一致
    expect(user_page.user_link(import_test_username)).to_have_count(1)
    assert len(rows) == 1, rows
    assert rows[0]['nickName'] == '导入测试用户', rows[0]


@allure.feature('系统管理')
@allure.story('用户导入导出页面')
@allure.title('通过页面按用户名导出用户 Excel')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_export_user(user_page, seeded_ui_user):
    username = seeded_ui_user['username']
    user_page.search(username)

    with user_page.page.expect_download() as download_info:
        user_page.export_button.click()
    download = download_info.value
    values = xlsx_text_values(download.path().read_bytes())

    # 断言：浏览器下载 XLSX，内容只需确认包含本次筛选的目标用户
    assert download.suggested_filename.endswith('.xlsx')
    assert username in values, values
    assert 'UI 预置用户' in values, values
