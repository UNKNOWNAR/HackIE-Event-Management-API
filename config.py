import os
from dotenv import load_dotenv
from celery.schedules import crontab

load_dotenv()

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///pathfinder.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Security settings
    SECURITY_PASSWORD_SALT = "salt-key"
    SECURITY_TOKEN_AUTHENTICATION_HEADER = "Authentication-Token"
    SECURITY_REGISTER_BLUEPRINT = False  # Disable default Flask-Security routes to use our own
    
    # JWT Config
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "pathfinder-jwt-secret-key-2026-secure!!")
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour in seconds

    # Cache Configuration
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = "redis://localhost:6379/0" 
    CACHE_DEFAULT_TIMEOUT = 300 

    # Celery Configuration
    CELERY_BROKER_URL = "redis://localhost:6379/1" 
    CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
    CELERY_TIMEZONE = "UTC"
    CELERY_BEAT_SCHEDULE = {
        'send-daily-reminders': {
            'task': 'services.AdminStudentCSV.daily_reminder_task',
            'schedule': crontab(hour=0, minute=0),  # Every day at midnight
        },
        'generate-monthly-report': {
            'task': 'services.AdminStudentCSV.monthly_report_task',
            'schedule': crontab(day_of_month=1, hour=0, minute=0),  # 1st of every month
        },
    }

    # Mail Configuration (Gmail SSL Setup)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "REDACTED_EMAIL")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "REDACTED")
    MAIL_DEFAULT_SENDER = MAIL_USERNAME
