import pytest

from common.ui import response_matches
from common.utils import load_config
from pages.system.logininfor_page import LogininforPage


config = load_config()


# 登录日志页面 - 打开已登录的登录日志页，并等首次列表返回后再交给用例
@pytest.fixture
def logininfor_page(authenticated_page):
    with authenticated_page.expect_response(
        lambda response: response_matches(response, '/monitor/logininfor/list')
    ):
        authenticated_page.goto(
            config['ui_url'].rstrip('/') + '/system/log/logininfor'
        )
    page = LogininforPage(authenticated_page)
    page.loading_mask.wait_for(state='hidden')
    return page


# 登录日志页面 - 通过失败登录准备一条可识别的登录日志
@pytest.fixture
def seeded_ui_login_log(create_failed_login):
    return create_failed_login()
