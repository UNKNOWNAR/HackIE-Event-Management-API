import csv
import os
from celery import shared_task
from datetime import datetime
from flask_mail import Message
from models import db, Student, PlacementDrive, Application, mail

EXPORT_DIR = os.path.join("static", "exports")
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)


@shared_task(ignore_result=False)
def export_resource_csv(resource_type, to_email, drive_id=None):
    filename = f"{resource_type}_export.csv"
    filepath = os.path.join(EXPORT_DIR, filename)

    with open(filepath, mode='w', newline='') as file:
        writer = csv.writer(file)

        if resource_type in ('students', 'participants'):
            writer.writerow(['ID', 'Name', 'Email', 'Branch', 'CGPA', 'Batch Year'])
            data = Student.query.all()
            for s in data:
                writer.writerow([s.user_id, s.name, s.email, s.branch, s.cgpa, s.batch_year])

        elif resource_type == 'events':
            writer.writerow(['ID', 'Title', 'Type', 'Venue', 'Status', 'Deadline', 'Registrations'])
            data = PlacementDrive.query.all()
            for e in data:
                reg_count = Application.query.filter_by(drive_id=e.drive_id).count()
                writer.writerow([e.drive_id, e.job_title, e.event_type, e.venue, e.status,
                                 e.application_deadline, reg_count])

        elif resource_type == 'registrations':
            writer.writerow(['Reg ID', 'Participant', 'Email', 'Event', 'Status', 'Present', 'Team Code', 'Date'])
            data = Application.query.all()
            for a in data:
                student = Student.query.get(a.student_id)
                drive = PlacementDrive.query.get(a.drive_id)
                writer.writerow([
                    a.application_id,
                    student.name if student else 'N/A',
                    student.email if student else 'N/A',
                    drive.job_title if drive else 'N/A',
                    a.status, a.is_present, a.team_code,
                    a.application_date
                ])

        elif resource_type == 'applicants' and drive_id:
            writer.writerow(['Participant Name', 'Email', 'Status', 'Present', 'Team Code', 'Date'])
            apps = Application.query.filter_by(drive_id=drive_id).all()
            for a in apps:
                student = Student.query.get(a.student_id)
                writer.writerow([student.name, student.email, a.status, a.is_present, a.team_code, a.application_date])

    try:
        subject = f"Event Management Export: {resource_type.capitalize()}"
        msg = Message(subject, recipients=[to_email])
        msg.body = f"Attached is the requested CSV report for {resource_type}."
        with open(filepath, "rb") as f:
            msg.attach(filename, "text/csv", f.read())
        mail.send(msg)
        return f"Export sent to {to_email}"
    except Exception as e:
        print(f"[ERROR] Mail failed: {str(e)}")
        return f"CSV saved at {filepath}, but mail failed."


@shared_task(ignore_result=False)
def export_student_history(student_id, to_email):
    filename = f"participant_{student_id}_history.csv"
    filepath = os.path.join(EXPORT_DIR, filename)

    apps = Application.query.filter_by(student_id=student_id).all()

    with open(filepath, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Registration ID', 'Event Title', 'Organizer', 'Status', 'Present', 'Date'])
        for a in apps:
            drive = PlacementDrive.query.get(a.drive_id)
            writer.writerow([
                a.application_id,
                drive.job_title if drive else 'N/A',
                drive.organizer_name if drive else 'N/A',
                a.status,
                a.is_present,
                a.application_date
            ])

    try:
        msg = Message("Your Event Registration History", recipients=[to_email])
        msg.body = "Hi! Attached is your complete event registration history."
        with open(filepath, "rb") as f:
            msg.attach(filename, "text/csv", f.read())
        mail.send(msg)
        return f"History sent to {to_email}"
    except Exception as e:
        print(f"[ERROR] Export mail failed: {str(e)}")
        return f"CSV saved at {filepath}, but mail failed."


@shared_task
def monthly_report_task():
    from models.user import User

    total_participants = Student.query.count()
    total_events = PlacementDrive.query.count()
    approved_events = PlacementDrive.query.filter_by(status='approved').count()
    total_registrations = Application.query.count()
    attended_count = Application.query.filter_by(is_present=True).count()
    selected_count = Application.query.filter_by(status='Selected').count()

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f8f9fa; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background: #fff; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;">
            <div style="background: #0d6efd; color: #fff; padding: 24px; text-align: center;">
                <h1 style="margin: 0;">HackIE&sup3; Event Portal</h1>
                <p style="margin: 4px 0 0; opacity: 0.9;">Monthly Activity Report</p>
            </div>
            <div style="padding: 32px;">
                <h3 style="color: #333;">Platform Overview</h3>
                <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 12px 8px; font-weight: bold;">Total Participants</td>
                        <td style="padding: 12px 8px; text-align: right; color: #0d6efd; font-weight: bold;">{total_participants}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 12px 8px; font-weight: bold;">Total Events</td>
                        <td style="padding: 12px 8px; text-align: right; color: #198754; font-weight: bold;">{total_events}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 12px 8px; font-weight: bold;">Approved Events</td>
                        <td style="padding: 12px 8px; text-align: right;">{approved_events}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 12px 8px; font-weight: bold;">Total Registrations</td>
                        <td style="padding: 12px 8px; text-align: right; font-weight: bold;">{total_registrations}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 12px 8px; font-weight: bold;">Attended</td>
                        <td style="padding: 12px 8px; text-align: right; color: #198754; font-weight: bold;">{attended_count}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 8px; font-weight: bold;">Selected</td>
                        <td style="padding: 12px 8px; text-align: right; color: #ffc107; font-weight: bold;">{selected_count}</td>
                    </tr>
                </table>
            </div>
            <div style="background: #f8f9fa; padding: 16px; text-align: center; color: #6c757d; font-size: 12px;">
                Auto-generated by HackIE&sup3; Event Management Portal
            </div>
        </div>
    </body>
    </html>
    """

    try:
        from xhtml2pdf import pisa
        from io import BytesIO

        admin = User.query.filter_by(role='admin').first()
        admin_email = admin.email if admin else "admin@example.com"

        pdf_filename = f"monthly_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        pdf_path = os.path.join(EXPORT_DIR, pdf_filename)

        with open(pdf_path, "w+b") as result_file:
            pisa_status = pisa.CreatePDF(html_body, dest=result_file)

        if pisa_status.err:
            return "PDF generation failed"

        msg = Message("Monthly Event Analytics [PDF]", recipients=[admin_email])
        msg.body = "Hi Admin! Attached is your monthly PDF report for the event management portal."

        with open(pdf_path, "rb") as f:
            msg.attach("monthly_report.pdf", "application/pdf", f.read())

        mail.send(msg)
        return f"Monthly PDF report sent to {admin_email}"
    except Exception as e:
        print(f"[ERROR] Monthly report PDF failed: {str(e)}")
        return f"Report generation failed: {str(e)}"


@shared_task
def daily_reminder_task():
    from datetime import timedelta
    from models import Student, PlacementDrive, Application, mail

    now = datetime.utcnow()
    deadline_threshold = now + timedelta(days=3)
    upcoming_events = PlacementDrive.query.filter(
        PlacementDrive.status == 'approved',
        PlacementDrive.application_deadline > now,
        PlacementDrive.application_deadline <= deadline_threshold
    ).all()

    if not upcoming_events:
        return "No upcoming deadlines to notify."

    reminders_sent = 0
    for event in upcoming_events:
        students = Student.query.all()
        for s in students:
            already_registered = Application.query.filter_by(student_id=s.user_id, drive_id=event.drive_id).first()
            if already_registered:
                continue

            if event.eligible_branch and event.eligible_branch != 'All' and event.eligible_branch != s.branch:
                continue
            if s.cgpa and event.cgpa_required and s.cgpa < event.cgpa_required:
                continue
            if event.eligible_year and s.batch_year and event.eligible_year != s.batch_year:
                continue

            try:
                msg = Message(
                    f"Reminder: Deadline Approaching for {event.job_title}",
                    recipients=[s.email]
                )
                msg.body = (
                    f"Hi {s.name},\n\n"
                    f"The registration deadline for '{event.job_title}' is approaching on "
                    f"{event.application_deadline.strftime('%d %b, %Y')}.\n\n"
                    f"You are eligible but haven't registered yet!\n\n"
                    f"Best regards,\nHackIE³ Event Team"
                )
                mail.send(msg)
                reminders_sent += 1
            except Exception as e:
                print(f"[ERROR] Reminder failed: {str(e)}")

    return f"Sent {reminders_sent} deadline reminders."


@shared_task(ignore_result=False)
def send_mass_email(subject, body, recipient_emails):
    sent = 0
    for email in recipient_emails:
        try:
            msg = Message(subject, recipients=[email])
            msg.body = body
            mail.send(msg)
            sent += 1
        except Exception as e:
            print(f"[ERROR] Mass email to {email} failed: {str(e)}")
    return f"Sent {sent}/{len(recipient_emails)} emails"


@shared_task(ignore_result=False)
def send_offer_letter(student_name, student_email, job_title, organizer_name):
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 50px; line-height: 1.6;">
        <div style="text-align: center; border-bottom: 3px solid #323232; padding-bottom: 20px;">
            <h1 style="margin: 0; color: #323232;">SELECTION LETTER</h1>
            <h3 style="margin: 5px 0; color: #2d8cf0;">{organizer_name}</h3>
        </div>

        <div style="margin-top: 50px;">
            <p><strong>Date:</strong> {datetime.now().strftime('%d %b, %Y')}</p>
            <p><strong>To,</strong><br>{student_name}</p>
        </div>

        <div style="margin-top: 30px;">
            <p>Dear {student_name},</p>
            <p>Congratulations! You have been selected for <strong>{job_title}</strong>
            organized by <strong>{organizer_name}</strong>.</p>
            <p>We look forward to your participation!</p>
        </div>

        <div style="margin-top: 60px;">
            <p>Sincerely,</p>
            <p><strong>{organizer_name}</strong></p>
        </div>

        <div style="margin-top: 100px; text-align: center; font-size: 10px; color: #666;">
            Auto-generated by HackIE&sup3; Event Management Portal
        </div>
    </body>
    </html>
    """

    filename = f"SelectionLetter_{student_name.replace(' ', '_')}.pdf"
    filepath = os.path.join(EXPORT_DIR, filename)

    try:
        from xhtml2pdf import pisa
        with open(filepath, "w+b") as result_file:
            pisa.CreatePDF(html_body, dest=result_file)

        msg = Message(f"Congratulations! Selection for {job_title}", recipients=[student_email])
        msg.body = f"Hi {student_name},\n\nCongratulations! You have been selected for {job_title}.\n\nPlease find the selection letter attached."

        with open(filepath, "rb") as f:
            msg.attach(filename, "application/pdf", f.read())

        mail.send(msg)
        return f"Selection letter sent to {student_email}"
    except Exception as e:
        print(f"[ERROR] Selection letter failed: {str(e)}")
        return f"Failed: {str(e)}"
