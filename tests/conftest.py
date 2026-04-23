import pytest
from app import create_app
from models import db as _db
from flask_security.utils import hash_password
from models import user_datastore
from models.students import Student


@pytest.fixture(scope='session')
def app():
    flask_app, _ = create_app()
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'CACHE_TYPE': 'SimpleCache',
        'WTF_CSRF_ENABLED': False,
        'SECURITY_PASSWORD_SALT': 'test-salt',
        'JWT_SECRET_KEY': 'test-jwt-key',
    })
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()


@pytest.fixture(scope='session')
def admin_token(app, client):
    with app.app_context():
        user_datastore.create_user(
            username='testadmin', email='testadmin@test.com',
            password=hash_password('admin123'), role='admin'
        )
        _db.session.commit()
    resp = client.post('/login', json={
        'username_or_email': 'testadmin', 'password': 'admin123'
    })
    return resp.get_json()['access_token']


@pytest.fixture(scope='session')
def participant_token(app, client):
    with app.app_context():
        user = user_datastore.create_user(
            username='testparticipant', email='testp@test.com',
            password=hash_password('pass123'), role='student', active=True
        )
        _db.session.flush()
        student = Student(user_id=user.user_id, name='Test Participant', email='testp@test.com',
                          branch='Computer Science', cgpa=8.5, batch_year=2025)
        _db.session.add(student)
        _db.session.commit()
    resp = client.post('/login', json={
        'username_or_email': 'testparticipant', 'password': 'pass123'
    })
    return resp.get_json()['access_token']
