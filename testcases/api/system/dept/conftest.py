import pytest


# 部门管理接口 - 非新增场景统一通过接口预置若依科技下的独立部门
@pytest.fixture
def seeded_dept(create_test_dept):
    return create_test_dept(leader='API 预置负责人')
