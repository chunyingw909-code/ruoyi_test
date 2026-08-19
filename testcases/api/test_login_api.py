import pytest
from api.login_api import LoginApi
from common.utils import read_yaml

data = read_yaml('data/login_data.yaml')

@pytest.mark.parametrize('case', data, ids=lambda x: x['desc'])
def test_login(case):
    api = LoginApi()
    result = api.login(case['username'], case['password'])
    assert result['code'] == case['expected_code']