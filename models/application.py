from . import db
from datetime import datetime
import uuid

class Application(db.Model):
    application_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.user_id', ondelete='CASCADE'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.drive_id', ondelete='CASCADE'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Registered')

    ticket_id = db.Column(db.String(36), unique=True, nullable=True, default=lambda: str(uuid.uuid4()))
    team_code = db.Column(db.String(20), nullable=True)
    is_present = db.Column(db.Boolean, default=False)
    certificate_sent = db.Column(db.Boolean, default=False)

    __table_args__ = (db.UniqueConstraint('student_id', 'drive_id', name='_student_drive_uc'),)

    def to_dict(self):
        return {
            'registration_id': self.application_id,
            'participant_id': self.student_id,
            'event_id': self.drive_id,
            'event_title': self.drive.job_title if self.drive else 'N/A',
            'organizer_name': self.drive.organizer_name if self.drive else 'N/A',
            'date': self.application_date.isoformat(),
            'status': self.status,
            'ticket_id': self.ticket_id,
            'team_code': self.team_code,
            'is_present': self.is_present,
            'certificate_sent': self.certificate_sent,
        }

    def updateStatus(self, new_status):
        self.status = new_status
        db.session.commit()
        return True
