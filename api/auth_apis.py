from flask_restful import Resource
from flask import request
from models import db, User, Student, user_datastore
from sqlalchemy import or_
from flask_jwt_extended import create_access_token, jwt_required
from flask_security.utils import hash_password

class LoginUser(Resource):
    def post(self):
        """
        Login
        ---
        tags: [Auth]
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                username_or_email: { type: string, example: "admin" }
                password: { type: string, example: "admin" }
        responses:
          200: { description: Login successful }
          401: { description: Invalid password }
          404: { description: User not found }
        """
        login_data = request.get_json(silent=True)

        if not login_data:
            return {'message': 'JSON payload required', 'status': 'error'}, 400

        if not login_data.get('username_or_email') or not login_data.get('password'):
            return {'message': 'Username/Email and Password are required', 'status': 'error'}, 400

        identity = login_data.get('username_or_email')
        password = login_data.get('password')

        user = User.query.filter(
            or_(User.username == identity, User.email == identity)
        ).first()

        if not user:
            return {'message': 'User not found', 'status': 'error'}, 404

        if not user.check_password(password):
            return {'message': 'Invalid password', 'status': 'error'}, 401

        if not user.active:
            return {'message': 'User is not active', 'status': 'error'}, 403

        access_token = create_access_token(identity=str(user.user_id), additional_claims={'role': user.role})

        return {
            'message': 'Login successful',
            'access_token': access_token,
            'role': user.role,
            'username': user.username
        }, 200

class LogoutUser(Resource):
    @jwt_required()
    def post(self):
        """
        Logout
        ---
        tags: [Auth]
        security: [{ Bearer: [] }]
        responses:
          200: { description: Logout successful }
        """
        return {'message': 'Logout successful'}, 200

class SignUpUser(Resource):
    def post(self):
        """
        Sign Up (Participant only)
        ---
        tags: [Auth]
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                username: { type: string, example: "john_doe" }
                email: { type: string, example: "john@example.com" }
                password: { type: string, example: "password123" }
        responses:
          201: { description: User registered }
          409: { description: Username or email already exists }
        """
        register_data = request.get_json()

        if not register_data or not all(k in register_data for k in ('username', 'email', 'password')):
            return {'message': 'username, email, and password are required', 'status': 'error'}, 400

        username = register_data.get('username')
        email = register_data.get('email')
        password = register_data.get('password')

        existing_user = User.query.filter(
            or_(User.username == username, User.email == email)
        ).first()

        if existing_user:
            conflict_field = "Username" if existing_user.username == username else "Email"
            return {'message': f'{conflict_field} already exists', 'status': 'error'}, 409

        user = user_datastore.create_user(
            username=username,
            email=email,
            password=hash_password(password),
            role='student',
            active=True
        )
        db.session.flush()

        student_entry = Student(user_id=user.user_id, name=username, email=email)
        db.session.add(student_entry)
        db.session.commit()

        return {'message': 'Participant registered successfully', 'status': 'success'}, 201
