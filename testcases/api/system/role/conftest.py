import pytest


# 角色管理接口 - 预置一个可供查询、更新和删除使用的角色
@pytest.fixture
def seeded_role(create_test_role):
    return create_test_role(remark='接口预置角色')


# 角色管理接口 - 预置两个角色供批量删除使用
@pytest.fixture
def seeded_roles(create_test_role):
    return [
        create_test_role(remark='批量角色一'),
        create_test_role(remark='批量角色二'),
    ]
