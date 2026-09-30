import allure
import pytest

from common.utils import read_yaml


add_error_data = read_yaml('data/system/dept_api_errors.yaml')


def exact_depts(result, dept_name):
    return [
        row for row in result.get('data', [])
        if row.get('deptName') == dept_name
    ]


@allure.feature('系统管理')
@allure.story('部门管理接口')
@allure.title('部门列表支持按名称精确筛选')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_list_dept_with_name_filter(dept_api, seeded_dept):
    result = dept_api.list_depts(deptName=seeded_dept['dept_name'])
    rows = exact_depts(result, seeded_dept['dept_name'])

    # 断言：列表接口成功，筛选结果只有目标部门
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) == 1, rows
    assert rows[0]['parentId'] == 100


@allure.feature('系统管理')
@allure.story('部门管理接口')
@allure.title('新增部门后可以按名称查询')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_add_and_list_dept(dept_api, unique_dept_name, track_test_dept):
    result = dept_api.add_dept(unique_dept_name, orderNum=20)
    rows = track_test_dept(unique_dept_name)

    # 断言：新增成功，部门名称和排序均已落库
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) == 1, rows
    assert rows[0]['orderNum'] == 20


@allure.feature('系统管理')
@allure.story('部门管理接口')
@allure.title('新增部门异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_dept_validation(dept_api, case):
    result = dept_api.add_dept(case['dept_name'])

    # 断言：必填部门名称缺失时业务层明确拒绝
    assert result.status_code == 200, result
    assert result['code'] == case['expected_code'], result
    assert result['msg'] == case['expected_message'], result


@allure.feature('系统管理')
@allure.story('部门管理接口')
@allure.title('同一上级部门下不能存在重复部门名称')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_add_dept_rejects_duplicate_name(dept_api, seeded_dept):
    result = dept_api.add_dept(seeded_dept['dept_name'])

    # 断言：同一上级下的重名部门被业务层拒绝
    assert result.status_code == 200, result
    assert result['code'] == 500, result
    assert '部门名称已存在' in result['msg'], result


@allure.feature('系统管理')
@allure.story('部门管理接口')
@allure.title('部门详情和排除自身的部门树结构正确')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.api
def test_get_dept_detail_and_exclude_tree(dept_api, seeded_dept):
    detail = dept_api.get_dept(seeded_dept['dept_id'])
    tree = dept_api.exclude_tree(seeded_dept['dept_id'])

    # 断言：详情与预置数据一致，排除接口不包含自身
    assert detail.status_code == 200, detail
    assert detail['data']['deptName'] == seeded_dept['dept_name'], detail
    assert tree.status_code == 200, tree
    assert all(
        row.get('deptId') != seeded_dept['dept_id']
        for row in tree.get('data', [])
    ), tree


@allure.feature('系统管理')
@allure.story('部门管理接口')
@allure.title('修改部门名称、排序和负责人后详情同步更新')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_update_dept(dept_api, seeded_dept):
    new_name = f"{seeded_dept['dept_name']}-updated"
    result = dept_api.update_dept(
        seeded_dept['dept_id'],
        new_name,
        orderNum=30,
        leader='接口修改负责人',
    )
    detail = dept_api.get_dept(seeded_dept['dept_id'])

    # 断言：修改成功，详情接口返回更新后的关键字段
    assert result['code'] == 200, result
    assert detail['data']['deptName'] == new_name, detail
    assert detail['data']['orderNum'] == 30, detail
    assert detail['data']['leader'] == '接口修改负责人', detail


@allure.feature('系统管理')
@allure.story('部门管理接口')
@allure.title('删除部门后列表中不再存在该部门')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_delete_dept(dept_api, seeded_dept):
    result = dept_api.delete_dept(seeded_dept['dept_id'])
    rows = exact_depts(
        dept_api.list_depts(deptName=seeded_dept['dept_name']),
        seeded_dept['dept_name'],
    )

    # 断言：删除接口成功，随后精确查询不到目标部门
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert rows == [], rows
