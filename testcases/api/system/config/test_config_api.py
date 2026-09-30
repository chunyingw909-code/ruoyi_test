import allure
import pytest

from common.utils import read_yaml
from common.xlsx_utils import xlsx_text_values


add_error_data = read_yaml('data/system/config_api_errors.yaml')


def exact_configs(result, config_name):
    return [
        row for row in result.get('rows', [])
        if row.get('configName') == config_name
    ]


@allure.feature('系统管理')
@allure.story('参数设置接口')
@allure.title('参数列表支持名称筛选和分页')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_list_config_with_filter_and_pagination(config_api, seeded_config):
    result = config_api.list_configs(
        configName=seeded_config['config_name'],
        pageNum=1,
        pageSize=10,
    )
    rows = exact_configs(result, seeded_config['config_name'])

    # 断言：列表接口成功，精确筛选只返回目标参数
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['total'] == 1, result
    assert len(rows) == 1, rows
    assert rows[0]['configKey'] == seeded_config['config_key']
    assert rows[0]['configType'] == 'N'


@allure.feature('系统管理')
@allure.story('参数设置接口')
@allure.title('新增参数后可以按名称查询，并按键名取到键值')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_add_and_get_config(config_api, unique_config_identity, track_test_config):
    identity = unique_config_identity
    result = config_api.add_config(
        identity['config_name'],
        identity['config_key'],
        '接口新增参数值',
    )
    rows = track_test_config(identity['config_name'])
    by_key = config_api.get_value_by_key(identity['config_key'])

    # 断言：新增成功。按键名查询把键值放在 msg，这是若依 success(String) 的返回方式
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) == 1, rows
    assert rows[0]['configValue'] == '接口新增参数值'
    assert rows[0]['configType'] == 'N'
    assert by_key['code'] == 200, by_key
    assert by_key['msg'] == '接口新增参数值', by_key


@allure.feature('系统管理')
@allure.story('参数设置接口')
@allure.title('新增参数异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_config_validation(config_api, track_test_config, case):
    try:
        result = config_api.add_config(
            case['config_name'],
            case['config_key'],
            case['config_value'],
        )
    finally:
        if case['config_name'].startswith('AUTOTEST-config-'):
            track_test_config(case['config_name'])

    # 断言：必填字段缺失时业务层拒绝新增并返回对应提示
    assert result.status_code == 200, result
    assert result['code'] == 500, result
    assert case['expect'] in result['msg'], result


@allure.feature('系统管理')
@allure.story('参数设置接口')
@allure.title('参数键名不能重复')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_add_config_rejects_duplicate_key(
    config_api,
    seeded_config,
    unique_config_identity,
    track_test_config,
):
    try:
        result = config_api.add_config(
            unique_config_identity['config_name'],
            seeded_config['config_key'],
        )
    finally:
        track_test_config(unique_config_identity['config_name'])

    # 断言：重复的参数键名被拒绝
    assert result['code'] == 500, result
    assert '参数键名已存在' in result['msg'], result


@allure.feature('系统管理')
@allure.story('参数设置接口')
@allure.title('参数详情返回完整基础信息')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_get_config_detail(config_api, seeded_config):
    result = config_api.get_config(seeded_config['config_id'])

    # 断言：详情与预置参数一致
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['data']['configId'] == seeded_config['config_id'], result
    assert result['data']['configName'] == seeded_config['config_name'], result
    assert result['data']['configKey'] == seeded_config['config_key'], result
    assert result['data']['configValue'] == seeded_config['config_value'], result


@allure.feature('系统管理')
@allure.story('参数设置接口')
@allure.title('修改参数键值和备注后详情同步更新')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_update_config(config_api, seeded_config):
    result = config_api.update_config(
        seeded_config['config_id'],
        seeded_config['config_name'],
        seeded_config['config_key'],
        '接口修改参数值',
        remark='接口修改参数',
    )
    detail = config_api.get_config(seeded_config['config_id'])
    by_key = config_api.get_value_by_key(seeded_config['config_key'])

    # 断言：修改成功，详情和按键名取值都返回新键值
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert detail['data']['configValue'] == '接口修改参数值', detail
    assert detail['data']['remark'] == '接口修改参数', detail
    assert by_key['msg'] == '接口修改参数值', by_key


@allure.feature('系统管理')
@allure.story('参数设置接口')
@allure.title('内置参数不能删除')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_delete_builtin_config_rejected(config_api, oper_log_guard):
    result = config_api.list_configs(
        configKey='sys.account.captchaEnabled', pageNum=1, pageSize=10
    )
    rows = [
        row for row in result.get('rows', [])
        if row.get('configKey') == 'sys.account.captchaEnabled'
    ]
    assert len(rows) == 1, result
    oper_log_guard.register_url(f"/system/config/{rows[0]['configId']}")
    rejected = config_api.delete_config(rows[0]['configId'])
    still_there = config_api.get_config(rows[0]['configId'])

    # 断言：内置参数删除被拒绝，参数本身仍然存在
    assert rejected.status_code == 200, rejected
    assert rejected['code'] == 500, rejected
    assert '不能删除' in rejected['msg'], rejected
    assert 'sys.account.captchaEnabled' in rejected['msg'], rejected
    assert still_there['data']['configKey'] == 'sys.account.captchaEnabled', still_there


@allure.feature('系统管理')
@allure.story('参数设置接口')
@allure.title('删除非内置参数后列表中不再存在该参数')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_delete_config(config_api, seeded_config, oper_log_guard):
    oper_log_guard.register_url(f"/system/config/{seeded_config['config_id']}")
    result = config_api.delete_config(seeded_config['config_id'])
    rows = exact_configs(
        config_api.list_configs(configName=seeded_config['config_name']),
        seeded_config['config_name'],
    )

    # 断言：删除接口成功，随后精确查询不到目标参数
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('参数设置接口')
@allure.title('多个参数可以通过一个请求批量删除')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_batch_delete_configs(config_api, seeded_configs, oper_log_guard):
    config_ids = [item['config_id'] for item in seeded_configs]
    oper_log_guard.register_url(
        '/system/config/' + ','.join(str(config_id) for config_id in config_ids)
    )
    result = config_api.delete_configs(config_ids)
    remaining = []
    for item in seeded_configs:
        remaining.extend(exact_configs(
            config_api.list_configs(configName=item['config_name']),
            item['config_name'],
        ))

    # 断言：批量删除成功，两个目标参数均不存在
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert remaining == [], remaining


@allure.feature('系统管理')
@allure.story('参数设置接口')
@allure.title('按参数名称导出的 Excel 包含目标参数')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_export_config(config_api, seeded_config):
    result = config_api.export_configs(configName=seeded_config['config_name'])
    values = xlsx_text_values(result.content)

    # 断言：返回有效 XLSX，且内容包含筛选参数的名称和键名
    assert result.status_code == 200, result
    assert result.content.startswith(b'PK\x03\x04')
    assert seeded_config['config_name'] in values, values
    assert seeded_config['config_key'] in values, values


@allure.feature('系统管理')
@allure.story('参数设置接口')
@allure.title('刷新参数缓存成功')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.api
def test_refresh_config_cache(config_api):
    result = config_api.refresh_cache()

    # 断言：刷新缓存接口成功
    assert result.status_code == 200, result
    assert result['code'] == 200, result
