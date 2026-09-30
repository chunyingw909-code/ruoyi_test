import allure
import pytest

from common.utils import read_yaml


add_error_data = read_yaml('data/system/notice_api_errors.yaml')


def exact_notices(result, notice_title):
    return [
        row for row in result.get('rows', [])
        if row.get('noticeTitle') == notice_title
    ]


@allure.feature('系统管理')
@allure.story('通知公告接口')
@allure.title('公告列表支持标题筛选和分页')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_list_notice_with_filter_and_pagination(notice_api, seeded_notice):
    result = notice_api.list_notices(
        noticeTitle=seeded_notice['notice_title'],
        pageNum=1,
        pageSize=10,
    )
    rows = exact_notices(result, seeded_notice['notice_title'])

    # 断言：列表接口成功，精确筛选只返回目标公告
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['total'] == 1, result
    assert len(rows) == 1, rows
    assert rows[0]['noticeType'] == '1'
    assert rows[0]['status'] == '0'


@allure.feature('系统管理')
@allure.story('通知公告接口')
@allure.title('新增公告后可以按标题查询')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_add_and_list_notice(notice_api, unique_notice_title, track_test_notice):
    result = notice_api.add_notice(
        unique_notice_title,
        notice_type='2',
        noticeContent='接口新增公告内容',
    )
    rows = track_test_notice(unique_notice_title)

    # 断言：新增成功，标题、类型和内容均已落库
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) == 1, rows
    assert rows[0]['noticeType'] == '2'
    assert rows[0]['noticeContent'] == '接口新增公告内容'


@allure.feature('系统管理')
@allure.story('通知公告接口')
@allure.title('新增公告异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_notice_validation(notice_api, track_test_notice, case):
    try:
        result = notice_api.add_notice(case['notice_title'])
    finally:
        if case['notice_title'].startswith('AUTOTEST-notice-'):
            track_test_notice(case['notice_title'])

    # 断言：非法公告标题被业务层拒绝，且拒绝原因与场景一致
    assert result.status_code == 200, result
    assert result['code'] == 500, result
    assert case['expect'] in result['msg'], result


@allure.feature('系统管理')
@allure.story('通知公告接口')
@allure.title('公告详情返回完整基础信息')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_get_notice_detail(notice_api, seeded_notice):
    result = notice_api.get_notice(seeded_notice['notice_id'])

    # 断言：详情与预置公告一致
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['data']['noticeId'] == seeded_notice['notice_id'], result
    assert result['data']['noticeTitle'] == seeded_notice['notice_title'], result
    assert result['data']['noticeContent'] == '自动化测试公告', result


@allure.feature('系统管理')
@allure.story('通知公告接口')
@allure.title('修改公告标题、类型和状态后详情同步更新')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_update_notice(notice_api, seeded_notice, track_test_notice):
    new_title = f"{seeded_notice['notice_title']}-updated"
    result = notice_api.update_notice(
        seeded_notice['notice_id'],
        new_title,
        notice_type='2',
        status='1',
        noticeContent='接口修改公告',
    )
    track_test_notice(new_title)
    detail = notice_api.get_notice(seeded_notice['notice_id'])

    # 断言：修改成功，详情接口返回更新后的关键字段
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert detail['data']['noticeTitle'] == new_title, detail
    assert detail['data']['noticeType'] == '2', detail
    assert detail['data']['status'] == '1', detail
    assert detail['data']['noticeContent'] == '接口修改公告', detail


@allure.feature('系统管理')
@allure.story('通知公告接口')
@allure.title('删除公告后列表中不再存在该公告')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_delete_notice(notice_api, seeded_notice, oper_log_guard):
    oper_log_guard.register_url(f"/system/notice/{seeded_notice['notice_id']}")
    result = notice_api.delete_notice(seeded_notice['notice_id'])
    rows = exact_notices(
        notice_api.list_notices(noticeTitle=seeded_notice['notice_title']),
        seeded_notice['notice_title'],
    )

    # 断言：删除接口成功，随后精确查询不到目标公告
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('通知公告接口')
@allure.title('多条公告可以通过一个请求批量删除')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_batch_delete_notices(notice_api, seeded_notices, oper_log_guard):
    notice_ids = [item['notice_id'] for item in seeded_notices]
    oper_log_guard.register_url(
        '/system/notice/' + ','.join(str(notice_id) for notice_id in notice_ids)
    )
    result = notice_api.delete_notices(notice_ids)
    remaining = []
    for item in seeded_notices:
        remaining.extend(exact_notices(
            notice_api.list_notices(noticeTitle=item['notice_title']),
            item['notice_title'],
        ))

    # 断言：批量删除成功，两条目标公告均不存在
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert remaining == [], remaining


@allure.feature('系统管理')
@allure.story('通知公告接口')
@allure.title('首页公告未读，标记已读后已读用户列表出现当前账号')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_mark_notice_read(notice_api, seeded_notice):
    before = notice_api.list_top()
    before_row = next(
        (
            row for row in before.get('data', [])
            if row.get('noticeId') == seeded_notice['notice_id']
        ),
        None,
    )
    marked = notice_api.mark_read(seeded_notice['notice_id'])
    after = notice_api.list_top()
    after_row = next(
        (
            row for row in after.get('data', [])
            if row.get('noticeId') == seeded_notice['notice_id']
        ),
        None,
    )
    readers = notice_api.list_read_users(seeded_notice['notice_id'])
    admin_rows = [
        row for row in readers.get('rows', [])
        if row.get('userName') == 'admin'
    ]

    # 断言：新公告出现在首页且未读，标记后变为已读，已读用户包含 admin
    assert before['code'] == 200, before
    assert before_row is not None, before
    assert before_row['isRead'] is False, before_row
    assert marked['code'] == 200, marked
    assert after_row is not None, after
    assert after_row['isRead'] is True, after_row
    assert readers['code'] == 200, readers
    assert len(admin_rows) == 1, readers
