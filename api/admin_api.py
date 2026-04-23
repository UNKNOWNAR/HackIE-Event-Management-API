from functools import wraps
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from flask_restful import Resource
from models import db, User, Student, PlacementDrive, Application
from models import cache


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return {'message': 'Admin access required'}, 403
        return fn(*args, **kwargs)
    return wrapper


# ─── Dashboard ───

class AdminStatsAPI(Resource):
    @admin_required
    def get(self):
        """
        Admin Dashboard Stats
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        responses:
          200: { description: Dashboard counts }
        """
        participant_count = Student.query.count()
        event_count = PlacementDrive.query.count()
        registration_count = Application.query.count()
        attended_count = Application.query.filter_by(is_present=True).count()
        attendance_rate = round((attended_count / registration_count * 100), 1) if registration_count > 0 else 0.0
        return {
            'participant_count': participant_count,
            'event_count': event_count,
            'registration_count': registration_count,
            'attended_count': attended_count,
            'attendance_rate': attendance_rate
        }, 200


# ─── Event CRUD ───

class AdminCreateEventAPI(Resource):
    @admin_required
    def post(self):
        """
        Create Event
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                job_title: { type: string, example: "AI Workshop 2026" }
                job_description: { type: string, example: "Hands-on ML workshop" }
                eligible_branch: { type: string, example: "All" }
                cgpa_required: { type: number, example: 6.0 }
                eligible_year: { type: integer, example: 2026 }
                event_type: { type: string, example: "workshop" }
                venue: { type: string, example: "Room 301, CS Block" }
                max_team_size: { type: integer, example: 1 }
                organizer_name: { type: string, example: "IEEE CS Chapter" }
                application_deadline: { type: string, example: "2026-05-15T23:59:00" }
        responses:
          201: { description: Event created }
        """
        user_id = get_jwt_identity()
        data = request.get_json()

        event = PlacementDrive(
            created_by=int(user_id),
            organizer_name=data.get('organizer_name', 'HackIE³ Team'),
            job_title=data.get('job_title'),
            job_description=data.get('job_description'),
            eligible_branch=data.get('eligible_branch', 'All'),
            cgpa_required=data.get('cgpa_required', 0.0),
            eligible_year=data.get('eligible_year'),
            event_type=data.get('event_type', 'general'),
            venue=data.get('venue'),
            max_team_size=data.get('max_team_size', 1),
            application_deadline=data.get('application_deadline'),
            status='approved'
        )

        if isinstance(event.application_deadline, str):
            from datetime import datetime
            event.application_deadline = datetime.fromisoformat(event.application_deadline)

        db.session.add(event)
        db.session.commit()
        cache.clear()
        return {'message': 'Event created successfully', 'event_id': event.drive_id}, 201


class AdminEventsAPI(Resource):
    @admin_required
    def get(self):
        """
        List All Events (with filters)
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - { name: status, in: query, type: string, description: "Filter by status (approved, pending, rejected)" }
          - { name: type, in: query, type: string, description: "Filter by event_type" }
        responses:
          200: { description: List of events }
        """
        query = PlacementDrive.query

        status = request.args.get('status')
        if status:
            query = query.filter(PlacementDrive.status == status)

        event_type = request.args.get('type')
        if event_type:
            query = query.filter(PlacementDrive.event_type == event_type)

        events = query.all()
        return [e.to_dict() for e in events], 200


class AdminEventAPI(Resource):
    @admin_required
    def get(self, event_id):
        """
        Get Event Detail with Registrations
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - { name: event_id, in: path, type: integer, required: true }
        responses:
          200: { description: Event with registrations }
          404: { description: Event not found }
        """
        event = PlacementDrive.query.get(event_id)
        if not event:
            return {'message': 'Event not found'}, 404

        registrations = Application.query.filter_by(drive_id=event_id).all()
        reg_list = []
        for reg in registrations:
            data = reg.to_dict()
            student = Student.query.get(reg.student_id)
            data['participant_name'] = student.name if student else 'Unknown'
            data['participant_email'] = student.email if student else 'Unknown'
            reg_list.append(data)

        result = event.to_dict()
        result['registrations'] = reg_list
        result['registration_count'] = len(reg_list)
        return result, 200

    @admin_required
    def patch(self, event_id):
        """
        Update Event
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - { name: event_id, in: path, type: integer, required: true }
          - in: body
            name: body
            schema:
              type: object
              properties:
                job_title: { type: string }
                job_description: { type: string }
                status: { type: string, example: "approved" }
                venue: { type: string }
                event_type: { type: string }
                max_team_size: { type: integer }
        responses:
          200: { description: Event updated }
          404: { description: Event not found }
        """
        event = PlacementDrive.query.get(event_id)
        if not event:
            return {'message': 'Event not found'}, 404

        data = request.get_json()
        event.updateData(data)
        cache.clear()
        return {'message': 'Event updated'}, 200

    @admin_required
    def delete(self, event_id):
        """
        Delete Event
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - { name: event_id, in: path, type: integer, required: true }
        responses:
          200: { description: Event deleted }
          404: { description: Event not found }
        """
        event = PlacementDrive.query.get(event_id)
        if not event:
            return {'message': 'Event not found'}, 404

        db.session.delete(event)
        db.session.commit()
        cache.clear()
        return {'message': 'Event deleted successfully'}, 200


# ─── Participants ───

class AdminParticipantsAPI(Resource):
    @admin_required
    def get(self):
        """
        List All Participants (with filters)
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - { name: branch, in: query, type: string }
          - { name: batch, in: query, type: integer }
        responses:
          200: { description: List of participants }
        """
        query = Student.query
        branch = request.args.get('branch')
        if branch:
            query = query.filter(Student.branch == branch)
        batch = request.args.get('batch')
        if batch:
            query = query.filter(Student.batch_year == int(batch))

        students = query.all()
        result = []
        for s in students:
            user = User.query.get(s.user_id)
            result.append({
                'user_id': s.user_id,
                'name': s.name,
                'email': s.email,
                'branch': s.branch,
                'batch_year': s.batch_year,
                'cgpa': s.cgpa,
                'active': user.active if user else False
            })
        return result, 200


class AdminToggleUserStatusAPI(Resource):
    @admin_required
    def post(self, user_id):
        """
        Toggle User Active Status
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - { name: user_id, in: path, type: integer, required: true }
        responses:
          200: { description: User status toggled }
          404: { description: User not found }
        """
        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404
        if user.role == 'admin':
            return {'message': 'Cannot deactivate admin'}, 403

        user.active = not user.active
        db.session.commit()
        cache.clear()

        status_text = "activated" if user.active else "deactivated"
        return {'message': f'User {status_text} successfully!', 'active': user.active}, 200


# ─── Registrations ───

class AdminRegistrationsAPI(Resource):
    @admin_required
    def get(self):
        """
        List All Registrations (with filters)
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - { name: event_id, in: query, type: integer }
          - { name: present, in: query, type: string, description: "true or false" }
          - { name: status, in: query, type: string }
        responses:
          200: { description: List of registrations }
        """
        query = Application.query

        event_id = request.args.get('event_id')
        if event_id:
            query = query.filter(Application.drive_id == int(event_id))

        present = request.args.get('present')
        if present is not None:
            query = query.filter(Application.is_present == (present.lower() == 'true'))

        status = request.args.get('status')
        if status:
            query = query.filter(Application.status == status)

        registrations = query.all()
        result = []
        for reg in registrations:
            data = reg.to_dict()
            student = Student.query.get(reg.student_id)
            data['participant_name'] = student.name if student else 'Unknown'
            data['participant_email'] = student.email if student else 'Unknown'
            result.append(data)
        return result, 200


class AdminBulkStatusAPI(Resource):
    @admin_required
    def patch(self):
        """
        Bulk Update Registration Status
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                ids: { type: array, items: { type: integer }, example: [1, 2, 3] }
                status: { type: string, example: "Selected" }
        responses:
          200: { description: Bulk update result }
        """
        data = request.get_json()
        ids = data.get('ids', [])
        new_status = data.get('status')

        if not ids or not new_status:
            return {'message': 'ids and status are required'}, 400

        updated = 0
        for app_id in ids:
            app = Application.query.get(app_id)
            if app:
                app.status = new_status
                updated += 1

        db.session.commit()
        return {'message': f'{updated} registrations updated to {new_status}'}, 200


class AdminUpdateRegistrationAPI(Resource):
    @admin_required
    def put(self, registration_id):
        """
        Update Single Registration Status
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - { name: registration_id, in: path, type: integer, required: true }
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                status: { type: string, example: "Selected" }
        responses:
          200: { description: Registration updated }
          404: { description: Registration not found }
        """
        app = Application.query.get(registration_id)
        if not app:
            return {'message': 'Registration not found'}, 404

        data = request.get_json()
        new_status = data.get('status')
        app.status = new_status
        db.session.commit()

        if new_status.lower() == 'selected':
            from services.AdminStudentCSV import send_offer_letter
            student = Student.query.get(app.student_id)
            drive = PlacementDrive.query.get(app.drive_id)
            if student and drive:
                send_offer_letter.delay(student.name, student.email, drive.job_title, drive.organizer_name)

        return {'message': 'Registration status updated'}, 200


# ─── QR Attendance ───

class AdminScanAttendanceAPI(Resource):
    @admin_required
    def post(self, ticket_id):
        """
        Scan QR — Mark Attendance
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - { name: ticket_id, in: path, type: string, required: true }
        responses:
          200: { description: Attendance marked }
          404: { description: Ticket not found }
        """
        reg = Application.query.filter_by(ticket_id=ticket_id).first()
        if not reg:
            return {'message': 'Ticket not found'}, 404

        if reg.is_present:
            return {'message': 'Already marked as present'}, 200

        reg.is_present = True
        db.session.commit()

        student = Student.query.get(reg.student_id)
        return {
            'message': 'Attendance marked',
            'participant': student.name if student else 'Unknown',
            'event_id': reg.drive_id
        }, 200


# ─── Certificates ───

class AdminDispatchCertificatesAPI(Resource):
    @admin_required
    def post(self, event_id):
        """
        Dispatch Certificates to Attendees
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - { name: event_id, in: path, type: integer, required: true }
        responses:
          200: { description: Certificate dispatch queued }
          404: { description: Event not found }
        """
        drive = PlacementDrive.query.get(event_id)
        if not drive:
            return {'message': 'Event not found'}, 404

        from services.certificate_service import dispatch_certificates
        task = dispatch_certificates.delay(event_id)
        return {'task_id': task.id, 'message': f'Certificate dispatch queued for: {drive.job_title}'}, 200


# ─── Mass Email ───

class AdminMassEmailAPI(Resource):
    @admin_required
    def post(self):
        """
        Send Mass Email
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                subject: { type: string, example: "Important Update" }
                body: { type: string, example: "Hello everyone!" }
                filter:
                  type: object
                  properties:
                    branch: { type: string, example: "Computer Science" }
                    batch_year: { type: integer, example: 2026 }
        responses:
          200: { description: Mass email queued }
        """
        data = request.get_json()
        subject = data.get('subject')
        body = data.get('body')
        filters = data.get('filter', {})

        if not subject or not body:
            return {'message': 'subject and body are required'}, 400

        query = Student.query
        if filters.get('branch'):
            query = query.filter(Student.branch == filters['branch'])
        if filters.get('batch_year'):
            query = query.filter(Student.batch_year == int(filters['batch_year']))

        recipients = query.all()
        if not recipients:
            return {'message': 'No participants match the filter'}, 404

        from services.AdminStudentCSV import send_mass_email
        emails = [s.email for s in recipients]
        task = send_mass_email.delay(subject, body, emails)
        return {'task_id': task.id, 'message': f'Mass email queued to {len(emails)} recipients'}, 200


# ─── Export ───

class AdminExportAPI(Resource):
    @admin_required
    def get(self, target):
        """
        Export CSV (participants, events, registrations)
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        parameters:
          - { name: target, in: path, type: string, required: true, description: "participants, events, or registrations" }
        responses:
          200: { description: Export task queued }
        """
        from services.AdminStudentCSV import export_resource_csv

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        admin_email = user.email if user else "admin@example.com"

        task = export_resource_csv.delay(target, admin_email)
        return {"task_id": task.id, "message": f"Exporting {target} to {admin_email}..."}, 200


class AdminMonthlyReportAPI(Resource):
    @admin_required
    def get(self):
        """
        Trigger Monthly Report
        ---
        tags: [Admin]
        security: [{ Bearer: [] }]
        responses:
          200: { description: Report generation triggered }
        """
        from services.AdminStudentCSV import monthly_report_task
        task = monthly_report_task.delay()
        return {"task_id": task.id, "message": "Triggered monthly report generation..."}, 200
