import pytest


# 用户管理接口 - 预置一个可供查询、更新和删除测试使用的用户
@pytest.fixture
def seeded_user(create_test_user):
    return create_test_user(nickname='接口预置用户')


# 用户管理接口 - 预置两个用户供批量删除使用
@pytest.fixture
def seeded_users(create_test_user):
    return [
        create_test_user(nickname='批量用户一'),
        create_test_user(nickname='批量用户二'),
    ]
