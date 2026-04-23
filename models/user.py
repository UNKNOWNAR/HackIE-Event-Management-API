from . import db
from werkzeug.security import generate_password_hash
from flask_security.utils import verify_password as fs_verify_password, hash_password as fs_hash_password
import uuid

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)#255 size to store large size of hashing password
    # Roles: 'admin', 'student'
    role = db.Column(db.String(80), nullable=False,default='student')
    fs_uniquifier = db.Column(db.String(255), nullable=False,unique=True,default=lambda: str(uuid.uuid4()))

    active = db.Column(db.Boolean, nullable=False,default=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def __init__(self, **kwargs):
        # Flask-Security automatically passes 'roles', so we pop it to prevent SQLAlchemy errors
        kwargs.pop('roles', None)
        super(User, self).__init__(**kwargs)

    @property
    def roles(self):
        # Flask-Security expects `roles` to be an iterable, so we return the single role in a list
        return [self.role]
    
    def set_password(self, password):
        self.password = fs_hash_password(password)
    
    def check_password(self, password):
        return fs_verify_password(password, self.password)

