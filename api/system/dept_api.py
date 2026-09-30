from common.http_client import HttpClient


class DeptApi:
    """系统管理 / 部门管理 API。"""

    def __init__(self, token):
        self.client = HttpClient(token)

    def list_depts(self, **params):
        return self.client.get('/system/dept/list', params=params)

    def get_dept(self, dept_id):
        return self.client.get(f'/system/dept/{dept_id}')

    def exclude_tree(self, dept_id):
        return self.client.get(f'/system/dept/list/exclude/{dept_id}')

    def add_dept(self, dept_name, parent_id=100, **kwargs):
        payload = self._dept_payload(dept_name, parent_id, **kwargs)
        return self.client.post('/system/dept', json=payload)

    def update_dept(self, dept_id, dept_name, parent_id=100, **kwargs):
        payload = self._dept_payload(dept_name, parent_id, **kwargs)
        payload['deptId'] = dept_id
        return self.client.put('/system/dept', json=payload)

    def delete_dept(self, dept_id):
        return self.client.delete(f'/system/dept/{dept_id}')

    @staticmethod
    def _dept_payload(dept_name, parent_id, **kwargs):
        payload = {
            'parentId': parent_id,
            'deptName': dept_name,
            'orderNum': 10,
            'leader': '自动化测试',
            'phone': '',
            'email': '',
            'status': '0',
        }
        payload.update(kwargs)
        return payload

    def close(self):
        self.client.close()
