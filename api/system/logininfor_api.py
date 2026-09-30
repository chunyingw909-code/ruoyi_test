from common.http_client import HttpClient


class LogininforApi:
    """系统管理 / 登录日志 API。

    不封装清空：`DELETE /monitor/logininfor/clean` 会删掉全部登录日志。
    """

    def __init__(self, token):
        self.client = HttpClient(token)

    def list_logs(self, **params):
        return self.client.get('/monitor/logininfor/list', params=params)

    def delete_log(self, info_id):
        return self.client.delete(f'/monitor/logininfor/{info_id}')

    def delete_logs(self, info_ids):
        joined_ids = ','.join(str(info_id) for info_id in info_ids)
        return self.client.delete(f'/monitor/logininfor/{joined_ids}')

    def export_logs(self, **filters):
        return self.client.download(
            'POST', '/monitor/logininfor/export', data=filters
        )

    def unlock(self, username):
        return self.client.get(f'/monitor/logininfor/unlock/{username}')

    def close(self):
        self.client.close()
