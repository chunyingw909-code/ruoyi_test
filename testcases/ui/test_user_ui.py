import allure
import time
from playwright.sync_api import expect


@allure.feature('用户管理模块')
@allure.story('新增用户-正向')
@allure.title('正常新增用户')
def test_add_user_success(user_page, cleanup_user):
    username = f'test_{int(time.time())}'
    cleanup_user.append(username)

    with allure.step('新增用户'):
        user_page.add_user(username, '测试001')

    with allure.step('搜索确认用户存在'):
        user_page.search(username)
        expect(user_page.user_link(username)).to_have_count(1)