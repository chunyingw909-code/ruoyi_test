import logging

import allure
import pytest


# UI 通用 - 用例失败时在页面关闭前附加截图
@pytest.fixture(autouse=True)
def screenshot_on_failure(request, page):
    yield
    failed = any(
        getattr(getattr(request.node, f'rep_{when}', None), 'failed', False)
        for when in ('setup', 'call')
    )
    if not failed:
        return
    try:
        allure.attach(
            page.screenshot(),
            name='失败截图',
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception as exc:
        logging.warning('失败截图抓取失败: %s', exc)
