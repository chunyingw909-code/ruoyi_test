import pytest

from common.ui import response_matches
from common.utils import load_config
from pages.system.dept_page import DeptPage


config = load_config()


# 部门管理页面 - 打开已登录的部门管理页，并等待首次树形列表返回
@pytest.fixture
def dept_page(authenticated_page):
    with authenticated_page.expect_response(
        lambda response: response_matches(response, '/system/dept/list')
    ):
        authenticated_page.goto(config['ui_url'].rstrip('/') + '/system/dept')
    page = DeptPage(authenticated_page)
    page.loading_mask.wait_for(state='hidden')
    return page


# 部门管理页面 - 非新增场景通过接口预置若依科技下的独立部门
@pytest.fixture
def seeded_ui_dept(create_test_dept):
    return create_test_dept(leader='UI 预置负责人')
