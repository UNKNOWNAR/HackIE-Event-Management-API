from . import db
from datetime import datetime

class PlacementDrive(db.Model):
    drive_id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    organizer_name = db.Column(db.String(255), nullable=True, default='HackIE³ Team')
    job_title = db.Column(db.String(255), nullable=False)
    job_description = db.Column(db.Text, nullable=False)

    eligible_branch = db.Column(db.String(100), nullable=True)
    cgpa_required = db.Column(db.Float, default=0.0)
    eligible_year = db.Column(db.Integer, nullable=True)

    application_deadline = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='approved')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    event_type = db.Column(db.String(50), nullable=True, default='general')
    venue = db.Column(db.String(255), nullable=True)
    max_team_size = db.Column(db.Integer, nullable=True, default=1)

    applications = db.relationship('Application', backref='drive', cascade="all, delete-orphan")

    ALLOWED_FIELDS = {
        'job_title', 'job_description',
        'eligible_branch', 'cgpa_required', 'eligible_year',
        'application_deadline', 'status', 'organizer_name',
        'event_type', 'venue', 'max_team_size'
    }

    def to_dict(self):
        return {
            'event_id': self.drive_id,
            'created_by': self.created_by,
            'organizer_name': self.organizer_name,
            'title': self.job_title,
            'description': self.job_description,
            'eligible_branch': self.eligible_branch,
            'cgpa_required': self.cgpa_required,
            'eligible_year': self.eligible_year,
            'deadline': self.application_deadline.isoformat() if self.application_deadline else None,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'event_type': self.event_type,
            'venue': self.venue,
            'max_team_size': self.max_team_size
        }

    def updateData(self, data):
        for key, value in data.items():
            if key in PlacementDrive.ALLOWED_FIELDS:
                if key == 'application_deadline' and isinstance(value, str):
                    value = datetime.fromisoformat(value)
                setattr(self, key, value)
        db.session.commit()
        return True
