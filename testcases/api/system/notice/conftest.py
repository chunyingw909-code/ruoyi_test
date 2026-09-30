import pytest


# 通知公告接口 - 预置一条可供查询、更新和删除使用的公告
@pytest.fixture
def seeded_notice(create_test_notice):
    return create_test_notice()


# 通知公告接口 - 预置两条公告供批量删除使用
@pytest.fixture
def seeded_notices(create_test_notice):
    return [create_test_notice(), create_test_notice()]
