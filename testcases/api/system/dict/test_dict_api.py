import allure
import pytest

from common.utils import read_yaml
from common.xlsx_utils import xlsx_text_values


add_error_data = read_yaml('data/system/dict_api_errors.yaml')
data_error_data = read_yaml('data/system/dict_data_api_errors.yaml')


def exact_types(result, dict_name):
    return [
        row for row in result.get('rows', [])
        if row.get('dictName') == dict_name
    ]


def exact_data(result, dict_label):
    return [
        row for row in result.get('rows', [])
        if row.get('dictLabel') == dict_label
    ]


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('字典类型列表支持名称筛选和分页')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_list_dict_type_with_filter_and_pagination(dict_type_api, seeded_dict_type):
    result = dict_type_api.list_dict_types(
        dictName=seeded_dict_type['dict_name'],
        pageNum=1,
        pageSize=10,
    )
    rows = exact_types(result, seeded_dict_type['dict_name'])

    # 断言：列表接口成功，精确筛选只返回目标字典类型
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['total'] == 1, result
    assert len(rows) == 1, rows
    assert rows[0]['dictType'] == seeded_dict_type['dict_type']


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('新增字典类型后可以按名称查询')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_add_and_list_dict_type(dict_type_api, unique_dict_identity, track_test_dict_type):
    identity = unique_dict_identity
    result = dict_type_api.add_dict_type(
        identity['dict_name'],
        identity['dict_type'],
    )
    rows = track_test_dict_type(identity['dict_name'])

    # 断言：新增成功，字典名称和字典类型均已落库
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) == 1, rows
    assert rows[0]['dictType'] == identity['dict_type']


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('新增字典类型异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_dict_type_validation(dict_type_api, track_test_dict_type, case):
    try:
        result = dict_type_api.add_dict_type(case['dict_name'], case['dict_type'])
    finally:
        if case['dict_name'].startswith('AUTOTEST-dict-'):
            track_test_dict_type(case['dict_name'])

    # 断言：非法字典类型被业务层拒绝。空类型同时踩中非空和格式两条校验，返回哪一条不固定
    expected = case['expect']
    if isinstance(expected, str):
        expected = [expected]
    assert result.status_code == 200, result
    assert result['code'] == 500, result
    assert any(item in result['msg'] for item in expected), result


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('字典类型不能重复')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_add_dict_type_rejects_duplicate_type(
    dict_type_api,
    seeded_dict_type,
    unique_dict_identity,
    track_test_dict_type,
):
    try:
        result = dict_type_api.add_dict_type(
            unique_dict_identity['dict_name'],
            seeded_dict_type['dict_type'],
        )
    finally:
        track_test_dict_type(unique_dict_identity['dict_name'])

    # 断言：重复的字典类型被拒绝
    assert result['code'] == 500, result
    assert '字典类型已存在' in result['msg'], result


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('字典类型详情和选项列表包含目标字典')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_get_dict_type_detail_and_options(dict_type_api, seeded_dict_type):
    detail = dict_type_api.get_dict_type(seeded_dict_type['dict_id'])
    options = dict_type_api.optionselect()
    matched = [
        row for row in options.get('data', [])
        if row.get('dictType') == seeded_dict_type['dict_type']
    ]

    # 断言：详情与预置数据一致，下拉选项也能找到该字典类型
    assert detail.status_code == 200, detail
    assert detail['code'] == 200, detail
    assert detail['data']['dictName'] == seeded_dict_type['dict_name'], detail
    assert detail['data']['dictType'] == seeded_dict_type['dict_type'], detail
    assert options['code'] == 200, options
    assert len(matched) == 1, matched


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('修改字典名称、状态和备注后详情同步更新')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_update_dict_type(dict_type_api, seeded_dict_type):
    new_name = f"{seeded_dict_type['dict_name']}-updated"
    result = dict_type_api.update_dict_type(
        seeded_dict_type['dict_id'],
        new_name,
        seeded_dict_type['dict_type'],
        status='1',
        remark='接口修改字典',
    )
    detail = dict_type_api.get_dict_type(seeded_dict_type['dict_id'])

    # 断言：修改成功，详情接口返回更新后的关键字段
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert detail['data']['dictName'] == new_name, detail
    assert detail['data']['status'] == '1', detail
    assert detail['data']['remark'] == '接口修改字典', detail


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('已分配字典数据的字典类型不能删除')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_delete_dict_type_rejected_when_data_exists(
    dict_type_api,
    seeded_dict_type,
    seeded_dict_data,
    oper_log_guard,
):
    oper_log_guard.register_url(f"/system/dict/type/{seeded_dict_type['dict_id']}")
    result = dict_type_api.delete_dict_type(seeded_dict_type['dict_id'])
    detail = dict_type_api.get_dict_type(seeded_dict_type['dict_id'])

    # 断言：类型下已有字典数据时删除被拒绝，字典类型仍然存在
    assert result.status_code == 200, result
    assert result['code'] == 500, result
    assert '已分配,不能删除' in result['msg'], result
    assert detail['data']['dictType'] == seeded_dict_type['dict_type'], detail
    assert seeded_dict_data['dict_type'] == seeded_dict_type['dict_type']


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('删除字典类型后列表中不再存在该类型')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_delete_dict_type(dict_type_api, seeded_dict_type, oper_log_guard):
    oper_log_guard.register_url(f"/system/dict/type/{seeded_dict_type['dict_id']}")
    result = dict_type_api.delete_dict_type(seeded_dict_type['dict_id'])
    rows = exact_types(
        dict_type_api.list_dict_types(dictName=seeded_dict_type['dict_name']),
        seeded_dict_type['dict_name'],
    )

    # 断言：删除接口成功，随后精确查询不到目标字典类型
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('多个字典类型可以通过一个请求批量删除')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_batch_delete_dict_types(dict_type_api, seeded_dict_types, oper_log_guard):
    dict_ids = [item['dict_id'] for item in seeded_dict_types]
    oper_log_guard.register_url(
        '/system/dict/type/' + ','.join(str(dict_id) for dict_id in dict_ids)
    )
    result = dict_type_api.delete_dict_types(dict_ids)
    remaining = []
    for item in seeded_dict_types:
        remaining.extend(exact_types(
            dict_type_api.list_dict_types(dictName=item['dict_name']),
            item['dict_name'],
        ))

    # 断言：批量删除成功，两个目标字典类型均不存在
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert remaining == [], remaining


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('按字典名称导出的 Excel 包含目标字典类型')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_export_dict_type(dict_type_api, seeded_dict_type):
    result = dict_type_api.export_dict_types(dictName=seeded_dict_type['dict_name'])
    values = xlsx_text_values(result.content)

    # 断言：返回有效 XLSX，且内容包含筛选字典的名称和类型
    assert result.status_code == 200, result
    assert result.content_type.startswith(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ), result.headers
    assert result.content.startswith(b'PK\x03\x04')
    assert seeded_dict_type['dict_name'] in values, values
    assert seeded_dict_type['dict_type'] in values, values


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('刷新字典缓存成功')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.api
def test_refresh_dict_cache(dict_type_api):
    result = dict_type_api.refresh_cache()

    # 断言：刷新缓存接口成功
    assert result.status_code == 200, result
    assert result['code'] == 200, result


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('新增字典数据后可以按标签查询，并出现在按类型取值的结果中')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_add_and_list_dict_data(
    dict_data_api,
    seeded_dict_type,
    track_test_dict_data,
):
    suffix = seeded_dict_type['dict_type'][-8:]
    label = f'AUTOTEST-label-{suffix}'
    value = f'autotest_{suffix}'
    result = dict_data_api.add_dict_data(
        label, value, seeded_dict_type['dict_type'], dictSort=3
    )
    rows = track_test_dict_data(seeded_dict_type['dict_type'], label)
    by_type = dict_data_api.list_by_type(seeded_dict_type['dict_type'])
    typed = [
        row for row in by_type.get('data', [])
        if row.get('dictLabel') == label
    ]

    # 断言：新增成功，列表和按类型取值都能查到该字典数据
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert len(rows) == 1, rows
    assert rows[0]['dictValue'] == value
    assert rows[0]['dictSort'] == 3
    assert by_type['code'] == 200, by_type
    assert len(typed) == 1, typed


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('新增字典数据异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.parametrize('case', data_error_data, ids=lambda x: x['desc'])
def test_add_dict_data_validation(
    dict_data_api,
    seeded_dict_type,
    track_test_dict_data,
    case,
):
    try:
        result = dict_data_api.add_dict_data(
            case['dict_label'],
            case['dict_value'],
            seeded_dict_type['dict_type'],
        )
    finally:
        if str(case['dict_label']).startswith('AUTOTEST-'):
            track_test_dict_data(seeded_dict_type['dict_type'], case['dict_label'])

    # 断言：缺少必填字段时业务层明确拒绝
    assert result.status_code == 200, result
    assert result['code'] == 500, result
    assert case['expect'] in result['msg'], result


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('字典数据详情返回完整基础信息')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_get_dict_data_detail(dict_data_api, seeded_dict_data):
    result = dict_data_api.get_dict_data(seeded_dict_data['dict_code'])

    # 断言：详情与预置字典数据一致
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert result['data']['dictCode'] == seeded_dict_data['dict_code'], result
    assert result['data']['dictLabel'] == seeded_dict_data['dict_label'], result
    assert result['data']['dictValue'] == seeded_dict_data['dict_value'], result
    assert result['data']['dictType'] == seeded_dict_data['dict_type'], result


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('修改字典标签、键值和排序后详情同步更新')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_update_dict_data(dict_data_api, seeded_dict_data, track_test_dict_data):
    new_label = f"{seeded_dict_data['dict_label']}-updated"
    result = dict_data_api.update_dict_data(
        seeded_dict_data['dict_code'],
        new_label,
        f"{seeded_dict_data['dict_value']}_new",
        seeded_dict_data['dict_type'],
        dictSort=8,
        remark='接口修改字典数据',
    )
    track_test_dict_data(seeded_dict_data['dict_type'], new_label)
    detail = dict_data_api.get_dict_data(seeded_dict_data['dict_code'])

    # 断言：修改成功，详情接口返回更新后的关键字段
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert detail['data']['dictLabel'] == new_label, detail
    assert detail['data']['dictValue'] == f"{seeded_dict_data['dict_value']}_new", detail
    assert detail['data']['dictSort'] == 8, detail
    assert detail['data']['remark'] == '接口修改字典数据', detail


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('删除字典数据后列表中不再存在该数据')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_delete_dict_data(dict_data_api, seeded_dict_data, oper_log_guard):
    oper_log_guard.register_url(f"/system/dict/data/{seeded_dict_data['dict_code']}")
    result = dict_data_api.delete_dict_data(seeded_dict_data['dict_code'])
    rows = exact_data(
        dict_data_api.list_dict_data(
            dictType=seeded_dict_data['dict_type'],
            dictLabel=seeded_dict_data['dict_label'],
        ),
        seeded_dict_data['dict_label'],
    )

    # 断言：删除接口成功，随后精确查询不到目标字典数据
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('多条字典数据可以通过一个请求批量删除')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_batch_delete_dict_data(dict_data_api, seeded_dict_data_rows, oper_log_guard):
    dict_codes = [item['dict_code'] for item in seeded_dict_data_rows]
    oper_log_guard.register_url(
        '/system/dict/data/' + ','.join(str(dict_code) for dict_code in dict_codes)
    )
    result = dict_data_api.delete_dict_data_batch(dict_codes)
    remaining = []
    for item in seeded_dict_data_rows:
        remaining.extend(exact_data(
            dict_data_api.list_dict_data(
                dictType=item['dict_type'], dictLabel=item['dict_label']
            ),
            item['dict_label'],
        ))

    # 断言：批量删除成功，两条目标字典数据均不存在
    assert result.status_code == 200, result
    assert result['code'] == 200, result
    assert remaining == [], remaining


@allure.feature('系统管理')
@allure.story('字典管理接口')
@allure.title('按字典类型导出的 Excel 包含目标字典数据')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
def test_export_dict_data(dict_data_api, seeded_dict_data, oper_log_guard):
    oper_log_guard.register_marker(seeded_dict_data['dict_type'])
    result = dict_data_api.export_dict_data(dictType=seeded_dict_data['dict_type'])
    values = xlsx_text_values(result.content)

    # 断言：返回有效 XLSX，且内容包含筛选出的字典标签和键值
    assert result.status_code == 200, result
    assert result.content.startswith(b'PK\x03\x04')
    assert seeded_dict_data['dict_label'] in values, values
    assert seeded_dict_data['dict_value'] in values, values
