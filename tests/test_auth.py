def test_signup_success(client):
    resp = client.post('/signup', json={
        'username': 'newuser1', 'email': 'new1@test.com',
        'password': 'testpass'
    })
    assert resp.status_code == 201
    assert resp.get_json()['status'] == 'success'


def test_signup_duplicate_rejected(client):
    client.post('/signup', json={
        'username': 'dupuser', 'email': 'dup@test.com',
        'password': 'testpass'
    })
    resp = client.post('/signup', json={
        'username': 'dupuser', 'email': 'dup@test.com',
        'password': 'testpass'
    })
    assert resp.status_code == 409


def test_login_success_returns_token(client):
    client.post('/signup', json={
        'username': 'logintest', 'email': 'login@test.com',
        'password': 'testpass'
    })
    resp = client.post('/login', json={
        'username_or_email': 'logintest', 'password': 'testpass'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'access_token' in data
    assert data['role'] == 'student'


def test_login_wrong_password_rejected(client):
    resp = client.post('/login', json={
        'username_or_email': 'logintest', 'password': 'wrongpass'
    })
    assert resp.status_code == 401
