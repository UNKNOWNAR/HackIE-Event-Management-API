from flask import Flask
from models import db, cache, mail, user_datastore
from models.user import User
from config import Config
from flask_security import Security
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from api import init_api
from celery import Celery, Task
from flask_security.utils import hash_password
from flasgger import Swagger


class FlaskTask(Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


def celery_init_app(flask_app):
    celery = Celery(flask_app.import_name, task_cls=FlaskTask)
    celery.config_from_object(flask_app.config["CELERY"])
    celery.set_default()
    flask_app.extensions["celery"] = celery
    return celery


SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Event Management API",
        "description": "A full-featured Event Management REST API with RBAC authentication, QR ticketing, team registrations, certificate dispatch, and admin analytics.",
        "version": "2.0.0",
        "contact": {"email": "amiarinjaysarkar@gmail.com"}
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT token. Format: Bearer <token>"
        }
    },
    "security": [{"Bearer": []}],
    "tags": [
        {"name": "Auth", "description": "Authentication endpoints"},
        {"name": "Events", "description": "Event browsing and registration"},
        {"name": "Participant", "description": "Participant profile and history"},
        {"name": "Admin", "description": "Admin dashboard, event management, and analytics"},
    ]
}


def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)
    flask_app.config.from_mapping(
        CELERY=dict(
            broker_url=Config.CELERY_BROKER_URL,
            result_backend=Config.CELERY_RESULT_BACKEND,
            task_ignore_result=True,
            beat_schedule=Config.CELERY_BEAT_SCHEDULE,
            imports=['services.AdminStudentCSV', 'services.certificate_service'],
        ),
    )

    celery_init_app(flask_app)
    db.init_app(flask_app)
    cache.init_app(flask_app)
    mail.init_app(flask_app)
    Security(flask_app, user_datastore)
    JWTManager(flask_app)

    Swagger(flask_app, template=SWAGGER_TEMPLATE)

    api = Api(flask_app)
    api = init_api(api)

    return flask_app, api


def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='amiarinjaysarkar@gmail.com').first():
            user_datastore.create_user(
                username='admin',
                email='amiarinjaysarkar@gmail.com',
                password=hash_password('admin'),
                role='admin'
            )
            db.session.commit()


app, api = create_app()
celery_app = app.extensions["celery"]
CORS(app)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
