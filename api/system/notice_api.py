from common.http_client import HttpClient


class NoticeApi:
    """系统管理 / 通知公告 API。"""

    def __init__(self, token):
        self.client = HttpClient(token)

    def list_notices(self, **params):
        return self.client.get('/system/notice/list', params=params)

    def get_notice(self, notice_id):
        return self.client.get(f'/system/notice/{notice_id}')

    def add_notice(self, notice_title, notice_type='1', **kwargs):
        payload = self._notice_payload(notice_title, notice_type, **kwargs)
        return self.client.post('/system/notice', json=payload)

    def update_notice(self, notice_id, notice_title, notice_type='1', **kwargs):
        payload = self._notice_payload(notice_title, notice_type, **kwargs)
        payload['noticeId'] = notice_id
        return self.client.put('/system/notice', json=payload)

    def delete_notice(self, notice_id):
        return self.client.delete(f'/system/notice/{notice_id}')

    def delete_notices(self, notice_ids):
        joined_ids = ','.join(str(notice_id) for notice_id in notice_ids)
        return self.client.delete(f'/system/notice/{joined_ids}')

    def list_top(self):
        return self.client.get('/system/notice/listTop')

    def mark_read(self, notice_id):
        return self.client.post(
            '/system/notice/markRead', params={'noticeId': notice_id}
        )

    def list_read_users(self, notice_id):
        return self.client.get(
            '/system/notice/readUsers/list', params={'noticeId': notice_id}
        )

    @staticmethod
    def _notice_payload(notice_title, notice_type, **kwargs):
        payload = {
            'noticeTitle': notice_title,
            'noticeType': notice_type,
            'noticeContent': '自动化测试公告',
            'status': '0',
        }
        payload.update(kwargs)
        return payload

    def close(self):
        self.client.close()
