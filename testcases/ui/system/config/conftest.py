import pytest

from common.ui import response_matches
from common.utils import load_config
from pages.system.config_page import ConfigPage


config = load_config()


# 参数设置页面 - 打开已登录的参数页，并等首次列表返回后再交给用例
@pytest.fixture
def config_page(authenticated_page):
    with authenticated_page.expect_response(
        lambda response: response_matches(response, '/system/config/list')
    ):
        authenticated_page.goto(config['ui_url'].rstrip('/') + '/system/config')
    page = ConfigPage(authenticated_page)
    page.loading_mask.wait_for(state='hidden')
    return page


# 参数设置页面 - 非新增场景统一通过接口预置非内置参数
@pytest.fixture
def seeded_ui_config(create_test_config):
    return create_test_config(remark='UI 预置参数')
