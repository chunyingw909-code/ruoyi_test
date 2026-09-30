"""操作日志登记与精确清理。只按 operId 删除本次登记命中的新日志。"""

from __future__ import annotations

import re
import time
from collections.abc import Mapping
from typing import Any, Iterable

# 完整 AUTOTEST/autotest 标识，必须以 8 位十六进制结尾。公共前缀不能登记。
_FULL_MARKER = re.compile(r"(?i)^[A-Za-z0-9_-]*autotest[A-Za-z0-9_-]*[0-9a-f]{8}$")
_HEX_SUFFIX = re.compile(r"(?i)[0-9a-f]{8}$")
_GENERIC_URL_SEGMENTS = frozenset(
    {"clean", "list", "export", "refreshcache", "import", "add", "edit", "remove"}
)
_EXACT_ID_PATH = re.compile(r"^/(?:[^/?#]+/)+(\d+(?:,\d+)*)$")
_POLL_DEADLINE_SEC = 5.0
_POLL_INTERVAL_SEC = 0.25
_PAGE_SIZE = 100


class OperLogLedger:
    """登记本次用例的完整 marker 与精确资源 URL，teardown 时只删命中的新操作日志。"""

    def __init__(self, operlog_api: Any, baseline_oper_id: int) -> None:
        self._api = operlog_api
        self._baseline = int(baseline_oper_id or 0)
        self._markers: set[str] = set()
        self._url_regs: list[tuple[str, int]] = []

    def register_marker(self, text: str) -> str:
        marker = (text or "").strip()
        if not _FULL_MARKER.fullmatch(marker) or not _HEX_SUFFIX.search(marker):
            raise ValueError(
                "register_marker 只接受带 8 位十六进制后缀的完整 AUTOTEST/autotest 标识"
            )
        self._markers.add(marker)
        return marker

    def register_url(self, path: str) -> str:
        normalized = _normalize_oper_url(path)
        if not _is_exact_id_url(normalized):
            raise ValueError(
                "register_url 只接受以数字 ID 或逗号分隔数字 ID 结尾的精确 API 路径"
            )
        self._url_regs.append((normalized, self._visible_max_oper_id()))
        return normalized

    def _visible_max_oper_id(self) -> int:
        payload = self._api.list_logs(
            pageNum=1,
            pageSize=1,
            orderByColumn="operId",
            isAsc="desc",
        )
        rows = list(_as_rows(payload))
        if not rows:
            return 0
        return _oper_id(rows[0])

    def cleanup(self) -> list[int]:
        """查询 operId 大于基线的新日志，只删除登记命中的 operId。"""
        rows = self._poll_new_rows()
        oper_ids = sorted({row_id for row_id in (self._match_id(row) for row in rows) if row_id})
        if oper_ids:
            self._api.delete_logs(oper_ids)
        return oper_ids

    def _fetch_new_rows(self) -> list[dict]:
        collected: list[dict] = []
        page = 1
        while True:
            payload = self._api.list_logs(
                pageNum=page,
                pageSize=_PAGE_SIZE,
                orderByColumn="operId",
                isAsc="desc",
            )
            rows = list(_as_rows(payload))
            if not rows:
                break
            reached_baseline = False
            for row in rows:
                if _oper_id(row) <= self._baseline:
                    reached_baseline = True
                    break
                collected.append(row)
            total = _total(payload)
            if reached_baseline or len(rows) < _PAGE_SIZE or (total is not None and page * _PAGE_SIZE >= total):
                break
            page += 1
        return collected

    def _poll_new_rows(self) -> list[dict]:
        """跨轮询累计命中。marker 与 URL 都登记时，每一项至少命中一次才停，最多等 5 秒。"""
        if not self._markers and not self._url_regs:
            return [row for row in self._fetch_new_rows() if self._match_id(row)]
        deadline = time.monotonic() + _POLL_DEADLINE_SEC
        matched: dict[int, dict] = {}
        while True:
            for row in self._fetch_new_rows():
                oper_id = self._match_id(row)
                if oper_id:
                    matched[oper_id] = row
            if self._registrations_covered(matched.values()) or time.monotonic() >= deadline:
                return list(matched.values())
            time.sleep(_POLL_INTERVAL_SEC)

    def _registrations_covered(self, rows: Iterable[dict]) -> bool:
        pending_markers = set(self._markers)
        covered = [False] * len(self._url_regs)
        for row in rows:
            oper_id = _oper_id(row)
            oper_param = str(row.get("operParam") or "")
            oper_url = str(row.get("operUrl") or "")
            pending_markers = {
                marker for marker in pending_markers if marker not in oper_param and marker not in oper_url
            }
            normalized = _normalize_oper_url(oper_url)
            for index, (url, floor) in enumerate(self._url_regs):
                if oper_id > self._baseline and oper_id > floor and normalized == url:
                    covered[index] = True
        return not pending_markers and all(covered)

    def _match_id(self, row: dict) -> int | None:
        oper_id = _oper_id(row)
        if oper_id <= self._baseline:
            return None
        oper_param = str(row.get("operParam") or "")
        oper_url = str(row.get("operUrl") or "")
        if any(marker in oper_param or marker in oper_url for marker in self._markers):
            return oper_id
        normalized = _normalize_oper_url(oper_url)
        if any(oper_id > floor and normalized == url for url, floor in self._url_regs):
            return oper_id
        return None


def _normalize_oper_url(path: str) -> str:
    text = (path or "").strip()
    if not text:
        return ""
    text = text.split("?", 1)[0].split("#", 1)[0]
    if not text.startswith("/"):
        text = "/" + text
    text = re.sub(r"/{2,}", "/", text)
    if len(text) > 1:
        text = text.rstrip("/")
    return text


def _is_exact_id_url(path: str) -> bool:
    match = _EXACT_ID_PATH.fullmatch(path)
    if not match:
        return False
    segments = [segment.lower() for segment in path.strip("/").split("/") if segment]
    if any(segment in _GENERIC_URL_SEGMENTS for segment in segments):
        return False
    ids = match.group(1).split(",")
    return all(part.isdigit() and int(part) > 0 for part in ids)


def _total(payload: Any) -> int | None:
    if not isinstance(payload, Mapping) or payload.get("total") is None:
        return None
    try:
        return int(payload["total"])
    except (TypeError, ValueError):
        return None


def _oper_id(row: dict) -> int:
    raw = row.get("operId", row.get("oper_id", 0))
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def _is_record(value: Any) -> bool:
    return isinstance(value, Mapping)


def _as_rows(payload: Any) -> Iterable[Mapping]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [row for row in payload if _is_record(row)]
    if isinstance(payload, Mapping):
        for key in ("rows", "data", "list"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if _is_record(row)]
        if "operId" in payload or "oper_id" in payload:
            return [payload]
    return []
