import allure
import pytest

from common.xlsx_utils import xlsx_text_values


def exact_oper_logs(result, oper_id):
    return [
        row for row in result.get('rows', [])
        if row.get('operId') == oper_id
    ]


def xlsx_has(values, text):
    return any(text in value for value in values)


@allure.feature('系统管理')
@allure.story('操作日志接口')
@allure.title('操作日志可按模块、类型、人员和状态筛选')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_list_oper_log_with_filter(operlog_api, seeded_oper_log):
    result = operlog_api.list_logs(
        title='字典类型',
        businessType=1,
        operName='admin',
        status=0,
        pageNum=1,
        pageSize=10,
    )
    rows = exact_oper_logs(result, seeded_oper_log['oper_id'])

    # 断言：筛选结果包含本次新增字典写下的日志，且模块、类型和请求参数正确
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) == 1, result
    assert rows[0]['title'] == '字典类型', rows[0]
    assert str(rows[0]['businessType']) == '1', rows[0]
    assert rows[0]['operName'] == 'admin', rows[0]
    assert str(rows[0]['status']) == '0', rows[0]
    assert seeded_oper_log['dict_name'] in str(rows[0].get('operParam')), rows[0]


@allure.feature('系统管理')
@allure.story('操作日志接口')
@allure.title('按系统模块导出的 Excel 包含本次操作')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_export_oper_log(operlog_api, seeded_oper_log):
    result = operlog_api.export_logs(title='字典类型', businessType=1)
    values = xlsx_text_values(result.content)

    # 断言：返回有效 XLSX，且内容包含本次字典名称
    assert result.status_code == 200, result
    assert result.content.startswith(b'PK\x03\x04')
    assert xlsx_has(values, '字典类型'), values
    assert xlsx_has(values, seeded_oper_log['dict_name']), values


@allure.feature('系统管理')
@allure.story('操作日志接口')
@allure.title('按日志编号删除后列表中不再存在该日志')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_delete_oper_log(operlog_api, seeded_oper_log):
    result = operlog_api.delete_log(seeded_oper_log['oper_id'])
    rows = exact_oper_logs(
        operlog_api.list_logs(
            title='字典类型', pageNum=1, pageSize=100
        ),
        seeded_oper_log['oper_id'],
    )

    # 断言：删除接口成功，随后查询不到这条日志
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('操作日志接口')
@allure.title('多条操作日志可以通过一个请求批量删除')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_batch_delete_oper_logs(operlog_api, seeded_oper_logs):
    oper_ids = [item['oper_id'] for item in seeded_oper_logs]
    result = operlog_api.delete_logs(oper_ids)
    remaining = exact_oper_logs(
        operlog_api.list_logs(title='字典类型', pageNum=1, pageSize=100),
        oper_ids[0],
    )
    remaining.extend(exact_oper_logs(
        operlog_api.list_logs(title='字典类型', pageNum=1, pageSize=100),
        oper_ids[1],
    ))

    # 断言：批量删除成功，两条目标日志均不存在
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert remaining == [], remaining
