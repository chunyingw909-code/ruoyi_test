from common.http_client import HttpClient


class RoleApi:
    """系统管理 / 角色管理 API。"""

    def __init__(self, token):
        self.client = HttpClient(token)

    def list_roles(self, **params):
        return self.client.get('/system/role/list', params=params)

    def get_role(self, role_id):
        return self.client.get(f'/system/role/{role_id}')

    def add_role(self, role_name, role_key, role_sort=1, **kwargs):
        payload = {
            'roleName': role_name,
            'roleKey': role_key,
            'roleSort': role_sort,
            'status': '0',
            'menuIds': [],
            'menuCheckStrictly': True,
        }
        payload.update(kwargs)
        return self.client.post('/system/role', json=payload)

    def update_role(self, role_id, **kwargs):
        payload = {'roleId': role_id}
        payload.update(kwargs)
        return self.client.put('/system/role', json=payload)

    def delete_role(self, role_id):
        return self.client.delete(f'/system/role/{role_id}')

    def delete_roles(self, role_ids):
        joined_ids = ','.join(str(role_id) for role_id in role_ids)
        return self.client.delete(f'/system/role/{joined_ids}')

    def change_status(self, role_id, status):
        return self.client.put(
            '/system/role/changeStatus',
            json={'roleId': role_id, 'status': status},
        )

    def menu_tree(self):
        return self.client.get('/system/menu/treeselect')

    def role_menu_tree(self, role_id):
        return self.client.get(f'/system/menu/roleMenuTreeselect/{role_id}')

    def dept_tree(self, role_id):
        return self.client.get(f'/system/role/deptTree/{role_id}')

    def change_data_scope(self, role_id, data_scope, dept_ids=None, **kwargs):
        payload = {
            'roleId': role_id,
            'dataScope': data_scope,
            'deptIds': dept_ids or [],
            'deptCheckStrictly': False,
        }
        payload.update(kwargs)
        return self.client.put('/system/role/dataScope', json=payload)

    def allocated_users(self, role_id, **params):
        query = {'roleId': role_id}
        query.update(params)
        return self.client.get(
            '/system/role/authUser/allocatedList',
            params=query,
        )

    def unallocated_users(self, role_id, **params):
        query = {'roleId': role_id}
        query.update(params)
        return self.client.get(
            '/system/role/authUser/unallocatedList',
            params=query,
        )

    def assign_users(self, role_id, user_ids):
        return self.client.put(
            '/system/role/authUser/selectAll',
            params={
                'roleId': role_id,
                'userIds': ','.join(str(user_id) for user_id in user_ids),
            },
        )

    def cancel_user(self, role_id, user_id):
        return self.client.put(
            '/system/role/authUser/cancel',
            json={'roleId': role_id, 'userId': user_id},
        )

    def cancel_users(self, role_id, user_ids):
        return self.client.put(
            '/system/role/authUser/cancelAll',
            params={
                'roleId': role_id,
                'userIds': ','.join(str(user_id) for user_id in user_ids),
            },
        )

    def export_roles(self, **filters):
        return self.client.download(
            'POST',
            '/system/role/export',
            data=filters,
        )

    def close(self):
        self.client.close()
