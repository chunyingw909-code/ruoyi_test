import allure
import pytest

from common.utils import read_yaml


add_error_data = read_yaml('data/system/menu_api_errors.yaml')


def exact_menus(result, menu_name):
    return [
        row for row in result.get('data', [])
        if row.get('menuName') == menu_name
    ]


@allure.feature('系统管理')
@allure.story('菜单管理接口')
@allure.title('菜单列表支持按名称精确筛选')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_list_menu_with_name_filter(menu_api, seeded_menu):
    result = menu_api.list_menus(menuName=seeded_menu['menu_name'])
    rows = exact_menus(result, seeded_menu['menu_name'])

    # 断言：列表接口成功，筛选结果只有目标菜单
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) == 1, rows
    assert rows[0]['path'] == seeded_menu['path']


@allure.feature('系统管理')
@allure.story('菜单管理接口')
@allure.title('新增顶级目录后可以按名称查询')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_add_and_list_menu(menu_api, unique_menu_identity, track_test_menu):
    identity = unique_menu_identity
    result = menu_api.add_menu(
        identity['menu_name'],
        identity['path'],
        orderNum=20,
        remark='接口新增菜单',
    )
    rows = track_test_menu(identity['menu_name'])

    # 断言：新增成功，目录名称、路由和排序均已落库
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) == 1, rows
    assert rows[0]['menuType'] == 'M'
    assert rows[0]['path'] == identity['path']
    assert rows[0]['orderNum'] == 20


@allure.feature('系统管理')
@allure.story('菜单管理接口')
@allure.title('新增菜单异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_menu_validation(menu_api, track_test_menu, case):
    try:
        result = menu_api.add_menu(case['menu_name'], case['path'])
    finally:
        if case['menu_name'].startswith('AUTOTEST-menu-'):
            track_test_menu(case['menu_name'])

    # 断言：必填菜单名称缺失时业务层明确拒绝
    assert result.status_code == 200, result
    assert result['code'] == case['expected_code'], result
    assert result['msg'] == case['expected_message'], result


@allure.feature('系统管理')
@allure.story('菜单管理接口')
@allure.title('同一上级菜单下不能存在重复菜单名称')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_add_menu_rejects_duplicate_name(
    menu_api,
    seeded_menu,
    unique_menu_identity,
):
    result = menu_api.add_menu(
        seeded_menu['menu_name'],
        unique_menu_identity['path'],
    )

    # 断言：同一父级下的重名目录被业务层拒绝
    assert result.status_code == 200, result
    assert result['code'] == 500, result
    assert '菜单名称已存在' in result['msg'], result


@allure.feature('系统管理')
@allure.story('菜单管理接口')
@allure.title('菜单详情和选择树返回完整层级信息')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.api
def test_get_menu_detail_and_tree(menu_api, seeded_menu):
    detail = menu_api.get_menu(seeded_menu['menu_id'])
    tree = menu_api.tree_select()

    # 断言：详情与预置数据一致，菜单树提供层级节点
    assert detail.status_code == 200, detail
    assert detail['code'] == 200, detail
    assert detail['data']['menuName'] == seeded_menu['menu_name'], detail
    assert detail['data']['path'] == seeded_menu['path'], detail
    assert tree.status_code == 200, tree
    assert tree['code'] == 200, tree
    assert isinstance(tree['data'], list) and tree['data'], tree
    assert {'id', 'label'} <= set(tree['data'][0]), tree


@allure.feature('系统管理')
@allure.story('菜单管理接口')
@allure.title('修改菜单名称、路由和排序后详情同步更新')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_update_menu(menu_api, seeded_menu):
    new_name = f"{seeded_menu['menu_name']}-updated"
    new_path = f"{seeded_menu['path']}-updated"
    result = menu_api.update_menu(
        seeded_menu['menu_id'],
        new_name,
        new_path,
        orderNum=30,
    )
    detail = menu_api.get_menu(seeded_menu['menu_id'])

    # 断言：修改成功，详情接口返回更新后的关键字段
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert detail['data']['menuName'] == new_name, detail
    assert detail['data']['path'] == new_path, detail
    assert detail['data']['orderNum'] == 30, detail


@allure.feature('系统管理')
@allure.story('菜单管理接口')
@allure.title('删除菜单后列表中不再存在该菜单')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_delete_menu(menu_api, seeded_menu):
    result = menu_api.delete_menu(seeded_menu['menu_id'])
    rows = exact_menus(
        menu_api.list_menus(menuName=seeded_menu['menu_name']),
        seeded_menu['menu_name'],
    )

    # 断言：删除接口成功，随后精确查询不到目标菜单
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert rows == [], rows
