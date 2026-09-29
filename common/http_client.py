import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

import requests

from common.utils import load_config

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ApiResponse(Mapping):
    """同时保留 HTTP 状态和 JSON 响应体。

    实现 Mapping 是为了让现有调用仍可使用 response['code'] 和 response.get()。
    """

    status_code: int
    body: dict[str, Any]

    def __getitem__(self, key):
        return self.body[key]

    def __iter__(self) -> Iterator:
        return iter(self.body)

    def __len__(self):
        return len(self.body)

    def __repr__(self):
        return f'ApiResponse(status_code={self.status_code}, body={self.body!r})'


@dataclass(frozen=True)
class FileResponse:
    """文件下载响应，保留 HTTP 状态、响应头和二进制内容。"""

    status_code: int
    headers: dict[str, str]
    content: bytes

    @property
    def content_type(self):
        return self.headers.get('Content-Type', '')


class HttpClient:
    def __init__(self, token=None):
        config = load_config()
        self.base_url = config['base_url']
        self.timeout = config.get('request_timeout', 10)
        self.s = requests.Session()
        if token:
            self.s.headers['Authorization'] = f'Bearer {token}'

    def _send(self, method, path, **kwargs):
        url = self.base_url + path
        log.info(f"{method} {url}")
        try:
            kwargs.setdefault('timeout', self.timeout)
            r = self.s.request(method, url, **kwargs)
        except requests.RequestException as e:
            log.error(f"请求失败: {e}")
            raise
        log.info(f"响应 {r.status_code}")
        return r

    def _request(self, method, path, **kwargs):
        r = self._send(method, path, **kwargs)
        try:
            body = r.json()
            if not isinstance(body, dict):
                raise ValueError(f"{r.url} JSON 响应不是对象: {type(body).__name__}")
            return ApiResponse(status_code=r.status_code, body=body)
        except requests.exceptions.JSONDecodeError:
            log.error(f"非JSON响应: {r.text[:200]}")
            raise ValueError(f"{r.url} 返回非JSON，状态码{r.status_code}")

    def post(self, path, **kwargs):
        return self._request('POST', path, **kwargs)

    def get(self, path, **kwargs):
        return self._request('GET', path, **kwargs)

    def delete(self, path, **kwargs):
        return self._request('DELETE', path, **kwargs)

    def put(self, path, **kwargs):
        return self._request('PUT', path, **kwargs)

    def download(self, method, path, **kwargs):
        r = self._send(method, path, **kwargs)
        return FileResponse(
            status_code=r.status_code,
            headers=dict(r.headers),
            content=r.content,
        )

    def close(self):
        self.s.close()
