import pytest
from common.utils import read_yaml
from api.user_api import UserApi


add_data = read_yaml('data/user_add_data.yaml')

@pytest.mark.parametrize('case', add_data, ids=lambda x: x['desc'])
def test_add_user(case, login_token, cleanup_user):
    api = UserApi(login_token)
    cleanup_user.append(case['userName'])

    result = api.add_user(case['userName'], case['nickName'])
    assert result['code'] == case['expected_code']









