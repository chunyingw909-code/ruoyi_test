import requests
import logging
from common.utils import read_yaml

log = logging.getLogger(__name__)

class HttpClient:
    def __init__(self, token=None):
        config = read_yaml('config/config.yaml')
        self.base_url = config['base_url']
        self.s = requests.Session()
        if token:
            self.s.headers['Authorization'] = f'Bearer {token}'

    def _request(self, method, path, **kwargs):
        url = self.base_url + path
        log.info(f"{method} {url}")
        try:
            r = self.s.request(method, url, **kwargs)
        except Exception as e:
            log.error(f"请求失败: {e}")
            raise
        log.info(f"响应 {r.status_code}")
        try:
            return r.json()
        except Exception:
            log.error(f"非JSON响应: {r.text[:200]}")
            raise ValueError(f"{url} 返回非JSON，状态码{r.status_code}")

    def post(self, path, **kwargs):
        return self._request('POST', path, **kwargs)

    def get(self, path, **kwargs):
        return self._request('GET', path, **kwargs)

    def delete(self, path, **kwargs):
        return self._request('DELETE', path, **kwargs)