from flask_restful import Resource
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt
from models import db, cache
from models.students import Student
from models.user import User
from models.application import Application


class ParticipantProfileAPI(Resource):
    """GET/PUT /participant/profile"""
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        cache_key = f"student_{user_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data, 200

        student = Student.query.filter_by(user_id=user_id).first()
        if student:
            cache.set(cache_key, student.to_dict())
            return student.to_dict(), 200
        return {'message': 'Participant record not found'}, 404

    @jwt_required()
    def put(self):
        user_id = get_jwt_identity()
        student = Student.query.filter_by(user_id=user_id).first()
        payload = request.get_json()

        if student:
            if not payload:
                return {'message': 'No data provided'}, 400

            user = User.query.get(user_id)
            if 'email' in payload and payload['email'] != user.email:
                existing = User.query.filter(User.email == payload['email'], User.user_id != user_id).first()
                if existing:
                    return {'message': 'This email address is already in use by another account.'}, 409
                user.email = payload['email']

            if 'name' in payload:
                del payload['name']

            student.updateData(payload)
            cache.delete(f"student_{user_id}")
            cache.delete(f"student_drives_{user_id}")
            db.session.commit()
            return {'message': 'Participant profile updated'}, 200
        else:
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                return {'message': 'User account mismatch'}, 404

            student = Student(user_id=user_id, name=user.username, email=user.email)
            student.updateData(payload)
            cache.delete(f"student_{user_id}")
            cache.delete(f"student_drives_{user_id}")
            db.session.add(student)
            db.session.commit()
            return {'message': 'Participant record created successfully'}, 201


class ParticipantStatsAPI(Resource):
    """GET /participant/stats"""
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        applied = Application.query.filter_by(student_id=user_id).count()
        shortlisted = Application.query.filter(Application.student_id == user_id, Application.status.ilike('shortlisted')).count()
        selected = Application.query.filter(Application.student_id == user_id, Application.status.ilike('selected')).count()
        attended = Application.query.filter(Application.student_id == user_id, Application.is_present == True).count()
        return {
            'registered': applied,
            'shortlisted': shortlisted,
            'selected': selected,
            'attended': attended
        }, 200


class MyRegistrationsAPI(Resource):
    """GET /my/registrations — All my registrations with ticket info"""
    @jwt_required()
    def get(self):
        claims = get_jwt()
        if claims.get('role') != 'student':
            return {'message': 'Participant access required'}, 403
        user_id = get_jwt_identity()
        apps = Application.query.filter_by(student_id=user_id).all()
        return [app.to_dict() for app in apps], 200


class ParticipantExportAPI(Resource):
    """GET /participant/export — Email CSV of own history"""
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        student = Student.query.filter_by(user_id=user_id).first()
        if not student:
            return {'message': 'Participant not found'}, 404

        from services.AdminStudentCSV import export_student_history
        task = export_student_history.delay(user_id, student.email)
        return {"task_id": task.id, "message": f"Exporting history to {student.email}..."}, 200
