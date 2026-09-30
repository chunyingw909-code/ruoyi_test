from common.http_client import HttpClient


class PostApi:
    """系统管理 / 岗位管理 API。"""

    def __init__(self, token):
        self.client = HttpClient(token)

    def list_posts(self, **params):
        return self.client.get('/system/post/list', params=params)

    def get_post(self, post_id):
        return self.client.get(f'/system/post/{post_id}')

    def add_post(self, post_name, post_code, post_sort=10, **kwargs):
        payload = self._post_payload(post_name, post_code, post_sort, **kwargs)
        return self.client.post('/system/post', json=payload)

    def update_post(self, post_id, post_name, post_code, post_sort=10, **kwargs):
        payload = self._post_payload(post_name, post_code, post_sort, **kwargs)
        payload['postId'] = post_id
        return self.client.put('/system/post', json=payload)

    def delete_post(self, post_id):
        return self.client.delete(f'/system/post/{post_id}')

    def delete_posts(self, post_ids):
        joined_ids = ','.join(str(post_id) for post_id in post_ids)
        return self.client.delete(f'/system/post/{joined_ids}')

    def export_posts(self, **filters):
        return self.client.download('POST', '/system/post/export', data=filters)

    @staticmethod
    def _post_payload(post_name, post_code, post_sort, **kwargs):
        payload = {
            'postName': post_name,
            'postCode': post_code,
            'postSort': post_sort,
            'status': '0',
            'remark': '自动化测试岗位',
        }
        payload.update(kwargs)
        return payload

    def close(self):
        self.client.close()
