import random
from app import create_app, init_db
from models import db, User, Student, PlacementDrive, Application, user_datastore
from flask_security.utils import hash_password
from datetime import datetime, timedelta

app, _ = create_app()

def seed_data():
    with app.app_context():
        Application.query.delete()
        PlacementDrive.query.delete()
        Student.query.delete()
        User.query.filter(User.role != 'admin').delete()
        db.session.commit()

        # Ensure admin exists
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = user_datastore.create_user(
                username='admin',
                email='amiarinjaysarkar@gmail.com',
                password=hash_password('admin'),
                role='admin'
            )
            db.session.flush()

        admin_id = admin.user_id

        # ── Create Participants ──
        branches = ['Computer Science', 'Information Technology', 'Electronics', 'Mechanical', 'Civil']
        participant_data = [
            ('john_doe', 'john@example.com'), ('alice_smith', 'alice@example.com'),
            ('bob_jones', 'bob@example.com'), ('charlie_brown', 'charlie@example.com'),
            ('david_wilson', 'david@example.com'), ('emma_davis', 'emma@example.com'),
            ('frank_miller', 'frank@example.com'), ('grace_hopper', 'grace@example.com'),
            ('henry_ford', 'henry@example.com'), ('isabella_ross', 'isabella@example.com'),
            ('jack_chen', 'jack@example.com'), ('kate_lee', 'kate@example.com'),
        ]

        students = []
        for username, email in participant_data:
            user = user_datastore.create_user(
                username=username, email=email,
                password=hash_password('password123'),
                role='student', active=True
            )
            db.session.flush()
            student = Student(
                user_id=user.user_id,
                name=username.replace('_', ' ').title(),
                email=email,
                branch=random.choice(branches),
                batch_year=random.choice([2024, 2025, 2026]),
                cgpa=round(random.uniform(6.5, 9.8), 2)
            )
            db.session.add(student)
            students.append(student)

        db.session.commit()
        print(f"Created {len(students)} participants.")

        # ── Create Events (by admin) ──
        event_templates = [
            ('AI/ML Workshop', 'Hands-on workshop on building ML models with Python and TensorFlow.', 'workshop', 'Room 301, CS Block', 1, 'IEEE CS Chapter'),
            ('Hackathon 2026', '24-hour hackathon to build innovative solutions for real-world problems.', 'hackathon', 'Main Auditorium', 4, 'HackIE³ Team'),
            ('Cloud Computing Seminar', 'Industry expert session on AWS and Azure cloud architectures.', 'seminar', 'Seminar Hall A', 1, 'Google DSC'),
            ('Competitive Programming Contest', 'Solve algorithmic challenges under time pressure.', 'competition', 'Lab 204, IT Block', 2, 'ACM Student Chapter'),
            ('Web Dev Bootcamp', '3-day intensive bootcamp on full-stack web development with React and Flask.', 'workshop', 'Room 105, CS Block', 1, 'Mozilla Campus Club'),
            ('Startup Pitch Competition', 'Pitch your startup idea to a panel of investors and industry mentors.', 'competition', 'Conference Room B', 3, 'E-Cell'),
            ('Cybersecurity CTF', 'Capture-the-flag cybersecurity challenge for beginners and intermediates.', 'competition', 'Online - Discord', 3, 'Cyber Club'),
            ('Data Science Symposium', 'Research paper presentations and panel discussions on data science trends.', 'seminar', 'Auditorium 2', 1, 'IEEE CS Chapter'),
            ('Open Source Contribution Day', 'Contribute to real open-source projects with mentors from top companies.', 'workshop', 'Lab 301', 1, 'FOSS Club'),
            ('Robotics Challenge', 'Build and program robots to navigate obstacle courses.', 'competition', 'Robotics Lab', 4, 'Robo Club'),
        ]

        events = []
        for title, desc, etype, venue, team_size, org_name in event_templates:
            branch = random.choice(branches + ['All', 'All'])
            event = PlacementDrive(
                created_by=admin_id,
                organizer_name=org_name,
                job_title=title,
                job_description=desc,
                eligible_branch=branch,
                cgpa_required=round(random.uniform(5.5, 7.5), 1),
                eligible_year=random.choice([2025, 2026, None]),
                application_deadline=datetime.now() + timedelta(days=random.randint(7, 60)),
                status='approved',
                event_type=etype,
                venue=venue,
                max_team_size=team_size
            )
            db.session.add(event)
            events.append(event)

        db.session.commit()
        print(f"Created {len(events)} events.")

        # ── Create Registrations ──
        team_codes = ['ALPHA', 'BETA', 'GAMMA', 'DELTA', 'EPSILON', 'ZETA']
        print("Creating registrations...")
        for s in students:
            registered_events = random.sample(events, k=random.randint(1, 5))
            for evt in registered_events:
                team_code = None
                if evt.max_team_size > 1:
                    team_code = random.choice(team_codes) + str(evt.drive_id)

                status = random.choice(['Registered', 'Shortlisted', 'Selected'])
                is_present = random.choice([True, False]) if status == 'Selected' else False

                app_entry = Application(
                    student_id=s.user_id,
                    drive_id=evt.drive_id,
                    status=status,
                    team_code=team_code,
                    is_present=is_present
                )
                db.session.add(app_entry)

        db.session.commit()
        print("--- Database successfully seeded! ---")
        print("Admin:       admin / admin")
        print("Participant: john_doe / password123")

if __name__ == "__main__":
    seed_data()
