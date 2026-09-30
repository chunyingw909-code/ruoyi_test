import allure
import pytest

from common.xlsx_utils import xlsx_text_values


def exact_login_logs(result, username):
    return [
        row for row in result.get('rows', [])
        if row.get('userName') == username
    ]


@allure.feature('系统管理')
@allure.story('登录日志接口')
@allure.title('登录日志可按用户名筛选出失败登录')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_list_login_log_with_filter(logininfor_api, seeded_login_log):
    username = seeded_login_log['username']
    result = logininfor_api.list_logs(
        userName=username,
        status='1',
        pageNum=1,
        pageSize=10,
    )
    rows = exact_login_logs(result, username)

    # 断言：精确筛选只返回该账号的失败登录，提示与登录接口一致
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['total'] >= 1, result
    assert len(rows) >= 1, result
    assert rows[0]['userName'] == username, rows[0]
    assert str(rows[0]['status']) == '1', rows[0]
    assert '用户不存在/密码错误' in str(rows[0].get('msg')), rows[0]


@allure.feature('系统管理')
@allure.story('登录日志接口')
@allure.title('按用户名导出的 Excel 包含这次失败登录')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_export_login_log(logininfor_api, seeded_login_log, oper_log_guard):
    oper_log_guard.register_marker(seeded_login_log['username'])
    result = logininfor_api.export_logs(userName=seeded_login_log['username'])
    values = xlsx_text_values(result.content)

    # 断言：返回有效 XLSX，且内容包含该账号和失败原因
    assert result.status_code == 200, result
    assert result.content.startswith(b'PK\x03\x04')
    assert seeded_login_log['username'] in values, values
    assert '用户不存在/密码错误' in values, values


@allure.feature('系统管理')
@allure.story('登录日志接口')
@allure.title('解锁只清除该账号的登录失败计数')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_unlock_login_user(logininfor_api, seeded_login_log):
    result = logininfor_api.unlock(seeded_login_log['username'])
    rows = exact_login_logs(
        logininfor_api.list_logs(userName=seeded_login_log['username']),
        seeded_login_log['username'],
    )

    # 断言：解锁成功，登录日志本身还在
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) >= 1, rows


@allure.feature('系统管理')
@allure.story('登录日志接口')
@allure.title('按访问编号删除后列表中不再存在该日志')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_delete_login_log(logininfor_api, seeded_login_log, oper_log_guard):
    oper_log_guard.register_url(
        f"/monitor/logininfor/{seeded_login_log['info_id']}"
    )
    result = logininfor_api.delete_log(seeded_login_log['info_id'])
    rows = exact_login_logs(
        logininfor_api.list_logs(userName=seeded_login_log['username']),
        seeded_login_log['username'],
    )
    remaining = [
        row for row in rows if row.get('infoId') == seeded_login_log['info_id']
    ]

    # 断言：删除接口成功，这条访问编号不再出现
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert remaining == [], rows


@allure.feature('系统管理')
@allure.story('登录日志接口')
@allure.title('多条登录日志可以通过一个请求批量删除')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_batch_delete_login_logs(logininfor_api, seeded_login_logs, oper_log_guard):
    info_ids = [item['info_id'] for item in seeded_login_logs]
    oper_log_guard.register_url(
        '/monitor/logininfor/' + ','.join(str(info_id) for info_id in info_ids)
    )
    result = logininfor_api.delete_logs(info_ids)
    remaining = []
    for item in seeded_login_logs:
        rows = exact_login_logs(
            logininfor_api.list_logs(userName=item['username']),
            item['username'],
        )
        remaining.extend(
            row for row in rows if row.get('infoId') in info_ids
        )

    # 断言：批量删除成功，两条目标日志均不存在
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert remaining == [], remaining
