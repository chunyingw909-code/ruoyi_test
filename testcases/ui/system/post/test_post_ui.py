import allure
import pytest
from playwright.sync_api import expect

from common.utils import read_yaml
from common.xlsx_utils import xlsx_text_values


add_error_data = read_yaml('data/system/post_ui_errors.yaml')


@allure.feature('系统管理')
@allure.story('岗位管理页面')
@allure.title('岗位管理页展示查询、工具栏和列表核心元素')
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.ui
def test_post_page_structure(post_page):
    # 断言：岗位页具备查询、新增、导出和主要列表字段
    expect(post_page.search_post_code_input).to_be_visible()
    expect(post_page.search_post_name_input).to_be_visible()
    expect(post_page.search_status_input).to_be_visible()
    expect(post_page.add_button).to_be_visible()
    expect(post_page.export_button).to_be_visible()
    expect(post_page.table_headers).to_contain_text('岗位编号')
    expect(post_page.table_headers).to_contain_text('岗位编码')
    expect(post_page.table_headers).to_contain_text('岗位名称')
    expect(post_page.table_headers).to_contain_text('岗位排序')
    expect(post_page.table_headers).to_contain_text('状态')
    expect(post_page.table_headers).to_contain_text('操作')


@allure.feature('系统管理')
@allure.story('岗位管理页面')
@allure.title('按岗位编码筛选后可以重置查询条件')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_search_and_reset_post(post_page, seeded_ui_post):
    post_page.search(seeded_ui_post['post_code'])

    # 断言：精确筛选只显示目标岗位
    expect(post_page.row_by_post_code(seeded_ui_post['post_code'])).to_have_count(1)
    expect(post_page.pagination_total).to_contain_text('共 1 条')

    post_page.reset_search()
    # 断言：重置后岗位编码查询框被清空
    expect(post_page.search_post_code_input).to_have_value('')


@allure.feature('系统管理')
@allure.story('岗位管理页面')
@allure.title('通过页面正常新增岗位')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_add_post_success(post_page, unique_post_identity, track_test_post):
    identity = unique_post_identity
    post_page.add_post(identity['post_name'], identity['post_code'])
    post_page.search(identity['post_code'])

    try:
        row = post_page.row_by_post_code(identity['post_code'])
        # 断言：新增后列表展示目标岗位名称和编码
        expect(row).to_have_count(1)
        expect(row).to_contain_text(identity['post_name'])
    finally:
        track_test_post(identity['post_name'])


@allure.feature('系统管理')
@allure.story('岗位管理页面')
@allure.title('新增岗位表单异常：{case[desc]}')
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
@pytest.mark.parametrize('case', add_error_data, ids=lambda x: x['desc'])
def test_add_post_validation(post_page, track_test_post, case):
    try:
        post_page.add_post(case['post_name'], case['post_code'])
        # 断言：缺少必填字段时弹窗展示字段级校验提示
        expect(post_page.add_form_error).to_have_text(case['expect'])
    finally:
        if case['post_name'].startswith('AUTOTEST-post-'):
            track_test_post(case['post_name'])


@allure.feature('系统管理')
@allure.story('岗位管理页面')
@allure.title('通过页面修改岗位名称并停用岗位')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_edit_post(post_page, post_api, seeded_ui_post):
    post_code = seeded_ui_post['post_code']
    new_name = f"{seeded_ui_post['post_name']}-updated"
    post_page.search(post_code)
    post_page.edit_name_and_disable(post_code, new_name)
    post_page.search(post_code)
    detail = post_api.get_post(seeded_ui_post['post_id'])

    row = post_page.row_by_post_code(post_code)
    # 断言：列表显示新名称和停用状态，接口详情也得到已落库的新值
    expect(row).to_contain_text(new_name)
    expect(row).to_contain_text('停用')
    assert detail['data']['postName'] == new_name, detail
    assert detail['data']['status'] == '1', detail


@allure.feature('系统管理')
@allure.story('岗位管理页面')
@allure.title('通过页面确认删除岗位')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_delete_post(post_page, post_api, seeded_ui_post):
    post_code = seeded_ui_post['post_code']
    post_page.search(post_code)
    post_page.delete_post(post_code)
    rows = [
        row for row in post_api.list_posts(postCode=post_code).get('rows', [])
        if row.get('postCode') == post_code
    ]

    # 断言：删除后页面和接口均不存在目标岗位
    expect(post_page.row_by_post_code(post_code)).to_have_count(0)
    assert rows == [], rows


@allure.feature('系统管理')
@allure.story('岗位管理页面')
@allure.title('通过页面按岗位编码导出岗位 Excel')
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.ui
def test_export_post(post_page, seeded_ui_post):
    post_page.search(seeded_ui_post['post_code'])

    with post_page.page.expect_download() as download_info:
        post_page.export_button.click()
    download = download_info.value
    values = xlsx_text_values(download.path().read_bytes())

    # 断言：浏览器下载 XLSX，内容包含本次筛选的目标岗位
    assert download.suggested_filename.endswith('.xlsx')
    assert seeded_ui_post['post_name'] in values, values
    assert seeded_ui_post['post_code'] in values, values
