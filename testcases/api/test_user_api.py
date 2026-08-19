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

def test_delete_user(login_token, create_user):
    api = UserApi(login_token)
    result = api.delete_user(create_user['user_id'])
    assert result['code'] == 200









