import pytest

from common.ui import response_matches
from common.utils import load_config
from pages.system.post_page import PostPage


config = load_config()


# 岗位管理页面 - 打开已登录的岗位管理页，并等首次列表返回后再交给用例
@pytest.fixture
def post_page(authenticated_page):
    with authenticated_page.expect_response(
        lambda response: response_matches(response, '/system/post/list')
    ):
        authenticated_page.goto(config['ui_url'].rstrip('/') + '/system/post')
    page = PostPage(authenticated_page)
    page.loading_mask.wait_for(state='hidden')
    return page


# 岗位管理页面 - 非新增场景统一通过接口预置数据
@pytest.fixture
def seeded_ui_post(create_test_post):
    return create_test_post(remark='UI 预置岗位')
