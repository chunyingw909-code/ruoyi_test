import yaml
import os


def read_yaml(file_path):
    base_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir,file_path)
    with open(full_path,'r',encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_config():
    """读取本地配置，并允许 CI 通过环境变量覆盖连接信息。"""
    config = read_yaml('config/config.yaml')
    config['base_url'] = os.getenv('BASE_URL', config['base_url'])
    config['ui_url'] = os.getenv('UI_URL', config['ui_url'])
    config['admin']['username'] = os.getenv(
        'ADMIN_USERNAME',
        config['admin']['username'],
    )
    config['admin']['password'] = os.getenv(
        'ADMIN_PASSWORD',
        config['admin']['password'],
    )
    return config


def project_path(*parts):
    """返回项目根目录下文件的绝对路径。"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, *parts)








