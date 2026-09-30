import os

from common.http_client import HttpClient


class UserApi:
    """系统管理 / 用户管理 API。"""

    def __init__(self, token):
        self.client = HttpClient(token)

    def add_user(self, username, nickname, **kwargs):
        payload = {'userName': username, 'nickName': nickname}
        payload.update(kwargs)
        return self.client.post('/system/user', json=payload)

    def list_user(self, username):
        return self.list_users(userName=username)

    def list_users(self, **params):
        return self.client.get('/system/user/list', params=params)

    def get_user(self, user_id):
        return self.client.get(f'/system/user/{user_id}')

    def dept_tree(self):
        return self.client.get('/system/user/deptTree')

    def delete_user(self, user_id):
        return self.client.delete(f'/system/user/{user_id}')

    def delete_users(self, user_ids):
        joined_ids = ','.join(str(user_id) for user_id in user_ids)
        return self.client.delete(f'/system/user/{joined_ids}')

    def update_user(self, user_id, **kwargs):
        payload = {'userId': user_id}
        payload.update(kwargs)
        return self.client.put('/system/user', json=payload)

    def change_status(self, user_id, status):
        return self.client.put(
            '/system/user/changeStatus',
            json={'userId': user_id, 'status': status},
        )

    def reset_password(self, user_id, password):
        return self.client.put(
            '/system/user/resetPwd',
            json={'userId': user_id, 'password': password},
        )

    def import_template(self):
        return self.client.download('POST', '/system/user/importTemplate')

    def import_users(self, file_path, update_support=False):
        with open(file_path, 'rb') as file:
            return self.client.post(
                '/system/user/importData',
                params={'updateSupport': str(update_support).lower()},
                files={
                    'file': (
                        os.path.basename(file_path),
                        file,
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    )
                },
            )

    def export_users(self, **filters):
        return self.client.download(
            'POST',
            '/system/user/export',
            data=filters,
        )

    def close(self):
        self.client.close()
