import allure
import pytest

from common.utils import read_yaml
from common.xlsx_utils import xlsx_text_values


add_error_data = read_yaml('data/system/role_api_errors.yaml')


def exact_roles(result, role_name):
    return [
        row for row in result.get('rows', [])
        if row.get('roleName') == role_name
    ]


@allure.feature('系统管理')
@allure.story('角色管理接口')
@allure.title('角色列表支持名称筛选和分页')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_list_role_with_filter_and_pagination(role_api, seeded_role):
    result = role_api.list_roles(
        roleName=seeded_role['role_name'],
        pageNum=1,
        pageSize=10,
    )
    rows = exact_roles(result, seeded_role['role_name'])

    # 断言：列表接口成功，精确筛选只返回目标角色
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['total'] == 1, result
    assert len(rows) == 1, rows
    assert rows[0]['roleKey'] == seeded_role['role_key']


@allure.feature('系统管理')
@allure.story('角色管理接口')
@allure.title('新增角色后可以按名称查询')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_add_and_list_role(role_api, unique_role_identity, track_test_role):
    identity = unique_role_identity
    result = role_api.add_role(
        identity['role_name'],
        identity['role_key'],
        role_sort=10,
        remark='接口新增角色',
    )
    rows = track_test_role(identity['role_name'])

    # 断言：新增成功，角色名称、权限字符和顺序均已落库
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) == 1, rows
    assert rows[0]['roleKey'] == identity['role_key']
    assert rows[0]['roleSort'] == 10


@allure.feature('系统管理')
@allure.story('角色管理接口')
@allure.title('新增角色异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_role_validation(role_api, track_test_role, case):
    try:
        result = role_api.add_role(case['role_name'], case['role_key'])
    finally:
        if case['role_name'].startswith('AUTOTEST-role-'):
            track_test_role(case['role_name'])

    # 断言：必填字段缺失时业务层拒绝新增并返回对应提示
    assert result.status_code == 200, result
    assert result['code'] == 500, result
    assert case['expect'] in result['msg'], result


@allure.feature('系统管理')
@allure.story('角色管理接口')
@allure.title('角色名称和权限字符不能重复')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_add_role_rejects_duplicate_identity(
    role_api,
    seeded_role,
    unique_role_identity,
    track_test_role,
):
    duplicate_name = role_api.add_role(
        seeded_role['role_name'],
        unique_role_identity['role_key'],
    )
    duplicate_key_name = f"{unique_role_identity['role_name']}-key"
    try:
        duplicate_key = role_api.add_role(
            duplicate_key_name,
            seeded_role['role_key'],
        )
    finally:
        track_test_role(duplicate_key_name)

    # 断言：名称重复和权限字符重复均被拒绝
    assert duplicate_name['code'] == 500, duplicate_name
    assert '角色名称已存在' in duplicate_name['msg'], duplicate_name
    assert duplicate_key['code'] == 500, duplicate_key
    assert '角色权限已存在' in duplicate_key['msg'], duplicate_key


@allure.feature('系统管理')
@allure.story('角色管理接口')
@allure.title('角色详情返回完整基础信息')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_get_role_detail(role_api, seeded_role):
    result = role_api.get_role(seeded_role['role_id'])

    # 断言：详情与预置角色一致，并包含数据权限配置
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['data']['roleId'] == seeded_role['role_id'], result
    assert result['data']['roleName'] == seeded_role['role_name'], result
    assert result['data']['roleKey'] == seeded_role['role_key'], result
    assert result['data']['dataScope'] == '1', result


@allure.feature('系统管理')
@allure.story('角色菜单权限接口')
@allure.title('菜单树和角色菜单树返回可配置的层级数据')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.api
def test_get_role_menu_trees(role_api, seeded_role):
    menu_tree = role_api.menu_tree()
    role_tree = role_api.role_menu_tree(seeded_role['role_id'])

    # 断言：菜单树有层级节点，角色菜单接口有选中项列表
    assert menu_tree.status_code == 200, menu_tree
    assert menu_tree['code'] == 200, menu_tree
    assert isinstance(menu_tree['data'], list) and menu_tree['data'], menu_tree
    assert {'id', 'label', 'children'} <= set(menu_tree['data'][0]), menu_tree
    assert role_tree.status_code == 200, role_tree
    assert role_tree['code'] == 200, role_tree
    assert isinstance(role_tree['menus'], list), role_tree
    assert isinstance(role_tree['checkedKeys'], list), role_tree


@allure.feature('系统管理')
@allure.story('角色管理接口')
@allure.title('修改角色名称、顺序和备注后查询得到新值')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_update_role(role_api, seeded_role):
    result = role_api.update_role(
        seeded_role['role_id'],
        roleName=f"{seeded_role['role_name']}-updated",
        roleKey=seeded_role['role_key'],
        roleSort=20,
        status='0',
        remark='接口修改角色',
        menuIds=[],
        menuCheckStrictly=True,
    )
    detail = role_api.get_role(seeded_role['role_id'])

    # 断言：修改成功，详情接口返回更新后的字段
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert detail['data']['roleName'].endswith('-updated'), detail
    assert detail['data']['roleSort'] == 20, detail
    assert detail['data']['remark'] == '接口修改角色', detail


@allure.feature('系统管理')
@allure.story('角色管理接口')
@allure.title('角色状态可以停用后重新启用')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_change_role_status(role_api, seeded_role):
    disabled = role_api.change_status(seeded_role['role_id'], '1')
    disabled_detail = role_api.get_role(seeded_role['role_id'])
    enabled = role_api.change_status(seeded_role['role_id'], '0')
    enabled_detail = role_api.get_role(seeded_role['role_id'])

    # 断言：停用、启用请求均成功，详情状态同步变化
    assert disabled['code'] == 200, disabled
    assert disabled_detail['data']['status'] == '1', disabled_detail
    assert enabled['code'] == 200, enabled
    assert enabled_detail['data']['status'] == '0', enabled_detail


@allure.feature('系统管理')
@allure.story('角色数据权限接口')
@allure.title('角色可以配置自定义部门数据权限')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_change_role_data_scope(role_api, seeded_role):
    result = role_api.change_data_scope(
        seeded_role['role_id'],
        data_scope='2',
        dept_ids=[100],
    )
    detail = role_api.get_role(seeded_role['role_id'])
    dept_tree = role_api.dept_tree(seeded_role['role_id'])

    # 断言：数据权限已切换为自定义，部门树回显选中的部门
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert detail['data']['dataScope'] == '2', detail
    assert dept_tree['code'] == 200, dept_tree
    assert 100 in dept_tree['checkedKeys'], dept_tree
    assert isinstance(dept_tree['depts'], list) and dept_tree['depts'], dept_tree


@allure.feature('系统管理')
@allure.story('角色用户分配接口')
@allure.title('角色可以分配并取消一个用户')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_assign_and_cancel_role_user(
    role_api,
    seeded_role,
    create_test_user,
):
    user = create_test_user(nickname='角色分配用户')
    unallocated = role_api.unallocated_users(
        seeded_role['role_id'],
        userName=user['username'],
    )
    assigned = role_api.assign_users(
        seeded_role['role_id'],
        [user['user_id']],
    )
    allocated = role_api.allocated_users(
        seeded_role['role_id'],
        userName=user['username'],
    )
    cancelled = role_api.cancel_user(
        seeded_role['role_id'],
        user['user_id'],
    )
    after_cancel = role_api.allocated_users(
        seeded_role['role_id'],
        userName=user['username'],
    )

    # 断言：用户初始可分配，分配后进入已分配列表，取消后移除
    assert len(exact_users(unallocated, user['username'])) == 1, unallocated
    assert assigned['code'] == 200, assigned
    assert len(exact_users(allocated, user['username'])) == 1, allocated
    assert cancelled['code'] == 200, cancelled
    assert exact_users(after_cancel, user['username']) == [], after_cancel


def exact_users(result, username):
    return [
        row for row in result.get('rows', [])
        if row.get('userName') == username
    ]


@allure.feature('系统管理')
@allure.story('角色用户分配接口')
@allure.title('角色可以批量分配并批量取消多个用户')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_batch_assign_and_cancel_role_users(
    role_api,
    seeded_role,
    create_test_user,
):
    users = [
        create_test_user(nickname='角色批量用户一'),
        create_test_user(nickname='角色批量用户二'),
    ]
    user_ids = [user['user_id'] for user in users]
    assigned = role_api.assign_users(seeded_role['role_id'], user_ids)
    allocated = role_api.allocated_users(
        seeded_role['role_id'],
        pageNum=1,
        pageSize=100,
    )
    cancelled = role_api.cancel_users(seeded_role['role_id'], user_ids)
    after_cancel = role_api.allocated_users(
        seeded_role['role_id'],
        pageNum=1,
        pageSize=100,
    )

    allocated_ids = {row['userId'] for row in allocated.get('rows', [])}
    remaining_ids = {row['userId'] for row in after_cancel.get('rows', [])}

    # 断言：两个用户均完成分配，并能通过一次请求全部取消
    assert assigned['code'] == 200, assigned
    assert set(user_ids) <= allocated_ids, allocated
    assert cancelled['code'] == 200, cancelled
    assert set(user_ids).isdisjoint(remaining_ids), after_cancel


@allure.feature('系统管理')
@allure.story('角色管理接口')
@allure.title('删除角色后列表中不再存在该角色')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_delete_role(role_api, seeded_role):
    result = role_api.delete_role(seeded_role['role_id'])
    rows = exact_roles(
        role_api.list_roles(roleName=seeded_role['role_name']),
        seeded_role['role_name'],
    )

    # 断言：删除接口成功，随后精确查询不到目标角色
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('角色管理接口')
@allure.title('多个角色可以通过一个请求批量删除')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_batch_delete_roles(role_api, seeded_roles):
    result = role_api.delete_roles([role['role_id'] for role in seeded_roles])
    remaining = []
    for role in seeded_roles:
        remaining.extend(exact_roles(
            role_api.list_roles(roleName=role['role_name']),
            role['role_name'],
        ))

    # 断言：批量删除成功，两个目标角色均不存在
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert remaining == [], remaining


@allure.feature('系统管理')
@allure.story('角色管理接口')
@allure.title('按角色名称导出的 Excel 包含目标角色')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_export_role(role_api, seeded_role):
    result = role_api.export_roles(roleName=seeded_role['role_name'])
    values = xlsx_text_values(result.content)

    # 断言：返回有效 XLSX，且内容包含筛选角色及其权限字符
    assert result.status_code == 200, result
    assert result.content_type.startswith(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ), result.headers
    assert result.content.startswith(b'PK\x03\x04')
    assert seeded_role['role_name'] in values, values
    assert seeded_role['role_key'] in values, values
