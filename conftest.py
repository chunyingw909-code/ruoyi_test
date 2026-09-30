import os
import logging
import time
import uuid

import pytest
from playwright.sync_api import sync_playwright

from api.auth.login_api import LoginApi
from api.system.config_api import ConfigApi
from api.system.dept_api import DeptApi
from api.system.dict_api import DictDataApi, DictTypeApi
from api.system.logininfor_api import LogininforApi
from api.system.menu_api import MenuApi
from api.system.notice_api import NoticeApi
from api.system.operlog_api import OperlogApi
from api.system.post_api import PostApi
from api.system.role_api import RoleApi
from api.system.user_api import UserApi
from common.oper_log_guard import OperLogLedger
from common.utils import load_config
from pages.auth.login_page import LoginPage

logging.basicConfig(level=logging.INFO)
config = load_config()


# 全局认证 - API 登录令牌
@pytest.fixture(scope="session")
def login_token():
    api = LoginApi()
    try:
        data = api.login(config['admin']['username'], config['admin']['password'])
        assert data is not None, "登录接口返回为空"
        assert data.get('code') == 200, f"登录失败，返回: {data}"
        assert data.get('token'), f"登录成功响应中没有 token: {data}"
        yield data['token']
    finally:
        api.close()


# 跨 API/UI - 生成隔离的用户管理测试账号
@pytest.fixture
def unique_username():
    """生成只属于当前用例的测试用户名。"""
    return f'AUTOTEST-{uuid.uuid4().hex[:8]}'


# 跨 API/UI - 用户管理接口客户端
@pytest.fixture
def user_api(login_token):
    """提供用户管理 API，并在用例结束后关闭 Session。"""
    api = UserApi(login_token)
    yield api
    api.close()


# 跨 API/UI - 角色管理接口客户端
@pytest.fixture
def role_api(login_token):
    """提供角色管理 API，并在用例结束后关闭 Session。"""
    api = RoleApi(login_token)
    yield api
    api.close()


# 跨 API/UI - 菜单管理接口客户端
@pytest.fixture
def menu_api(login_token):
    """提供菜单管理 API，并在用例结束后关闭 Session。"""
    api = MenuApi(login_token)
    yield api
    api.close()


# 跨 API/UI - 部门管理接口客户端
@pytest.fixture
def dept_api(login_token):
    api = DeptApi(login_token)
    yield api
    api.close()


# 跨 API/UI - 岗位管理接口客户端
@pytest.fixture
def post_api(login_token):
    api = PostApi(login_token)
    yield api
    api.close()


# 跨 API/UI - 生成隔离的岗位名称和岗位编码
@pytest.fixture
def unique_post_identity():
    suffix = uuid.uuid4().hex[:8]
    return {
        'post_name': f'AUTOTEST-post-{suffix}',
        'post_code': f'autotest_{suffix}',
    }


# 跨 API/UI - 岗位登记与安全清理
@pytest.fixture
def track_test_post(post_api):
    """只登记 AUTOTEST 岗位，teardown 按精确 postId 清理。"""
    tracked = {}

    def _track(post_name):
        if not post_name.startswith('AUTOTEST-post-'):
            raise ValueError(f'只允许登记 AUTOTEST 测试岗位，收到: {post_name!r}')
        result = post_api.list_posts(postName=post_name, pageNum=1, pageSize=100)
        rows = [
            row for row in result.get('rows', [])
            if row.get('postName') == post_name
        ]
        for row in rows:
            tracked[row['postId']] = post_name
        return rows

    yield _track

    for post_id, post_name in reversed(list(tracked.items())):
        try:
            detail = post_api.get_post(post_id).get('data') or {}
            safe_to_delete = (
                detail.get('postId') == post_id
                and detail.get('postName', '').startswith('AUTOTEST-post-')
                and detail.get('postCode', '').startswith('autotest_')
            )
            if safe_to_delete:
                result = post_api.delete_post(post_id)
                if result.get('code') != 200:
                    logging.warning(
                        '清理测试岗位被拒绝: postName=%s, postId=%s, result=%s',
                        post_name,
                        post_id,
                        result,
                    )
        except Exception as exc:
            logging.warning(
                '清理测试岗位失败: postName=%s, postId=%s, error=%s',
                post_name,
                post_id,
                exc,
            )


# 跨 API/UI - 通过接口创建并自动登记测试岗位
@pytest.fixture
def create_test_post(post_api, track_test_post):
    def _create(post_name=None, post_code=None, **kwargs):
        suffix = uuid.uuid4().hex[:8]
        post_name = post_name or f'AUTOTEST-post-{suffix}'
        post_code = post_code or f'autotest_{suffix}'
        result = post_api.add_post(post_name, post_code, **kwargs)
        assert result.status_code == 200, result
        assert result.get('code') == 200, f'测试岗位创建失败: {result}'

        rows = track_test_post(post_name)
        assert len(rows) == 1, f'未找到唯一测试岗位: {rows}'
        return {
            'post_name': post_name,
            'post_code': post_code,
            'post_id': rows[0]['postId'],
            'row': rows[0],
        }

    return _create


# 跨 API/UI - 字典类型接口客户端
@pytest.fixture
def dict_type_api(login_token):
    api = DictTypeApi(login_token)
    yield api
    api.close()


# 跨 API/UI - 字典数据接口客户端
@pytest.fixture
def dict_data_api(login_token):
    api = DictDataApi(login_token)
    yield api
    api.close()


# 跨 API/UI - 生成隔离的字典名称和字典类型
@pytest.fixture
def unique_dict_identity():
    suffix = uuid.uuid4().hex[:8]
    return {
        'dict_name': f'AUTOTEST-dict-{suffix}',
        'dict_type': f'autotest_dict_{suffix}',
    }


def _register_unique_marker(oper_log_guard, text):
    """只登记带 8 位 hex 后缀的完整标识。公共或非唯一值跳过，不打断原用例。"""
    try:
        oper_log_guard.register_marker(text)
    except ValueError:
        return


# 跨 API/UI - 字典类型登记与安全清理。先删本类型下的 AUTOTEST 字典数据
@pytest.fixture
def track_test_dict_type(dict_type_api, dict_data_api, oper_log_guard):
    tracked = {}

    def _track(dict_name):
        if not dict_name.startswith('AUTOTEST-dict-'):
            raise ValueError(f'只允许登记 AUTOTEST 测试字典，收到: {dict_name!r}')
        _register_unique_marker(oper_log_guard, dict_name)
        result = dict_type_api.list_dict_types(
            dictName=dict_name, pageNum=1, pageSize=100
        )
        rows = [
            row for row in result.get('rows', [])
            if row.get('dictName') == dict_name
        ]
        for row in rows:
            tracked[row['dictId']] = dict_name
        return rows

    yield _track

    for dict_id, dict_name in reversed(list(tracked.items())):
        try:
            detail = dict_type_api.get_dict_type(dict_id).get('data') or {}
            safe_to_delete = (
                detail.get('dictId') == dict_id
                and detail.get('dictName', '').startswith('AUTOTEST-dict-')
                and detail.get('dictType', '').startswith('autotest_')
            )
            if not safe_to_delete:
                continue
            data_rows = dict_data_api.list_dict_data(
                dictType=detail['dictType'], pageNum=1, pageSize=100
            ).get('rows', [])
            data_ids = [
                row['dictCode'] for row in data_rows
                if str(row.get('dictLabel', '')).startswith('AUTOTEST-')
            ]
            if data_ids:
                joined_ids = ','.join(str(data_id) for data_id in data_ids)
                oper_log_guard.register_url(f'/system/dict/data/{joined_ids}')
                dict_data_api.delete_dict_data_batch(data_ids)
            oper_log_guard.register_url(f'/system/dict/type/{dict_id}')
            result = dict_type_api.delete_dict_type(dict_id)
            if result.get('code') != 200:
                logging.warning(
                    '清理测试字典被拒绝: dictName=%s, dictId=%s, result=%s',
                    dict_name,
                    dict_id,
                    result,
                )
        except Exception as exc:
            logging.warning(
                '清理测试字典失败: dictName=%s, dictId=%s, error=%s',
                dict_name,
                dict_id,
                exc,
            )


# 跨 API/UI - 通过接口创建并自动登记测试字典类型
@pytest.fixture
def create_test_dict_type(dict_type_api, track_test_dict_type):
    def _create(dict_name=None, dict_type=None, **kwargs):
        suffix = uuid.uuid4().hex[:8]
        dict_name = dict_name or f'AUTOTEST-dict-{suffix}'
        dict_type = dict_type or f'autotest_dict_{suffix}'
        result = dict_type_api.add_dict_type(dict_name, dict_type, **kwargs)
        assert result.status_code == 200, result
        assert result.get('code') == 200, f'测试字典创建失败: {result}'
        rows = track_test_dict_type(dict_name)
        assert len(rows) == 1, f'未找到唯一测试字典: {rows}'
        return {
            'dict_name': dict_name,
            'dict_type': dict_type,
            'dict_id': rows[0]['dictId'],
            'row': rows[0],
        }

    return _create


# 跨 API/UI - 字典数据登记与安全清理
@pytest.fixture
def track_test_dict_data(dict_data_api, oper_log_guard):
    tracked = {}

    def _track(dict_type, dict_label):
        if not str(dict_label).startswith('AUTOTEST-'):
            raise ValueError(f'只允许登记 AUTOTEST 测试字典数据，收到: {dict_label!r}')
        _register_unique_marker(oper_log_guard, dict_label)
        result = dict_data_api.list_dict_data(
            dictType=dict_type, dictLabel=dict_label, pageNum=1, pageSize=100
        )
        rows = [
            row for row in result.get('rows', [])
            if row.get('dictLabel') == dict_label
        ]
        for row in rows:
            tracked[row['dictCode']] = dict_label
        return rows

    yield _track

    for dict_code, dict_label in reversed(list(tracked.items())):
        try:
            detail = dict_data_api.get_dict_data(dict_code).get('data') or {}
            safe_to_delete = (
                detail.get('dictCode') == dict_code
                and detail.get('dictLabel', '').startswith('AUTOTEST-')
            )
            if safe_to_delete:
                oper_log_guard.register_url(f'/system/dict/data/{dict_code}')
                result = dict_data_api.delete_dict_data(dict_code)
                if result.get('code') != 200:
                    logging.warning(
                        '清理测试字典数据被拒绝: dictLabel=%s, dictCode=%s, result=%s',
                        dict_label,
                        dict_code,
                        result,
                    )
        except Exception as exc:
            logging.warning(
                '清理测试字典数据失败: dictLabel=%s, dictCode=%s, error=%s',
                dict_label,
                dict_code,
                exc,
            )


# 跨 API/UI - 通过接口创建并自动登记测试字典数据
@pytest.fixture
def create_test_dict_data(dict_data_api, track_test_dict_data):
    def _create(dict_type, dict_label=None, dict_value=None, **kwargs):
        suffix = uuid.uuid4().hex[:8]
        dict_label = dict_label or f'AUTOTEST-label-{suffix}'
        dict_value = dict_value or f'autotest_{suffix}'
        result = dict_data_api.add_dict_data(
            dict_label, dict_value, dict_type, **kwargs
        )
        assert result.status_code == 200, result
        assert result.get('code') == 200, f'测试字典数据创建失败: {result}'
        rows = track_test_dict_data(dict_type, dict_label)
        assert len(rows) == 1, f'未找到唯一测试字典数据: {rows}'
        return {
            'dict_type': dict_type,
            'dict_label': dict_label,
            'dict_value': dict_value,
            'dict_code': rows[0]['dictCode'],
            'row': rows[0],
        }

    return _create


# 跨 API/UI - 参数设置接口客户端
@pytest.fixture
def config_api(login_token):
    api = ConfigApi(login_token)
    yield api
    api.close()


# 跨 API/UI - 生成隔离的参数名称和键名
@pytest.fixture
def unique_config_identity():
    suffix = uuid.uuid4().hex[:8]
    return {
        'config_name': f'AUTOTEST-config-{suffix}',
        'config_key': f'autotest_{suffix}',
    }


# 跨 API/UI - 参数登记与安全清理。只删除非内置的 AUTOTEST 参数
@pytest.fixture
def track_test_config(config_api, oper_log_guard):
    tracked = {}

    def _track(config_name):
        if not config_name.startswith('AUTOTEST-config-'):
            raise ValueError(f'只允许登记 AUTOTEST 测试参数，收到: {config_name!r}')
        _register_unique_marker(oper_log_guard, config_name)
        result = config_api.list_configs(
            configName=config_name, pageNum=1, pageSize=100
        )
        rows = [
            row for row in result.get('rows', [])
            if row.get('configName') == config_name
        ]
        for row in rows:
            tracked[row['configId']] = config_name
        return rows

    yield _track

    for config_id, config_name in reversed(list(tracked.items())):
        try:
            detail = config_api.get_config(config_id).get('data') or {}
            safe_to_delete = (
                detail.get('configId') == config_id
                and detail.get('configName', '').startswith('AUTOTEST-config-')
                and detail.get('configKey', '').startswith('autotest_')
                and detail.get('configType') == 'N'
            )
            if safe_to_delete:
                oper_log_guard.register_url(f'/system/config/{config_id}')
                result = config_api.delete_config(config_id)
                if result.get('code') != 200:
                    logging.warning(
                        '清理测试参数被拒绝: configName=%s, configId=%s, result=%s',
                        config_name,
                        config_id,
                        result,
                    )
        except Exception as exc:
            logging.warning(
                '清理测试参数失败: configName=%s, configId=%s, error=%s',
                config_name,
                config_id,
                exc,
            )


# 跨 API/UI - 通过接口创建并自动登记非内置测试参数
@pytest.fixture
def create_test_config(config_api, track_test_config):
    def _create(config_name=None, config_key=None, config_value='autotest', **kwargs):
        suffix = uuid.uuid4().hex[:8]
        config_name = config_name or f'AUTOTEST-config-{suffix}'
        config_key = config_key or f'autotest_{suffix}'
        result = config_api.add_config(
            config_name, config_key, config_value, **kwargs
        )
        assert result.status_code == 200, result
        assert result.get('code') == 200, f'测试参数创建失败: {result}'
        rows = track_test_config(config_name)
        assert len(rows) == 1, f'未找到唯一测试参数: {rows}'
        return {
            'config_name': config_name,
            'config_key': config_key,
            'config_value': config_value,
            'config_id': rows[0]['configId'],
            'row': rows[0],
        }

    return _create


# 跨 API/UI - 通知公告接口客户端
@pytest.fixture
def notice_api(login_token):
    api = NoticeApi(login_token)
    yield api
    api.close()


# 跨 API/UI - 生成隔离的公告标题
@pytest.fixture
def unique_notice_title():
    return f'AUTOTEST-notice-{uuid.uuid4().hex[:8]}'


# 跨 API/UI - 公告登记与安全清理
@pytest.fixture
def track_test_notice(notice_api, oper_log_guard):
    tracked = {}

    def _track(notice_title):
        if not notice_title.startswith('AUTOTEST-notice-'):
            raise ValueError(f'只允许登记 AUTOTEST 测试公告，收到: {notice_title!r}')
        _register_unique_marker(oper_log_guard, notice_title)
        result = notice_api.list_notices(
            noticeTitle=notice_title, pageNum=1, pageSize=100
        )
        rows = [
            row for row in result.get('rows', [])
            if row.get('noticeTitle') == notice_title
        ]
        for row in rows:
            tracked[row['noticeId']] = notice_title
        return rows

    yield _track

    for notice_id, notice_title in reversed(list(tracked.items())):
        try:
            detail = notice_api.get_notice(notice_id).get('data') or {}
            safe_to_delete = (
                detail.get('noticeId') == notice_id
                and detail.get('noticeTitle', '').startswith('AUTOTEST-notice-')
            )
            if safe_to_delete:
                oper_log_guard.register_url(f'/system/notice/{notice_id}')
                result = notice_api.delete_notice(notice_id)
                if result.get('code') != 200:
                    logging.warning(
                        '清理测试公告被拒绝: noticeTitle=%s, noticeId=%s, result=%s',
                        notice_title,
                        notice_id,
                        result,
                    )
        except Exception as exc:
            logging.warning(
                '清理测试公告失败: noticeTitle=%s, noticeId=%s, error=%s',
                notice_title,
                notice_id,
                exc,
            )


# 跨 API/UI - 通过接口创建并自动登记测试公告
@pytest.fixture
def create_test_notice(notice_api, track_test_notice):
    def _create(notice_title=None, **kwargs):
        notice_title = notice_title or f'AUTOTEST-notice-{uuid.uuid4().hex[:8]}'
        result = notice_api.add_notice(notice_title, **kwargs)
        assert result.status_code == 200, result
        assert result.get('code') == 200, f'测试公告创建失败: {result}'
        rows = track_test_notice(notice_title)
        assert len(rows) == 1, f'未找到唯一测试公告: {rows}'
        return {
            'notice_title': notice_title,
            'notice_id': rows[0]['noticeId'],
            'row': rows[0],
        }

    return _create


def _poll(fetch, accept, timeout=5):
    """操作日志和登录日志由后写队列入库，刚请求完列表里可能还没有。"""
    deadline = time.monotonic() + timeout
    last = fetch()
    while not accept(last) and time.monotonic() < deadline:
        time.sleep(0.2)
        last = fetch()
    return last


def _oper_logs_for_dict(operlog_api, dict_name, dict_id=None):
    """新增日志的请求参数里有字典名；删除日志只在 URL 上带字典编号。"""
    result = operlog_api.list_logs(title='字典类型', pageNum=1, pageSize=50)
    suffix = None if dict_id is None else f'/system/dict/type/{dict_id}'
    matched = []
    for row in result.get('rows', []):
        if row.get('title') != '字典类型':
            continue
        param = str(row.get('operParam') or '')
        url = str(row.get('operUrl') or '').rstrip('/')
        if dict_name and dict_name in param:
            matched.append(row)
        elif suffix and url.endswith(suffix):
            matched.append(row)
    return matched


def _login_logs_for_user(logininfor_api, username):
    result = logininfor_api.list_logs(userName=username, pageNum=1, pageSize=20)
    return [
        row for row in result.get('rows', [])
        if row.get('userName') == username
    ]


# 跨 API/UI - 操作日志接口客户端
@pytest.fixture
def operlog_api(login_token):
    api = OperlogApi(login_token)
    yield api
    api.close()


def _max_oper_id(operlog_api):
    result = operlog_api.list_logs(pageNum=1, pageSize=1, orderByColumn='operId', isAsc='desc')
    rows = result.get('rows') or []
    return max((int(row.get('operId') or 0) for row in rows), default=0)


# 功能级操作日志守卫：记下当前最大 operId，用例结束后只删登记命中的新日志
@pytest.fixture
def oper_log_guard(operlog_api):
    ledger = OperLogLedger(operlog_api, _max_oper_id(operlog_api))
    yield ledger
    ledger.cleanup()


# 跨 API/UI - 登录日志接口客户端
@pytest.fixture
def logininfor_api(login_token):
    api = LogininforApi(login_token)
    yield api
    api.close()


# 跨 API/UI - 新增一条 AUTOTEST 字典类型，并找到它写下的操作日志。
# 清理时先删字典，再删这条字典的新增和删除日志。删除日志不带字典名，只能按编号对 URL
@pytest.fixture
def create_test_oper_log(dict_type_api, operlog_api, oper_log_guard):
    tracked = []

    def _create():
        suffix = uuid.uuid4().hex[:8]
        dict_name = f'AUTOTEST-dict-{suffix}'
        dict_type = f'autotest_dict_{suffix}'
        oper_log_guard.register_marker(dict_name)
        result = dict_type_api.add_dict_type(dict_name, dict_type)
        assert result.status_code == 200, result
        assert result.get('code') == 200, f'测试字典创建失败: {result}'
        listed = dict_type_api.list_dict_types(
            dictName=dict_name, pageNum=1, pageSize=10
        )
        dict_rows = [
            row for row in listed.get('rows', [])
            if row.get('dictName') == dict_name
        ]
        assert len(dict_rows) == 1, dict_rows
        tracked.append({
            'dict_id': dict_rows[0]['dictId'],
            'dict_name': dict_name,
        })
        logs = _poll(
            lambda: _oper_logs_for_dict(operlog_api, dict_name),
            lambda rows: any(
                str(row.get('businessType')) == '1' for row in rows
            ),
        )
        insert_logs = [
            row for row in logs if str(row.get('businessType')) == '1'
        ]
        assert len(insert_logs) == 1, logs
        return {
            'dict_name': dict_name,
            'dict_type': dict_type,
            'dict_id': dict_rows[0]['dictId'],
            'oper_id': insert_logs[0]['operId'],
            'row': insert_logs[0],
        }

    yield _create

    for item in reversed(tracked):
        dict_id = item['dict_id']
        dict_name = item['dict_name']
        try:
            detail = dict_type_api.get_dict_type(dict_id).get('data') or {}
            safe_to_delete = (
                detail.get('dictId') == dict_id
                and detail.get('dictName', '').startswith('AUTOTEST-dict-')
                and detail.get('dictType', '').startswith('autotest_')
            )
            if safe_to_delete:
                oper_log_guard.register_url(f'/system/dict/type/{dict_id}')
                dict_type_api.delete_dict_type(dict_id)
        except Exception as exc:
            logging.warning(
                '清理操作日志对应的测试字典失败: dictName=%s, dictId=%s, error=%s',
                dict_name,
                dict_id,
                exc,
            )


# 跨 API/UI - 用一个不存在的 AUTOTEST 账号失败登录，得到可删除的登录日志。
# 收尾时删掉该账号的日志，并清掉登录失败计数
@pytest.fixture
def create_failed_login(logininfor_api, oper_log_guard):
    tracked = []

    def _create():
        username = f'AUTOTEST-login-{uuid.uuid4().hex[:8]}'
        oper_log_guard.register_marker(username)
        api = LoginApi()
        try:
            result = api.login(username, 'wrong-password')
        finally:
            api.close()
        assert result.status_code == 200, result
        assert result.get('code') == 500, result
        assert '用户不存在/密码错误' in str(result.get('msg')), result
        tracked.append(username)
        rows = _poll(
            lambda: _login_logs_for_user(logininfor_api, username),
            lambda found: any(
                '用户不存在/密码错误' in str(row.get('msg')) for row in found
            ),
        )
        matched = [
            row for row in rows
            if '用户不存在/密码错误' in str(row.get('msg'))
        ]
        assert matched, rows
        return {
            'username': username,
            'info_id': matched[0]['infoId'],
            'row': matched[0],
            'rows': rows,
        }

    yield _create

    for username in reversed(tracked):
        try:
            info_ids = [
                row['infoId']
                for row in _login_logs_for_user(logininfor_api, username)
            ]
            if info_ids:
                joined_ids = ','.join(str(info_id) for info_id in info_ids)
                oper_log_guard.register_url(f'/monitor/logininfor/{joined_ids}')
                result = logininfor_api.delete_logs(info_ids)
                if result.get('code') != 200:
                    logging.warning(
                        '清理测试登录日志被拒绝: userName=%s, infoIds=%s, result=%s',
                        username,
                        info_ids,
                        result,
                    )
            unlocked = logininfor_api.unlock(username)
            if unlocked.get('code') != 200:
                logging.warning(
                    '清理登录失败计数被拒绝: userName=%s, result=%s',
                    username,
                    unlocked,
                )
        except Exception as exc:
            logging.warning(
                '清理测试登录日志失败: userName=%s, error=%s',
                username,
                exc,
            )


# 跨 API/UI - 生成隔离的部门名称
@pytest.fixture
def unique_dept_name():
    return f'AUTOTEST-dept-{uuid.uuid4().hex[:8]}'


# 跨 API/UI - 部门登记与安全清理
@pytest.fixture
def track_test_dept(dept_api):
    tracked = {}

    def _track(dept_name):
        if not dept_name.startswith('AUTOTEST-dept-'):
            raise ValueError(f'只允许登记 AUTOTEST 测试部门，收到: {dept_name!r}')
        rows = [
            row for row in dept_api.list_depts(deptName=dept_name).get('data', [])
            if row.get('deptName') == dept_name
        ]
        for row in rows:
            tracked[row['deptId']] = dept_name
        return rows

    yield _track

    for dept_id, dept_name in reversed(list(tracked.items())):
        try:
            detail = dept_api.get_dept(dept_id).get('data') or {}
            if (
                detail.get('deptId') == dept_id
                and detail.get('deptName', '').startswith('AUTOTEST-dept-')
            ):
                result = dept_api.delete_dept(dept_id)
                if result.get('code') != 200:
                    logging.warning(
                        '清理测试部门被拒绝: deptName=%s, deptId=%s, result=%s',
                        dept_name,
                        dept_id,
                        result,
                    )
        except Exception as exc:
            logging.warning(
                '清理测试部门失败: deptName=%s, deptId=%s, error=%s',
                dept_name,
                dept_id,
                exc,
            )


# 跨 API/UI - 通过接口创建并自动登记测试部门
@pytest.fixture
def create_test_dept(dept_api, track_test_dept):
    def _create(dept_name=None, **kwargs):
        dept_name = dept_name or f'AUTOTEST-dept-{uuid.uuid4().hex[:8]}'
        result = dept_api.add_dept(dept_name, **kwargs)
        assert result.status_code == 200, result
        assert result.get('code') == 200, f'测试部门创建失败: {result}'
        rows = track_test_dept(dept_name)
        assert len(rows) == 1, f'未找到唯一测试部门: {rows}'
        return {
            'dept_name': dept_name,
            'dept_id': rows[0]['deptId'],
            'row': rows[0],
        }

    return _create


# 跨 API/UI - 生成隔离的菜单名称和路由地址
@pytest.fixture
def unique_menu_identity():
    suffix = uuid.uuid4().hex[:8]
    return {
        'menu_name': f'AUTOTEST-menu-{suffix}',
        'path': f'autotest-menu-{suffix}',
    }


# 跨 API/UI - 菜单登记与安全清理
@pytest.fixture
def track_test_menu(menu_api):
    """只登记 AUTOTEST 菜单，teardown 按精确 menuId 清理。"""
    tracked = {}

    def _track(menu_name):
        if not menu_name.startswith('AUTOTEST-menu-'):
            raise ValueError(f'只允许登记 AUTOTEST 测试菜单，收到: {menu_name!r}')
        result = menu_api.list_menus(menuName=menu_name)
        rows = [
            row for row in result.get('data', [])
            if row.get('menuName') == menu_name
        ]
        for row in rows:
            tracked[row['menuId']] = menu_name
        return rows

    yield _track

    for menu_id, menu_name in reversed(list(tracked.items())):
        try:
            detail = menu_api.get_menu(menu_id).get('data') or {}
            safe_to_delete = (
                detail.get('menuId') == menu_id
                and detail.get('menuName', '').startswith('AUTOTEST-menu-')
            )
            if safe_to_delete:
                result = menu_api.delete_menu(menu_id)
                if result.get('code') != 200:
                    logging.warning(
                        '清理测试菜单被拒绝: menuName=%s, menuId=%s, result=%s',
                        menu_name,
                        menu_id,
                        result,
                    )
        except Exception as exc:
            logging.warning(
                '清理测试菜单失败: menuName=%s, menuId=%s, error=%s',
                menu_name,
                menu_id,
                exc,
            )


# 跨 API/UI - 通过接口创建并自动登记测试菜单
@pytest.fixture
def create_test_menu(menu_api, track_test_menu):
    def _create(menu_name=None, path=None, **kwargs):
        suffix = uuid.uuid4().hex[:8]
        menu_name = menu_name or f'AUTOTEST-menu-{suffix}'
        path = path or f'autotest-menu-{suffix}'
        result = menu_api.add_menu(menu_name, path, **kwargs)
        assert result.status_code == 200, result
        assert result.get('code') == 200, f'测试菜单创建失败: {result}'

        rows = track_test_menu(menu_name)
        assert len(rows) == 1, f'未找到唯一测试菜单: {rows}'
        return {
            'menu_name': menu_name,
            'path': path,
            'menu_id': rows[0]['menuId'],
            'row': rows[0],
        }

    return _create


# 跨 API/UI - 生成隔离的角色名称和权限字符
@pytest.fixture
def unique_role_identity():
    suffix = uuid.uuid4().hex[:8]
    return {
        'role_name': f'AUTOTEST-role-{suffix}',
        'role_key': f'autotest_{suffix}',
    }


# 跨 API/UI - 角色登记与安全清理
@pytest.fixture
def track_test_role(role_api):
    """只登记 AUTOTEST 角色，teardown 按精确 roleId 清理。"""
    tracked = {}

    def _track(role_name):
        if not role_name.startswith('AUTOTEST-role-'):
            raise ValueError(f'只允许登记 AUTOTEST 测试角色，收到: {role_name!r}')
        result = role_api.list_roles(roleName=role_name)
        rows = [
            row for row in result.get('rows', [])
            if row.get('roleName') == role_name
        ]
        for row in rows:
            tracked[row['roleId']] = role_name
        return rows

    yield _track

    for role_id, role_name in reversed(list(tracked.items())):
        try:
            result = role_api.list_roles(
                roleName='AUTOTEST-role-',
                pageNum=1,
                pageSize=1000,
            )
            current = next(
                (
                    row for row in result.get('rows', [])
                    if row.get('roleId') == role_id
                ),
                {},
            )
            safe_to_delete = (
                current.get('roleId') == role_id
                and current.get('roleName', '').startswith('AUTOTEST-role-')
                and current.get('roleKey', '').startswith('autotest_')
            )
            if safe_to_delete:
                role_api.delete_role(role_id)
        except Exception as exc:
            logging.warning(
                '清理测试角色失败: roleName=%s, roleId=%s, error=%s',
                role_name,
                role_id,
                exc,
            )


# 跨 API/UI - 通过接口创建并自动登记测试角色
@pytest.fixture
def create_test_role(role_api, track_test_role):
    def _create(role_name=None, role_key=None, **kwargs):
        suffix = uuid.uuid4().hex[:8]
        role_name = role_name or f'AUTOTEST-role-{suffix}'
        role_key = role_key or f'autotest_{suffix}'
        result = role_api.add_role(role_name, role_key, **kwargs)
        assert result.status_code == 200, result
        assert result.get('code') == 200, f'测试角色创建失败: {result}'

        rows = track_test_role(role_name)
        assert len(rows) == 1, f'未找到唯一测试角色: {rows}'
        return {
            'role_name': role_name,
            'role_key': role_key,
            'role_id': rows[0]['roleId'],
            'row': rows[0],
        }

    return _create


# 跨 API/UI - 测试用户登记与安全清理
@pytest.fixture
def track_test_user(user_api):
    """按精确用户名登记 AUTOTEST 用户，teardown 仅按其 userId 清理。

    该入口拒绝登记空用户名或固定业务账号，从机制上避免模糊查询后误删真实数据。
    """
    tracked = {}

    def _track(username):
        if not username.startswith('AUTOTEST-'):
            raise ValueError(f'只允许登记 AUTOTEST 测试用户，收到: {username!r}')
        result = user_api.list_user(username)
        rows = [
            row for row in result.get('rows', [])
            if row.get('userName') == username
        ]
        for row in rows:
            tracked[row['userId']] = username
        return rows

    yield _track

    for user_id, username in reversed(list(tracked.items())):
        try:
            result = user_api.list_user(username)
            still_exists = any(
                row.get('userName') == username and row.get('userId') == user_id
                for row in result.get('rows', [])
            )
            if still_exists:
                user_api.delete_user(user_id)
        except Exception as exc:
            logging.warning(
                '清理测试用户失败: username=%s, userId=%s, error=%s',
                username,
                user_id,
                exc,
            )


# 跨 API/UI - 通过接口创建并自动登记测试用户
@pytest.fixture
def create_test_user(user_api, track_test_user):
    def _create(username=None, nickname='自动化测试用户', **kwargs):
        username = username or f'AUTOTEST-{uuid.uuid4().hex[:8]}'
        payload = {'password': 'AutoTest123', 'status': '0'}
        payload.update(kwargs)
        result = user_api.add_user(username, nickname, **payload)
        assert result.status_code == 200, result
        assert result.get('code') == 200, f'测试用户创建失败: {result}'

        rows = track_test_user(username)
        assert len(rows) == 1, f'未找到唯一测试用户: {rows}'
        return {
            'username': username,
            'user_id': rows[0]['userId'],
            'password': payload['password'],
            'row': rows[0],
        }

    return _create


# 跨 API/UI - 导入用固定测试账号的前置清理与事后登记
@pytest.fixture
def import_test_username(user_api, track_test_user):
    username = 'AUTOTEST-import-fixture'
    stale_rows = [
        row for row in user_api.list_user(username).get('rows', [])
        if row.get('userName') == username
    ]
    for row in stale_rows:
        user_api.delete_user(row['userId'])

    yield username
    track_test_user(username)


# 全局浏览器 - CI 环境无头，本地默认有头
@pytest.fixture(scope='session')
def browser():
    pw = sync_playwright().start()
    b = None
    try:
        headless = os.getenv('CI', '') != ''
        b = pw.chromium.launch(headless=headless)
        yield b
    finally:
        if b is not None:
            b.close()
        pw.stop()


# 每条 UI 用例使用独立页面，避免登录态和页面状态互相污染
@pytest.fixture
def page(browser):
    p = browser.new_page(viewport={'width': 1440, 'height': 900})
    yield p
    p.close()


# 已登录页面 - 非登录模块复用，不重复验证登录表单
@pytest.fixture
def authenticated_page(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login(config['admin']['username'], config['admin']['password'])
    page.wait_for_url('**/index')
    return page


# 将用例执行结果暴露给失败截图 Fixture
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)





