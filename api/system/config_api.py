from common.http_client import HttpClient


class ConfigApi:
    """系统管理 / 参数设置 API。"""

    def __init__(self, token):
        self.client = HttpClient(token)

    def list_configs(self, **params):
        return self.client.get('/system/config/list', params=params)

    def get_config(self, config_id):
        return self.client.get(f'/system/config/{config_id}')

    def get_value_by_key(self, config_key):
        return self.client.get(f'/system/config/configKey/{config_key}')

    def add_config(self, config_name, config_key, config_value='autotest', **kwargs):
        payload = self._config_payload(
            config_name, config_key, config_value, **kwargs
        )
        return self.client.post('/system/config', json=payload)

    def update_config(
        self, config_id, config_name, config_key, config_value, **kwargs
    ):
        payload = self._config_payload(
            config_name, config_key, config_value, **kwargs
        )
        payload['configId'] = config_id
        return self.client.put('/system/config', json=payload)

    def delete_config(self, config_id):
        return self.client.delete(f'/system/config/{config_id}')

    def delete_configs(self, config_ids):
        joined_ids = ','.join(str(config_id) for config_id in config_ids)
        return self.client.delete(f'/system/config/{joined_ids}')

    def export_configs(self, **filters):
        return self.client.download('POST', '/system/config/export', data=filters)

    def refresh_cache(self):
        return self.client.delete('/system/config/refreshCache')

    @staticmethod
    def _config_payload(config_name, config_key, config_value, **kwargs):
        payload = {
            'configName': config_name,
            'configKey': config_key,
            'configValue': config_value,
            'configType': 'N',
            'remark': '自动化测试参数',
        }
        payload.update(kwargs)
        return payload

    def close(self):
        self.client.close()
