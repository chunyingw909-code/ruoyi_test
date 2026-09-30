import pytest

from common.ui import response_matches
from common.utils import load_config
from pages.system.notice_page import NoticePage


config = load_config()


# 通知公告页面 - 打开已登录的公告页，并等首次列表返回后再交给用例
@pytest.fixture
def notice_page(authenticated_page):
    with authenticated_page.expect_response(
        lambda response: response_matches(response, '/system/notice/list')
    ):
        authenticated_page.goto(config['ui_url'].rstrip('/') + '/system/notice')
    page = NoticePage(authenticated_page)
    page.loading_mask.wait_for(state='hidden')
    return page


# 通知公告页面 - 非新增场景统一通过接口预置公告
@pytest.fixture
def seeded_ui_notice(create_test_notice):
    return create_test_notice()
