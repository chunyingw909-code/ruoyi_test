import time
from urllib.parse import parse_qs, urlparse


def response_matches(response, path, method='GET', query=None):
    """匹配浏览器实际发出的列表请求。

    只看路径会把进页时还没返回的未筛选列表当成这次搜索。
    """
    if response.request.method != method:
        return False
    if not urlparse(response.url).path.endswith(path):
        return False
    if query is None:
        return True
    actual = parse_qs(urlparse(response.url).query)
    for key, expected in query.items():
        values = actual.get(key, [''])
        if (values[0] if values else '') != expected:
            return False
    return True


def click_and_wait_list(page, button, loading_mask, path, query):
    with page.expect_response(
        lambda response: response_matches(response, path, query=query)
    ):
        button.click()
    loading_mask.wait_for(state='hidden', timeout=5000)


def row_operation_button(row, index):
    """行内操作是无文字图标按钮，按当前模板从左到右取第 index 个。"""
    return row.locator('td').last.get_by_role('button').nth(index)


def wait_dialog_settled(page, dialog, form_error, message, timeout_ms=10000):
    """表单错误留在弹窗里；成功提交会关掉弹窗；业务拒绝只出全局提示。"""
    previous_message = message.inner_text() if _visible(message) else ''
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if _visible(form_error):
            return
        if dialog.count() == 0 or dialog.is_hidden():
            return
        if _visible(message) and message.inner_text() != previous_message:
            try:
                dialog.wait_for(state='hidden', timeout=800)
            except Exception:
                return
            return
        page.wait_for_timeout(50)
    raise TimeoutError('提交后弹窗没有关闭，也没有出现表单或业务提示')


def _visible(locator):
    try:
        return locator.count() > 0 and locator.first.is_visible()
    except Exception:
        return False
