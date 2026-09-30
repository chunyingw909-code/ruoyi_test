from common.http_client import HttpClient


class OperlogApi:
    """系统管理 / 操作日志 API。

    不封装清空：`DELETE /monitor/operlog/clean` 会删掉全部操作日志。
    """

    def __init__(self, token):
        self.client = HttpClient(token)

    def list_logs(self, **params):
        return self.client.get('/monitor/operlog/list', params=params)

    def delete_log(self, oper_id):
        return self.client.delete(f'/monitor/operlog/{oper_id}')

    def delete_logs(self, oper_ids):
        joined_ids = ','.join(str(oper_id) for oper_id in oper_ids)
        return self.client.delete(f'/monitor/operlog/{joined_ids}')

    def export_logs(self, **filters):
        return self.client.download('POST', '/monitor/operlog/export', data=filters)

    def close(self):
        self.client.close()
