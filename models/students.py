from . import db

class Student(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'), primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(100), nullable=True)   # Optional until profile update
    cgpa = db.Column(db.Float, nullable=True, default=0.0)
    batch_year = db.Column(db.Integer, nullable=True)

    # Relationships
    applications = db.relationship('Application', backref='student_obj', lazy=True)

    def __repr__(self):
        return f'<Student {self.name}>'

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'branch': self.branch,
            'cgpa': self.cgpa,
            'batch_year': self.batch_year,
            'applications': [app.to_dict() for app in self.applications] # History included
        }

    # Only allow updates to core academic fields
    ALLOWED_FIELDS = {'name', 'email', 'branch', 'cgpa', 'batch_year'}

    def updateData(self, data):
        for key, value in data.items():
            if key in Student.ALLOWED_FIELDS:
                setattr(self, key, value)
        return self
