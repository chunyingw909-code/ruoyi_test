import pytest

from common.ui import response_matches
from common.utils import load_config
from pages.system.dict_data_page import DictDataPage
from pages.system.dict_page import DictPage


config = load_config()


# 字典管理页面 - 打开已登录的字典类型页，并等首次列表返回后再交给用例
@pytest.fixture
def dict_page(authenticated_page):
    with authenticated_page.expect_response(
        lambda response: response_matches(response, '/system/dict/type/list')
    ):
        authenticated_page.goto(config['ui_url'].rstrip('/') + '/system/dict')
    page = DictPage(authenticated_page)
    page.loading_mask.wait_for(state='hidden')
    return page


# 字典管理页面 - 非新增场景统一通过接口预置字典类型
@pytest.fixture
def seeded_ui_dict_type(create_test_dict_type):
    return create_test_dict_type(remark='UI 预置字典')


# 字典数据页面 - 打开预置字典类型的数据页
@pytest.fixture
def dict_data_page(authenticated_page, seeded_ui_dict_type):
    url = (
        config['ui_url'].rstrip('/')
        + f"/system/dict-data/index/{seeded_ui_dict_type['dict_id']}"
    )
    with authenticated_page.expect_response(
        lambda response: response_matches(response, '/system/dict/data/list')
    ):
        authenticated_page.goto(url)
    page = DictDataPage(authenticated_page)
    page.loading_mask.wait_for(state='hidden')
    return page


# 字典数据页面 - 在预置字典类型下创建一条数据
@pytest.fixture
def seeded_ui_dict_data(seeded_ui_dict_type, create_test_dict_data):
    return create_test_dict_data(seeded_ui_dict_type['dict_type'])
