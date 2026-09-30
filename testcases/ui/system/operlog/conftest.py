import pytest

from common.ui import response_matches
from common.utils import load_config
from pages.system.operlog_page import OperlogPage


config = load_config()


# 操作日志页面 - 打开已登录的操作日志页，并等首次列表返回后再交给用例
@pytest.fixture
def operlog_page(authenticated_page):
    with authenticated_page.expect_response(
        lambda response: response_matches(response, '/monitor/operlog/list')
    ):
        authenticated_page.goto(
            config['ui_url'].rstrip('/') + '/system/log/operlog'
        )
    page = OperlogPage(authenticated_page)
    page.loading_mask.wait_for(state='hidden')
    return page


# 操作日志页面 - 通过新增字典类型准备一条可识别的操作日志
@pytest.fixture
def seeded_ui_oper_log(create_test_oper_log):
    return create_test_oper_log()
