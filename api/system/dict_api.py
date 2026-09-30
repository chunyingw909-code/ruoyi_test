from common.http_client import HttpClient


class DictTypeApi:
    """系统管理 / 字典类型 API。"""

    def __init__(self, token):
        self.client = HttpClient(token)

    def list_dict_types(self, **params):
        return self.client.get('/system/dict/type/list', params=params)

    def get_dict_type(self, dict_id):
        return self.client.get(f'/system/dict/type/{dict_id}')

    def optionselect(self):
        return self.client.get('/system/dict/type/optionselect')

    def add_dict_type(self, dict_name, dict_type, **kwargs):
        payload = self._type_payload(dict_name, dict_type, **kwargs)
        return self.client.post('/system/dict/type', json=payload)

    def update_dict_type(self, dict_id, dict_name, dict_type, **kwargs):
        payload = self._type_payload(dict_name, dict_type, **kwargs)
        payload['dictId'] = dict_id
        return self.client.put('/system/dict/type', json=payload)

    def delete_dict_type(self, dict_id):
        return self.client.delete(f'/system/dict/type/{dict_id}')

    def delete_dict_types(self, dict_ids):
        joined_ids = ','.join(str(dict_id) for dict_id in dict_ids)
        return self.client.delete(f'/system/dict/type/{joined_ids}')

    def export_dict_types(self, **filters):
        return self.client.download('POST', '/system/dict/type/export', data=filters)

    def refresh_cache(self):
        return self.client.delete('/system/dict/type/refreshCache')

    @staticmethod
    def _type_payload(dict_name, dict_type, **kwargs):
        payload = {
            'dictName': dict_name,
            'dictType': dict_type,
            'status': '0',
            'remark': '自动化测试字典',
        }
        payload.update(kwargs)
        return payload

    def close(self):
        self.client.close()


class DictDataApi:
    """系统管理 / 字典数据 API。"""

    def __init__(self, token):
        self.client = HttpClient(token)

    def list_dict_data(self, **params):
        return self.client.get('/system/dict/data/list', params=params)

    def get_dict_data(self, dict_code):
        return self.client.get(f'/system/dict/data/{dict_code}')

    def list_by_type(self, dict_type):
        return self.client.get(f'/system/dict/data/type/{dict_type}')

    def add_dict_data(self, dict_label, dict_value, dict_type, **kwargs):
        payload = self._data_payload(dict_label, dict_value, dict_type, **kwargs)
        return self.client.post('/system/dict/data', json=payload)

    def update_dict_data(self, dict_code, dict_label, dict_value, dict_type, **kwargs):
        payload = self._data_payload(dict_label, dict_value, dict_type, **kwargs)
        payload['dictCode'] = dict_code
        return self.client.put('/system/dict/data', json=payload)

    def delete_dict_data(self, dict_code):
        return self.client.delete(f'/system/dict/data/{dict_code}')

    def delete_dict_data_batch(self, dict_codes):
        joined_ids = ','.join(str(dict_code) for dict_code in dict_codes)
        return self.client.delete(f'/system/dict/data/{joined_ids}')

    def export_dict_data(self, **filters):
        return self.client.download('POST', '/system/dict/data/export', data=filters)

    @staticmethod
    def _data_payload(dict_label, dict_value, dict_type, **kwargs):
        payload = {
            'dictLabel': dict_label,
            'dictValue': dict_value,
            'dictType': dict_type,
            'dictSort': 1,
            'status': '0',
            'remark': '自动化测试字典数据',
        }
        payload.update(kwargs)
        return payload

    def close(self):
        self.client.close()
