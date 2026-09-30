import pytest

from common.ui import response_matches
from common.utils import load_config
from pages.system.role_page import RolePage


config = load_config()


# 角色管理页面 - 打开已登录的角色管理页，并等首次列表返回后再交给用例
@pytest.fixture
def role_page(authenticated_page):
    with authenticated_page.expect_response(
        lambda response: response_matches(response, '/system/role/list')
    ):
        authenticated_page.goto(config['ui_url'].rstrip('/') + '/system/role')
    page = RolePage(authenticated_page)
    page.loading_mask.wait_for(state='hidden')
    return page


# 角色管理页面 - 非新增场景统一通过接口预置数据
@pytest.fixture
def seeded_ui_role(create_test_role):
    return create_test_role(remark='UI 预置角色')
