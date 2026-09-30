import pytest

from common.ui import response_matches
from common.utils import load_config
from pages.system.menu_page import MenuPage


config = load_config()


# 菜单管理页面 - 打开已登录的菜单管理页，并等待首次树形列表返回
@pytest.fixture
def menu_page(authenticated_page):
    with authenticated_page.expect_response(
        lambda response: response_matches(response, '/system/menu/list')
    ):
        authenticated_page.goto(config['ui_url'].rstrip('/') + '/system/menu')
    page = MenuPage(authenticated_page)
    page.loading_mask.wait_for(state='hidden')
    return page


# 菜单管理页面 - 非新增场景通过接口预置可安全清理的独立顶级目录
@pytest.fixture
def seeded_ui_menu(create_test_menu):
    return create_test_menu(remark='UI 预置菜单')
