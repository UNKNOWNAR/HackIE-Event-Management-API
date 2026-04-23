from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_mail import Mail
from flask_security import SQLAlchemyUserDatastore

db = SQLAlchemy()
cache = Cache()
mail = Mail()

from models.user import User
user_datastore = SQLAlchemyUserDatastore(db, User, None)

from models.students import Student
from models.placement import PlacementDrive
from models.application import Application
