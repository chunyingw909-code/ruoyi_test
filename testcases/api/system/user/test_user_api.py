import allure
import pytest

from api.auth.login_api import LoginApi
from common.utils import project_path, read_yaml
from common.xlsx_utils import xlsx_text_values


add_error_data = read_yaml('data/system/user_api_errors.yaml')


@allure.feature('系统管理')
@allure.story('用户管理接口')
@allure.title('用户列表支持用户名精确筛选和分页')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_list_user_with_filter_and_pagination(user_api, seeded_user):
    result = user_api.list_users(
        userName=seeded_user['username'],
        pageNum=1,
        pageSize=10,
    )
    exact_rows = [
        row for row in result.get('rows', [])
        if row.get('userName') == seeded_user['username']
    ]

    # 断言：HTTP/业务响应成功，筛选结果只包含目标用户
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['total'] == 1, result
    assert len(exact_rows) == 1, exact_rows


@allure.feature('系统管理')
@allure.story('用户管理接口')
@allure.title('新增用户后可以按用户名查询')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_add_and_list_user(user_api, unique_username, track_test_user):
    result = user_api.add_user(
        unique_username,
        '接口新增用户',
        password='AutoTest123',
        status='0',
    )
    rows = track_test_user(unique_username)

    # 断言：新增接口成功，并且列表接口能精确查到新用户
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) == 1, rows
    assert rows[0]['userName'] == unique_username
    assert rows[0]['nickName'] == '接口新增用户'


@allure.feature('系统管理')
@allure.story('用户管理接口')
@allure.title('新增用户异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_user_validation(user_api, unique_username, track_test_user, case):
    username = unique_username if case['username'] == '__unique__' else case['username']
    try:
        result = user_api.add_user(username, case['nickname'])
    finally:
        # 即使产品错误地创建了非法数据，也只登记并清理唯一 AUTOTEST 用户。
        if username.startswith('AUTOTEST-'):
            track_test_user(username)

    # 断言：非法或重复的用户数据被业务层拒绝
    assert result.status_code == 200, result
    assert result['code'] == case['expected_code'], result


@allure.feature('系统管理')
@allure.story('用户管理接口')
@allure.title('用户详情返回用户、角色和岗位选项')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_get_user_detail(user_api, seeded_user):
    result = user_api.get_user(seeded_user['user_id'])

    # 断言：详情对应目标用户，并提供编辑表单所需角色/岗位数据
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['data']['userId'] == seeded_user['user_id'], result
    assert result['data']['userName'] == seeded_user['username'], result
    assert isinstance(result['roles'], list), result
    assert isinstance(result['posts'], list), result
    assert isinstance(result['roleIds'], list), result
    assert isinstance(result['postIds'], list), result


@allure.feature('系统管理')
@allure.story('用户管理接口')
@allure.title('部门树接口返回可供用户归属选择的层级数据')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.api
def test_get_department_tree(user_api):
    result = user_api.dept_tree()

    # 断言：部门树响应成功，根节点包含 id、名称和子节点
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert isinstance(result['data'], list) and result['data'], result
    root = result['data'][0]
    assert root.get('id') is not None, root
    assert root.get('label'), root
    assert isinstance(root.get('children'), list), root


@allure.feature('系统管理')
@allure.story('用户管理接口')
@allure.title('更新用户昵称后列表返回新值')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_update_user(user_api, seeded_user):
    email = f"{seeded_user['username'].lower()}@example.com"
    result = user_api.update_user(
        seeded_user['user_id'],
        userName=seeded_user['username'],
        nickName='接口更新用户',
        email=email,
        sex='1',
        status='0',
    )
    list_result = user_api.list_user(seeded_user['username'])
    exact_rows = [
        row for row in list_result.get('rows', [])
        if row.get('userName') == seeded_user['username']
    ]

    # 断言：更新接口成功，并且重新查询得到更新后的昵称
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(exact_rows) == 1, exact_rows
    assert exact_rows[0]['nickName'] == '接口更新用户'
    assert exact_rows[0]['email'] == email
    assert exact_rows[0]['sex'] == '1'


@allure.feature('系统管理')
@allure.story('用户管理接口')
@allure.title('用户状态可以停用后重新启用')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_change_user_status(user_api, seeded_user):
    disabled = user_api.change_status(seeded_user['user_id'], '1')
    disabled_row = user_api.list_user(seeded_user['username'])['rows'][0]
    enabled = user_api.change_status(seeded_user['user_id'], '0')
    enabled_row = user_api.list_user(seeded_user['username'])['rows'][0]

    # 断言：停用和启用请求都成功，列表状态随操作变化
    assert disabled.status_code == 200, disabled
    assert disabled['code'] == 200, disabled
    assert disabled_row['status'] == '1', disabled_row
    assert enabled.status_code == 200, enabled
    assert enabled['code'] == 200, enabled
    assert enabled_row['status'] == '0', enabled_row


@allure.feature('系统管理')
@allure.story('用户管理接口')
@allure.title('重置密码后用户可以使用新密码登录')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_reset_user_password(user_api, seeded_user):
    new_password = 'Reset12345'
    reset_result = user_api.reset_password(seeded_user['user_id'], new_password)
    login_api = LoginApi()
    authenticated_api = None
    try:
        login_result = login_api.login(seeded_user['username'], new_password)
        if login_result.get('token'):
            authenticated_api = LoginApi(login_result['token'])
            authenticated_api.logout()
    finally:
        login_api.close()
        if authenticated_api is not None:
            authenticated_api.close()

    # 断言：密码重置成功，新密码可以完成真实登录
    assert reset_result.status_code == 200, reset_result
    assert reset_result['code'] == 200, reset_result
    assert login_result.status_code == 200, login_result
    assert login_result['code'] == 200, login_result
    assert login_result.get('token'), login_result


@allure.feature('系统管理')
@allure.story('用户管理接口')
@allure.title('删除用户后列表中不再存在该用户')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_delete_user(user_api, seeded_user):
    result = user_api.delete_user(seeded_user['user_id'])
    list_result = user_api.list_user(seeded_user['username'])
    exact_rows = [
        row for row in list_result.get('rows', [])
        if row.get('userName') == seeded_user['username']
    ]

    # 断言：删除接口成功，随后精确查询不到目标用户
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert exact_rows == [], exact_rows


@allure.feature('系统管理')
@allure.story('用户管理接口')
@allure.title('多个用户可以通过一个请求批量删除')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_batch_delete_users(user_api, seeded_users):
    result = user_api.delete_users([user['user_id'] for user in seeded_users])
    remaining = []
    for user in seeded_users:
        rows = user_api.list_user(user['username']).get('rows', [])
        remaining.extend(
            row for row in rows if row.get('userName') == user['username']
        )

    # 断言：批量删除成功，两个目标用户均不存在
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert remaining == [], remaining


@allure.feature('系统管理')
@allure.story('用户导入导出接口')
@allure.title('导入模板接口返回有效 Excel 工作簿')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_download_import_template(user_api):
    result = user_api.import_template()
    values = xlsx_text_values(result.content)

    # 断言：返回 XLSX 文件，并包含若依用户导入模板字段
    assert result.status_code == 200, result
    assert result.content_type.startswith(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ), result.headers
    assert result.content.startswith(b'PK\x03\x04')
    assert {'部门编号', '登录名称', '用户名称', '账号状态'} <= set(values)


@allure.feature('系统管理')
@allure.story('用户导入导出接口')
@allure.title('上传合法 Excel 可以导入一个用户')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_import_user(user_api, import_test_username):
    result = user_api.import_users(
        project_path('data', 'system', 'user_import.xlsx')
    )
    exact_rows = [
        row for row in user_api.list_user(import_test_username).get('rows', [])
        if row.get('userName') == import_test_username
    ]

    # 断言：导入成功且用户字段与工作簿一致
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert '共 1 条' in result['msg'], result
    assert len(exact_rows) == 1, exact_rows
    assert exact_rows[0]['nickName'] == '导入测试用户'
    assert exact_rows[0]['status'] == '0'


@allure.feature('系统管理')
@allure.story('用户导入导出接口')
@allure.title('按用户名导出的 Excel 包含目标用户')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_export_user(user_api, seeded_user):
    result = user_api.export_users(userName=seeded_user['username'])
    values = xlsx_text_values(result.content)

    # 断言：返回有效 XLSX，且导出内容包含筛选用户和昵称
    assert result.status_code == 200, result
    assert result.content_type.startswith(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ), result.headers
    assert result.content.startswith(b'PK\x03\x04')
    assert seeded_user['username'] in values, values
    assert '接口预置用户' in values, values
