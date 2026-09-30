import pytest


# 岗位管理接口 - 预置一个可供查询、更新和删除使用的岗位
@pytest.fixture
def seeded_post(create_test_post):
    return create_test_post(remark='接口预置岗位')


# 岗位管理接口 - 预置两个岗位供批量删除使用
@pytest.fixture
def seeded_posts(create_test_post):
    return [
        create_test_post(remark='批量岗位一'),
        create_test_post(remark='批量岗位二'),
    ]
