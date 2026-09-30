import pytest


# 字典管理接口 - 预置一个可供查询、更新和删除使用的字典类型
@pytest.fixture
def seeded_dict_type(create_test_dict_type):
    return create_test_dict_type(remark='接口预置字典')


# 字典管理接口 - 预置两个字典类型供批量删除使用
@pytest.fixture
def seeded_dict_types(create_test_dict_type):
    return [
        create_test_dict_type(remark='批量字典一'),
        create_test_dict_type(remark='批量字典二'),
    ]


# 字典管理接口 - 在预置字典类型下创建一条字典数据
@pytest.fixture
def seeded_dict_data(seeded_dict_type, create_test_dict_data):
    return create_test_dict_data(seeded_dict_type['dict_type'])


# 字典管理接口 - 预置两条字典数据供批量删除使用
@pytest.fixture
def seeded_dict_data_rows(seeded_dict_type, create_test_dict_data):
    dict_type = seeded_dict_type['dict_type']
    return [
        create_test_dict_data(dict_type),
        create_test_dict_data(dict_type),
    ]
