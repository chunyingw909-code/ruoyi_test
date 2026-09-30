import pytest


# 参数设置接口 - 预置一个可供查询、更新和删除使用的非内置参数
@pytest.fixture
def seeded_config(create_test_config):
    return create_test_config(remark='接口预置参数')


# 参数设置接口 - 预置两个参数供批量删除使用
@pytest.fixture
def seeded_configs(create_test_config):
    return [
        create_test_config(remark='批量参数一'),
        create_test_config(remark='批量参数二'),
    ]
