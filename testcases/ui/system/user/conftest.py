import pytest

from common.ui import response_matches
from common.utils import load_config
from pages.system.user_page import UserPage


config = load_config()


# 用户管理页面 - 打开已登录的用户管理页，并等首次列表返回后再交给用例
@pytest.fixture
def user_page(authenticated_page):
    with authenticated_page.expect_response(
        lambda response: response_matches(response, '/system/user/list')
    ):
        authenticated_page.goto(config['ui_url'].rstrip('/') + '/system/user')
    page = UserPage(authenticated_page)
    page.loading_mask.wait_for(state='hidden')
    return page


# 用户管理页面 - 非新增场景统一通过接口预置数据
@pytest.fixture
def seeded_ui_user(create_test_user):
    return create_test_user(nickname='UI 预置用户')
