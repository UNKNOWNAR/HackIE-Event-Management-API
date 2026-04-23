from flask import request
from models import db, PlacementDrive, Application, Student
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_restful import Resource
from models import cache


class EventListAPI(Resource):
    """GET /events — Browse approved events with optional filters"""
    @jwt_required()
    def get(self):
        """
        List Events
        ---
        tags: [Events]
        security: [{ Bearer: [] }]
        parameters:
          - { name: type, in: query, type: string, description: "Filter by event_type (workshop, hackathon, seminar, competition)" }
          - { name: venue, in: query, type: string, description: "Filter by venue (partial match)" }
          - { name: branch, in: query, type: string, description: "Filter by eligible branch" }
        responses:
          200: { description: List of approved events }
        """
        query = PlacementDrive.query.filter(PlacementDrive.status == 'approved')

        event_type = request.args.get('type')
        if event_type:
            query = query.filter(PlacementDrive.event_type == event_type)

        venue = request.args.get('venue')
        if venue:
            query = query.filter(PlacementDrive.venue.ilike(f'%{venue}%'))

        branch = request.args.get('branch')
        if branch:
            query = query.filter(
                (PlacementDrive.eligible_branch == branch) | (PlacementDrive.eligible_branch == 'All')
            )

        events = query.all()
        return [e.to_dict() for e in events], 200


class EventDetailAPI(Resource):
    """GET /events/<id> — Single event detail"""
    @jwt_required()
    def get(self, event_id):
        """
        Event Detail
        ---
        tags: [Events]
        security: [{ Bearer: [] }]
        parameters:
          - { name: event_id, in: path, type: integer, required: true }
        responses:
          200: { description: Event details }
          404: { description: Event not found }
        """
        event = PlacementDrive.query.get(event_id)
        if not event:
            return {'message': 'Event not found'}, 404
        data = event.to_dict()
        data['registration_count'] = Application.query.filter_by(drive_id=event_id).count()
        return data, 200


class EventRegisterAPI(Resource):
    """POST /events/<id>/register — Participant registers for an event"""
    @jwt_required()
    def post(self, event_id):
        """
        Register for Event
        ---
        tags: [Events]
        security: [{ Bearer: [] }]
        parameters:
          - { name: event_id, in: path, type: integer, required: true }
          - in: body
            name: body
            schema:
              type: object
              properties:
                team_code: { type: string, example: "ALPHA42", description: "Optional team code for team events" }
        responses:
          201: { description: Registration successful }
          400: { description: Eligibility or team error }
          409: { description: Already registered }
        """
        claims = get_jwt()
        if claims.get('role') != 'student':
            return {'message': 'Participant access required'}, 403

        user_id = get_jwt_identity()
        student = Student.query.get(user_id)
        if not student:
            return {'message': 'Participant profile not found'}, 404

        event = PlacementDrive.query.get(event_id)
        if not event or event.status != 'approved':
            return {'message': 'Event is not available for registration'}, 404

        if student.cgpa and event.cgpa_required and student.cgpa < event.cgpa_required:
            return {'message': 'You do not meet the minimum CGPA requirement.'}, 400
        if event.eligible_branch and event.eligible_branch != 'All' and event.eligible_branch != student.branch:
            return {'message': 'You do not belong to the eligible branch for this event.'}, 400
        if event.eligible_year and student.batch_year and event.eligible_year != student.batch_year:
            return {'message': f'Only candidates from the {event.eligible_year} batch are eligible.'}, 400

        if Application.query.filter_by(student_id=user_id, drive_id=event_id).first():
            return {'message': 'Already registered'}, 409

        data = request.get_json(silent=True) or {}
        team_code = data.get('team_code')

        max_team = event.max_team_size or 1
        if max_team <= 1:
            team_code = None

        if team_code and max_team > 1:
            existing_team = Application.query.filter_by(drive_id=event_id, team_code=team_code).count()
            if existing_team >= max_team:
                return {'message': 'Team is full'}, 400

        new_app = Application(
            student_id=user_id,
            drive_id=event_id,
            status='Registered',
            team_code=team_code
        )
        db.session.add(new_app)
        db.session.commit()

        cache.delete(f"student_events_{user_id}")

        return {
            'message': 'Registration successful!',
            'ticket_id': new_app.ticket_id,
            'team_code': new_app.team_code
        }, 201


class CancelRegistrationAPI(Resource):
    """DELETE /my/registrations/<reg_id>"""
    @jwt_required()
    def delete(self, reg_id):
        """
        Cancel Registration
        ---
        tags: [Events]
        security: [{ Bearer: [] }]
        parameters:
          - { name: reg_id, in: path, type: integer, required: true }
        responses:
          200: { description: Registration cancelled }
          404: { description: Registration not found }
        """
        claims = get_jwt()
        if claims.get('role') != 'student':
            return {'message': 'Participant access required'}, 403

        user_id = get_jwt_identity()
        reg = Application.query.filter_by(application_id=reg_id, student_id=user_id).first()
        if not reg:
            return {'message': 'Registration not found'}, 404

        db.session.delete(reg)
        db.session.commit()
        cache.delete(f"student_events_{user_id}")
        return {'message': 'Registration cancelled'}, 200


class TeamViewAPI(Resource):
    """GET /my/team/<team_code> — View teammates"""
    @jwt_required()
    def get(self, team_code):
        """
        View Team Members
        ---
        tags: [Events]
        security: [{ Bearer: [] }]
        parameters:
          - { name: team_code, in: path, type: string, required: true }
        responses:
          200: { description: Team member list }
          404: { description: No team found }
        """
        members = Application.query.filter_by(team_code=team_code).all()
        if not members:
            return {'message': 'No team found with this code'}, 404

        result = []
        for m in members:
            student = Student.query.get(m.student_id)
            result.append({
                'participant_id': m.student_id,
                'name': student.name if student else 'Unknown',
                'email': student.email if student else 'Unknown',
                'status': m.status
            })
        return {'team_code': team_code, 'members': result}, 200


class TicketQRAPI(Resource):
    """GET /ticket/<ticket_id>/qr — Returns base64 QR image"""
    @jwt_required()
    def get(self, ticket_id):
        """
        Get Ticket QR Code
        ---
        tags: [Events]
        security: [{ Bearer: [] }]
        parameters:
          - { name: ticket_id, in: path, type: string, required: true }
        responses:
          200: { description: Base64 QR code image }
          404: { description: Ticket not found }
        """
        reg = Application.query.filter_by(ticket_id=ticket_id).first()
        if not reg:
            return {'message': 'Ticket not found'}, 404

        from services.qr_service import generate_qr_base64
        qr_data = generate_qr_base64(ticket_id)
        return {'ticket_id': ticket_id, 'qr_base64': qr_data}, 200
