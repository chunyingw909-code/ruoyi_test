import pytest


# 菜单管理接口 - 非新增场景统一通过接口预置独立顶级目录
@pytest.fixture
def seeded_menu(create_test_menu):
    return create_test_menu(remark='API 预置菜单')
