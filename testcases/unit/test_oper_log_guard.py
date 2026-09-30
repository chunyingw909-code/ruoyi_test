"""OperLogLedger 纯单元测试。不访问若依，不跑界面。"""

from collections.abc import Mapping

import pytest

from common.oper_log_guard import OperLogLedger


class ApiResponseLike(Mapping):
    """非 dict 的 Mapping，对应 ApiResponse。"""

    def __init__(self, payload):
        self._payload = payload

    def __getitem__(self, key):
        return self._payload[key]

    def __iter__(self):
        return iter(self._payload)

    def __len__(self):
        return len(self._payload)


class FakeOperlogApi:
    def __init__(self, rows):
        self.rows = list(rows)
        self.deleted = []
        self.list_calls = 0
        self.clean_calls = 0

    def list_logs(self, **params):
        self.list_calls += 1
        self.last_params = params
        assert params.get('orderByColumn') == 'operId'
        assert params.get('isAsc') == 'desc'
        assert params.get('pageNum') == 1
        ordered = sorted(self.rows, key=lambda row: int(row['operId']), reverse=True)
        if params.get('pageSize') == 1:
            return {'rows': ordered[:1], 'total': len(self.rows)}
        assert params.get('pageSize') == 100
        return {'rows': list(self.rows), 'total': len(self.rows)}

    def delete_logs(self, oper_ids):
        self.deleted.append(list(oper_ids))
        return {'code': 200}

    def clean(self):
        self.clean_calls += 1
        raise AssertionError('禁止调用 clean')


def _row(oper_id, oper_param='', oper_url=''):
    return {'operId': oper_id, 'operParam': oper_param, 'operUrl': oper_url}


def _fast_clock(monkeypatch):
    clock = {'now': 0.0}
    monkeypatch.setattr('common.oper_log_guard.time.monotonic', lambda: clock['now'])

    def _sleep(seconds):
        clock['now'] += seconds

    monkeypatch.setattr('common.oper_log_guard.time.sleep', _sleep)


def test_history_and_unregistered_concurrent_logs_stay(monkeypatch):
    _fast_clock(monkeypatch)
    marker = 'AUTOTEST-user-a1b2c3d4'
    api = FakeOperlogApi([
        _row(10, oper_param=marker),
        _row(11, oper_param='AUTOTEST-other-ffffffff', oper_url='/system/role/88'),
    ])
    ledger = OperLogLedger(api, baseline_oper_id=10)
    ledger.register_marker(marker)
    ledger.register_url('/system/user/99')

    # 断言：基线及更早的日志、未登记的并发日志都不删除
    assert ledger.cleanup() == []
    assert api.deleted == []
    assert api.clean_calls == 0


def test_marker_exact_hit_deletes_only_that_oper_id(monkeypatch):
    monkeypatch.setattr('common.oper_log_guard.time.sleep', lambda _seconds: None)
    marker = 'autotest_post_00ab12ef'
    api = FakeOperlogApi([
        _row(4, oper_param='{"postName":"%s"}' % marker),
        _row(5, oper_param='AUTOTEST-other-11223344'),
    ])
    ledger = OperLogLedger(api, baseline_oper_id=3)
    ledger.register_marker(marker)

    # 断言：只有 operParam 含完整 marker 的新日志被按 operId 删除
    assert ledger.cleanup() == [4]
    assert api.deleted == [[4]]
    assert api.clean_calls == 0


def test_url_match_is_exact_after_normalize():
    api = FakeOperlogApi([])
    ledger = OperLogLedger(api, baseline_oper_id=7)
    ledger.register_url('/system/post/12/')
    api.rows.extend([
        _row(8, oper_url='/system/post/12'),
        _row(9, oper_url='/system/post/123'),
        _row(10, oper_url='/system/post/12/extra'),
        _row(11, oper_url='system/post/12?foo=1'),
    ])

    # 断言：前缀和更长路径不算命中；查询串去掉后与登记 URL 相等才删
    assert ledger.cleanup() == [8, 11]
    assert api.deleted == [[8, 11]]


def test_public_marker_and_generic_url_are_rejected():
    ledger = OperLogLedger(FakeOperlogApi([]), baseline_oper_id=1)
    for text in ('AUTOTEST', 'autotest', 'AUTOTEST-', 'AUTOTEST_user', 'autotest_deadbee'):
        with pytest.raises(ValueError):
            ledger.register_marker(text)
    for path in (
        '/monitor/operlog/clean',
        '/system/post/list',
        '/monitor/operlog/export',
        '/system/config/refreshCache',
        '/system/user/',
        '/system/user/0',
    ):
        with pytest.raises(ValueError):
            ledger.register_url(path)

    # 断言：拒绝之后账本为空，清理不会删任何日志
    assert ledger.cleanup() == []


def test_comma_separated_ids_and_oper_url_marker():
    marker = 'AUTOTEST-notice-deadbeef'
    api = FakeOperlogApi([
        _row(21, oper_url='/system/notice/21'),
        _row(22, oper_url='/system/notice/%s' % marker),
    ])
    ledger = OperLogLedger(api, baseline_oper_id=20)
    registered = ledger.register_url('/system/notice/21,22')
    ledger.register_marker(marker)
    api.rows.append(_row(23, oper_url='/system/notice/21,22'))

    # 断言：逗号 ID 路径可登记；operUrl 上的完整 marker 与精确 URL 都只按 operId 删除
    assert registered == '/system/notice/21,22'
    assert ledger.cleanup() == [22, 23]
    assert api.deleted == [[22, 23]]


def test_waits_for_later_url_log_after_marker(monkeypatch):
    _fast_clock(monkeypatch)
    marker = 'AUTOTEST-user-a1b2c3d4'
    waves = [
        [_row(31, oper_param=marker)],
        [_row(31, oper_param=marker), _row(32, oper_url='/system/user/32')],
    ]

    class WaveApi(FakeOperlogApi):
        def __init__(self):
            super().__init__([])
            self.wave = 0

        def list_logs(self, **params):
            self.list_calls += 1
            assert params.get('orderByColumn') == 'operId'
            assert params.get('isAsc') == 'desc'
            if params.get('pageSize') == 1:
                return {'rows': [], 'total': 0}
            assert params.get('pageSize') == 100
            rows = waves[min(self.wave, len(waves) - 1)]
            self.wave += 1
            return {'rows': rows, 'total': len(rows)}

    api = WaveApi()
    ledger = OperLogLedger(api, baseline_oper_id=30)
    ledger.register_marker(marker)
    ledger.register_url('/system/user/32')

    # 断言：先出现的 marker 不会让清理提前结束，稍后的删除 URL 也按精确 ID 删掉
    assert ledger.cleanup() == [31, 32]
    assert api.deleted == [[31, 32]]
    assert api.clean_calls == 0
    assert api.wave >= 2


def test_pages_past_100_and_skips_unregistered(monkeypatch):
    _fast_clock(monkeypatch)
    marker = 'autotest_dept_abcdef12'
    page_one = [_row(1000 - index, oper_param='AUTOTEST-other-11223344') for index in range(100)]
    page_two = [
        _row(800, oper_param=marker),
        _row(50, oper_param=marker),
    ]

    class PagedApi(FakeOperlogApi):
        def list_logs(self, **params):
            self.list_calls += 1
            assert params.get('orderByColumn') == 'operId'
            assert params.get('isAsc') == 'desc'
            assert params.get('pageSize') == 100
            page = params.get('pageNum')
            if page == 1:
                return {'rows': page_one, 'total': 102}
            if page == 2:
                return {'rows': page_two, 'total': 102}
            return {'rows': [], 'total': 102}

    api = PagedApi([])
    ledger = OperLogLedger(api, baseline_oper_id=100)
    ledger.register_marker(marker)

    # 断言：第二页基线之上的命中被删除；第一页未登记日志和基线及更早的日志保留
    assert ledger.cleanup() == [800]
    assert api.deleted == [[800]]
    assert api.clean_calls == 0


def test_bare_numeric_path_is_rejected():
    ledger = OperLogLedger(FakeOperlogApi([]), baseline_oper_id=1)
    with pytest.raises(ValueError):
        ledger.register_url('/123')


def test_mapping_response_parses_rows_total_and_deletes_exact_ids():
    marker = 'AUTOTEST-user-a1b2c3d4'

    class ShortMappingApi(FakeOperlogApi):
        def list_logs(self, **params):
            self.list_calls += 1
            assert params.get('pageSize') == 100
            response = ApiResponseLike({
                'rows': [
                    _row(11, oper_param=marker),
                    _row(10, oper_param=marker),
                ],
                'total': 2,
            })
            assert not isinstance(response, dict)
            return response

    short_api = ShortMappingApi([])
    short_ledger = OperLogLedger(short_api, baseline_oper_id=10)
    short_ledger.register_marker(marker)

    # 断言：非 dict Mapping 的 rows 会被读到，基线及更早的 operId 不删
    assert short_ledger.cleanup() == [11]
    assert short_api.deleted == [[11]]
    assert short_api.clean_calls == 0

    page_one = [_row(index, oper_param='plain') for index in range(200, 100, -1)]
    page_one[-1] = _row(102, oper_param=marker)
    assert len(page_one) == 100

    class PagedMappingApi(FakeOperlogApi):
        def list_logs(self, **params):
            self.list_calls += 1
            assert params.get('orderByColumn') == 'operId'
            assert params.get('isAsc') == 'desc'
            assert params.get('pageSize') == 100
            page = params.get('pageNum')
            if page == 1:
                payload = {'rows': page_one, 'total': 100}
            else:
                payload = {'rows': [_row(101, oper_param=marker)], 'total': 100}
            response = ApiResponseLike(payload)
            assert not isinstance(response, dict)
            return response

    paged_api = PagedMappingApi([])
    paged_ledger = OperLogLedger(paged_api, baseline_oper_id=100)
    paged_ledger.register_marker(marker)

    # 断言：total 被解析后不再请求下一页，只删本页精确命中的 operId
    assert paged_ledger.cleanup() == [102]
    assert paged_api.deleted == [[102]]
    assert paged_api.list_calls == 1
    assert paged_api.clean_calls == 0


def test_same_url_registrations_keep_separate_floors(monkeypatch):
    _fast_clock(monkeypatch)
    url = '/system/dict/type/221'

    class FloorApi(FakeOperlogApi):
        def __init__(self):
            super().__init__([])
            self.visible = 100
            self.polls = 0

        def list_logs(self, **params):
            self.list_calls += 1
            assert params.get('orderByColumn') == 'operId'
            assert params.get('isAsc') == 'desc'
            assert params.get('pageNum') == 1
            if params.get('pageSize') == 1:
                return {'rows': [_row(self.visible)], 'total': 1}
            assert params.get('pageSize') == 100
            self.polls += 1
            rows = [
                _row(130, oper_url='/system/role/88'),
                _row(110, oper_url=url),
                _row(90, oper_url=url),
            ]
            if self.polls >= 2:
                rows.insert(1, _row(120, oper_url=url))
            return {'rows': rows, 'total': len(rows)}

    api = FloorApi()
    ledger = OperLogLedger(api, baseline_oper_id=100)
    ledger.register_url(url)
    api.visible = 110
    ledger.register_url(url)

    # 断言：第一条登记不能用失败删除日志盖过第二次；两条精确日志都删，历史和未登记保留
    assert ledger.cleanup() == [110, 120]
    assert api.deleted == [[110, 120]]
    assert api.polls >= 2
    assert api.clean_calls == 0
