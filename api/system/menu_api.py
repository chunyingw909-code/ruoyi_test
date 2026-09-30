from common.http_client import HttpClient


class MenuApi:
    """系统管理 / 菜单管理 API。"""

    def __init__(self, token):
        self.client = HttpClient(token)

    def list_menus(self, **params):
        return self.client.get('/system/menu/list', params=params)

    def get_menu(self, menu_id):
        return self.client.get(f'/system/menu/{menu_id}')

    def tree_select(self):
        return self.client.get('/system/menu/treeselect')

    def add_menu(self, menu_name, path, **kwargs):
        payload = self._menu_payload(menu_name, path, **kwargs)
        return self.client.post('/system/menu', json=payload)

    def update_menu(self, menu_id, menu_name, path, **kwargs):
        payload = self._menu_payload(menu_name, path, **kwargs)
        payload['menuId'] = menu_id
        return self.client.put('/system/menu', json=payload)

    def delete_menu(self, menu_id):
        return self.client.delete(f'/system/menu/{menu_id}')

    @staticmethod
    def _menu_payload(menu_name, path, **kwargs):
        payload = {
            'parentId': 0,
            'menuName': menu_name,
            'icon': '#',
            'menuType': 'M',
            'orderNum': 10,
            'isFrame': '1',
            'isCache': '0',
            'visible': '0',
            'status': '0',
            'path': path,
            'component': '',
            'perms': '',
            'query': '',
            'remark': '自动化测试菜单',
        }
        payload.update(kwargs)
        return payload

    def close(self):
        self.client.close()
