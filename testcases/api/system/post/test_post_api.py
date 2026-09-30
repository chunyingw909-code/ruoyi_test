import allure
import pytest

from common.utils import read_yaml
from common.xlsx_utils import xlsx_text_values


add_error_data = read_yaml('data/system/post_api_errors.yaml')


def exact_posts(result, post_name):
    return [
        row for row in result.get('rows', [])
        if row.get('postName') == post_name
    ]


@allure.feature('系统管理')
@allure.story('岗位管理接口')
@allure.title('岗位列表支持名称筛选和分页')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_list_post_with_filter_and_pagination(post_api, seeded_post):
    result = post_api.list_posts(
        postName=seeded_post['post_name'],
        pageNum=1,
        pageSize=10,
    )
    rows = exact_posts(result, seeded_post['post_name'])

    # 断言：列表接口成功，精确筛选只返回目标岗位
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['total'] == 1, result
    assert len(rows) == 1, rows
    assert rows[0]['postCode'] == seeded_post['post_code']


@allure.feature('系统管理')
@allure.story('岗位管理接口')
@allure.title('新增岗位后可以按名称查询')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_add_and_list_post(post_api, unique_post_identity, track_test_post):
    identity = unique_post_identity
    result = post_api.add_post(
        identity['post_name'],
        identity['post_code'],
        post_sort=20,
    )
    rows = track_test_post(identity['post_name'])

    # 断言：新增成功，岗位名称、编码和排序均已落库
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) == 1, rows
    assert rows[0]['postCode'] == identity['post_code']
    assert rows[0]['postSort'] == 20


@allure.feature('系统管理')
@allure.story('岗位管理接口')
@allure.title('新增岗位异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_post_validation(post_api, track_test_post, case):
    try:
        result = post_api.add_post(case['post_name'], case['post_code'])
    finally:
        if case['post_name'].startswith('AUTOTEST-post-'):
            track_test_post(case['post_name'])

    # 断言：必填字段缺失时业务层拒绝新增并返回对应提示
    assert result.status_code == 200, result
    assert result['code'] == 500, result
    assert case['expect'] in result['msg'], result


@allure.feature('系统管理')
@allure.story('岗位管理接口')
@allure.title('岗位名称和岗位编码不能重复')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_add_post_rejects_duplicate_identity(
    post_api,
    seeded_post,
    unique_post_identity,
    track_test_post,
):
    try:
        duplicate_name = post_api.add_post(
            seeded_post['post_name'],
            unique_post_identity['post_code'],
        )
    finally:
        track_test_post(seeded_post['post_name'])
    duplicate_code_name = f"{unique_post_identity['post_name']}-code"
    try:
        duplicate_code = post_api.add_post(
            duplicate_code_name,
            seeded_post['post_code'],
        )
    finally:
        track_test_post(duplicate_code_name)

    # 断言：名称重复和编码重复均被拒绝
    assert duplicate_name['code'] == 500, duplicate_name
    assert '岗位名称已存在' in duplicate_name['msg'], duplicate_name
    assert duplicate_code['code'] == 500, duplicate_code
    assert '岗位编码已存在' in duplicate_code['msg'], duplicate_code


@allure.feature('系统管理')
@allure.story('岗位管理接口')
@allure.title('岗位详情返回完整基础信息')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_get_post_detail(post_api, seeded_post):
    result = post_api.get_post(seeded_post['post_id'])

    # 断言：详情与预置岗位一致
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['data']['postId'] == seeded_post['post_id'], result
    assert result['data']['postName'] == seeded_post['post_name'], result
    assert result['data']['postCode'] == seeded_post['post_code'], result


@allure.feature('系统管理')
@allure.story('岗位管理接口')
@allure.title('修改岗位名称、排序、状态和备注后详情同步更新')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_update_post(post_api, seeded_post):
    new_name = f"{seeded_post['post_name']}-updated"
    result = post_api.update_post(
        seeded_post['post_id'],
        new_name,
        seeded_post['post_code'],
        post_sort=30,
        status='1',
        remark='接口修改岗位',
    )
    detail = post_api.get_post(seeded_post['post_id'])

    # 断言：修改成功，详情接口返回更新后的关键字段
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert detail['data']['postName'] == new_name, detail
    assert detail['data']['postSort'] == 30, detail
    assert detail['data']['status'] == '1', detail
    assert detail['data']['remark'] == '接口修改岗位', detail


@allure.feature('系统管理')
@allure.story('岗位管理接口')
@allure.title('删除岗位后列表中不再存在该岗位')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_delete_post(post_api, seeded_post):
    result = post_api.delete_post(seeded_post['post_id'])
    rows = exact_posts(
        post_api.list_posts(postName=seeded_post['post_name']),
        seeded_post['post_name'],
    )

    # 断言：删除接口成功，随后精确查询不到目标岗位
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('岗位管理接口')
@allure.title('多个岗位可以通过一个请求批量删除')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_batch_delete_posts(post_api, seeded_posts):
    result = post_api.delete_posts([post['post_id'] for post in seeded_posts])
    remaining = []
    for post in seeded_posts:
        remaining.extend(exact_posts(
            post_api.list_posts(postName=post['post_name']),
            post['post_name'],
        ))

    # 断言：批量删除成功，两个目标岗位均不存在
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert remaining == [], remaining


@allure.feature('系统管理')
@allure.story('岗位管理接口')
@allure.title('按岗位名称导出的 Excel 包含目标岗位')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_export_post(post_api, seeded_post):
    result = post_api.export_posts(postName=seeded_post['post_name'])
    values = xlsx_text_values(result.content)

    # 断言：返回有效 XLSX，且内容包含筛选岗位及其编码
    assert result.status_code == 200, result
    assert result.content_type.startswith(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ), result.headers
    assert result.content.startswith(b'PK\x03\x04')
    assert seeded_post['post_name'] in values, values
    assert seeded_post['post_code'] in values, values
