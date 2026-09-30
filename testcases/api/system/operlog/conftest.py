import pytest


# 操作日志接口 - 预置一条由新增字典类型产生的日志
@pytest.fixture
def seeded_oper_log(create_test_oper_log):
    return create_test_oper_log()


# 操作日志接口 - 预置两条日志供批量删除使用
@pytest.fixture
def seeded_oper_logs(create_test_oper_log):
    return [create_test_oper_log(), create_test_oper_log()]
