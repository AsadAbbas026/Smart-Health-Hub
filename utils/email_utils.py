import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "aarizy.2k@gmail.com")  # verified sender
FROM_NAME = "Smart Health Hub"
REPLY_TO_EMAIL = os.getenv("REPLY_TO_EMAIL", FROM_EMAIL)

def send_email(to_email, subject, html_content, plain_text):
    """Generic function to send email via SendGrid."""
    try:
        message = Mail(
            from_email=Email(FROM_EMAIL, FROM_NAME),
            to_emails=To(to_email),
            subject=subject,
            plain_text_content=plain_text,
            html_content=html_content,
        )
        message.reply_to = Email(REPLY_TO_EMAIL, FROM_NAME)
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent to {to_email}, Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False


def send_welcome_email(to_email, name):
    subject = "Welcome to Smart Health Hub"
    plain_text = f"""Welcome {name},

Thank you for registering with Smart Health Hub. Your profile has been created successfully.

Log in to manage your profile and access our services.

Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""
    html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial; background:#F4F4F4; color:#333;">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:20px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff; border-radius:8px; padding:30px;">
<tr><td style="text-align:center; background:#3d3693; padding:20px;">
<h1 style="color:#fff;">Welcome to Smart Health Hub</h1>
</td></tr>
<tr><td style="padding:20px;">
<h2 style="color:#3d3693;">Welcome, {name}!</h2>
<p>Thank you for registering. Your profile has been created successfully.</p>
<p><a href="http://localhost:8501" style="background:#3d3693;color:#fff;padding:12px 24px;text-decoration:none;border-radius:4px;">Log In Now</a></p>
</td></tr>
<tr><td style="text-align:center; padding:20px; color:#666;">
<p>Smart Health Hub | Islamabad, Pakistan</p>
<p><a href="mailto:support@smarthealthhub.com" style="color:#3d3693;">support@smarthealthhub.com</a></p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""
    return send_email(to_email, subject, html_content, plain_text)


def send_otp_email(to_email, name, otp):
    subject = "Smart Health Hub - OTP Verification"
    plain_text = f"""Hello {name},

Your verification code (OTP) is: {otp}

Enter this code to verify your account.

Best regards,
Smart Health Hub Team
"""
    html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial; background:#F4F4F4; color:#333;">
<table width="100%" cellpadding="20">
<tr><td align="center">
<table width="600" style="background:#fff; border-radius:8px; padding:30px;">
<tr><td style="text-align:center; padding-bottom:20px;">
<h1 style="color:#3d3693;">OTP Verification</h1>
</td></tr>
<tr><td style="text-align:center; padding:20px; font-size:16px;">
Hello {name},<br><br>
Thank you for registering. Use the following One-Time Password (OTP):
</td></tr>
<tr><td style="text-align:center; padding:20px;">
<h2 style="background:#3d3693;color:#fff;padding:15px 30px;border-radius:5px;">{otp}</h2>
</td></tr>
<tr><td style="text-align:center; padding:20px; color:#666;">
Smart Health Hub Team<br>Islamabad, Pakistan<br>
<a href="mailto:support@smarthealthhub.com" style="color:#3d3693;">support@smarthealthhub.com</a>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""
    return send_email(to_email, subject, html_content, plain_text)


def send_appointment_confirmation(patient_email, doctor_email, patient_name, patient_age, patient_gender, patient_phone, doctor_name, appointment_date, time_slot, reference_number):
    """Send appointment confirmation to patient and notification to doctor via SendGrid."""
    
    # --- Patient Email ---
    if patient_email:
        subject_patient = "Your Appointment Confirmation - Smart Health Hub"
        plain_text_patient = f"""Dear {patient_name},

Your appointment has been successfully registered with the following details:
- Reference Number: {reference_number}
- Patient Name: {patient_name}
- Age: {patient_age}
- Gender: {patient_gender}
- Phone Number: {patient_phone}
- Doctor Name: {doctor_name}
- Appointment Date: {appointment_date.strftime('%Y-%m-%d')}
- Time Slot: {time_slot}

Please bring a valid ID to your appointment.

Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""
        html_content_patient = f"""<html><body style="font-family: Arial; background:#F4F4F4; color:#333;">
<table width="100%" cellpadding="20"><tr><td align="center">
<table width="600" style="background:#fff; border-radius:8px; padding:30px;">
<tr><td style="background:#3d3693; padding:20px; text-align:center;">
<h1 style="color:#fff;">Appointment Confirmation</h1>
</td></tr>
<tr><td style="padding:20px;">
<p>Dear {patient_name},</p>
<p>Your appointment has been successfully registered with the following details:</p>
<ul>
<li><strong>Reference Number:</strong> {reference_number}</li>
<li><strong>Patient Name:</strong> {patient_name}</li>
<li><strong>Age:</strong> {patient_age}</li>
<li><strong>Gender:</strong> {patient_gender}</li>
<li><strong>Phone Number:</strong> {patient_phone}</li>
<li><strong>Doctor Name:</strong> {doctor_name}</li>
<li><strong>Appointment Date:</strong> {appointment_date.strftime('%Y-%m-%d')}</li>
<li><strong>Time Slot:</strong> {time_slot}</li>
</ul>
<p>Please bring a valid ID to your appointment.</p>
</td></tr>
<tr><td style="text-align:center; padding:20px; color:#666;">
Smart Health Hub | Islamabad, Pakistan<br>
<a href="mailto:support@smarthealthhub.com" style="color:#3d3693;">support@smarthealthhub.com</a>
</td></tr>
</table></td></tr></table></body></html>"""
        send_email(patient_email, subject_patient, html_content_patient, plain_text_patient)

    # --- Doctor Email ---
    if doctor_email:
        subject_doctor = "New Appointment Notification - Smart Health Hub"
        plain_text_doctor = f"""Dear {doctor_name},

A new appointment has been scheduled with the following details:
- Reference Number: {reference_number}
- Patient Name: {patient_name}
- Age: {patient_age}
- Gender: {patient_gender}
- Phone Number: {patient_phone}
- Appointment Date: {appointment_date.strftime('%Y-%m-%d')}
- Time Slot: {time_slot}

Please prepare accordingly and contact the patient if needed.

Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""
        html_content_doctor = f"""<html><body style="font-family: Arial; background:#F4F4F4; color:#333;">
<table width="100%" cellpadding="20"><tr><td align="center">
<table width="600" style="background:#fff; border-radius:8px; padding:30px;">
<tr><td style="background:#3d3693; padding:20px; text-align:center;">
<h1 style="color:#fff;">New Appointment Notification</h1>
</td></tr>
<tr><td style="padding:20px;">
<p>Dear {doctor_name},</p>
<p>A new appointment has been scheduled with the following details:</p>
<ul>
<li><strong>Reference Number:</strong> {reference_number}</li>
<li><strong>Patient Name:</strong> {patient_name}</li>
<li><strong>Age:</strong> {patient_age}</li>
<li><strong>Gender:</strong> {patient_gender}</li>
<li><strong>Phone Number:</strong> {patient_phone}</li>
<li><strong>Appointment Date:</strong> {appointment_date.strftime('%Y-%m-%d')}</li>
<li><strong>Time Slot:</strong> {time_slot}</li>
</ul>
<p>Please prepare accordingly and contact the patient if needed.</p>
</td></tr>
<tr><td style="text-align:center; padding:20px; color:#666;">
Smart Health Hub | Islamabad, Pakistan<br>
<a href="mailto:support@smarthealthhub.com" style="color:#3d3693;">support@smarthealthhub.com</a>
</td></tr>
</table></td></tr></table></body></html>"""
        send_email(doctor_email, subject_doctor, html_content_doctor, plain_text_doctor)

    return True

def send_cancellation_email_doctor(patient_email: str, reference_number: str):
    """Notify patient that doctor cancelled the appointment."""
    subject = "Appointment Cancellation Notification"
    plain_text = f"""Dear Patient,

Your appointment with Reference Number {reference_number} has been cancelled by the doctor.

Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""
    html_content = f"""<html><body style="font-family: Arial; background:#F4F4F4; color:#333;">
<table width="100%" cellpadding="20"><tr><td align="center">
<table width="600" style="background:#fff; border-radius:8px; padding:30px;">
<tr><td style="background:#3d3693; padding:20px; text-align:center;">
<h1 style="color:#fff;">Appointment Cancellation</h1>
</td></tr>
<tr><td style="padding:20px;">
<p>Dear Patient,</p>
<p>Your appointment with Reference Number <strong>{reference_number}</strong> has been cancelled by the doctor.</p>
</td></tr>
<tr><td style="text-align:center; padding:20px; color:#666;">
Smart Health Hub | Islamabad, Pakistan<br>
<a href="mailto:support@smarthealthhub.com" style="color:#3d3693;">support@smarthealthhub.com</a>
</td></tr>
</table></td></tr></table></body></html>"""
    return send_email(patient_email, subject, html_content, plain_text)


def send_cancellation_email(doctor_email: str, appointment_id: str):
    """Notify doctor that patient cancelled the appointment."""
    subject = "Appointment Cancellation Notification"
    plain_text = f"""Dear Doctor,

An appointment (ID: {appointment_id}) has been cancelled by the patient.

Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""
    html_content = f"""<html><body style="font-family: Arial; background:#F4F4F4; color:#333;">
<table width="100%" cellpadding="20"><tr><td align="center">
<table width="600" style="background:#fff; border-radius:8px; padding:30px;">
<tr><td style="background:#3d3693; padding:20px; text-align:center;">
<h1 style="color:#fff;">Appointment Cancellation Notification</h1>
</td></tr>
<tr><td style="padding:20px;">
<p>Dear Doctor,</p>
<p>An appointment (ID: {appointment_id}) has been cancelled by the patient.</p>
</td></tr>
<tr><td style="text-align:center; padding:20px; color:#666;">
Smart Health Hub | Islamabad, Pakistan<br>
<a href="mailto:support@smarthealthhub.com" style="color:#3d3693;">support@smarthealthhub.com</a>
</td></tr>
</table></td></tr></table></body></html>"""
    return send_email(doctor_email, subject, html_content, plain_text)


def send_reschedule_email(doctor_email: str, appointment_id: str, new_date, new_time):
    """Notify doctor that appointment has been rescheduled."""
    subject = "Appointment Reschedule Notification"
    plain_text = f"""Dear Doctor,

An appointment (ID: {appointment_id}) has been rescheduled to {new_date.strftime('%Y-%m-%d')} at {new_time}.

Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""
    html_content = f"""<html><body style="font-family: Arial; background:#F4F4F4; color:#333;">
<table width="100%" cellpadding="20"><tr><td align="center">
<table width="600" style="background:#fff; border-radius:8px; padding:30px;">
<tr><td style="background:#3d3693; padding:20px; text-align:center;">
<h1 style="color:#fff;">Appointment Reschedule Notification</h1>
</td></tr>
<tr><td style="padding:20px;">
<p>Dear Doctor,</p>
<p>An appointment (ID: {appointment_id}) has been rescheduled to <strong>{new_date.strftime('%Y-%m-%d')}</strong> at <strong>{new_time}</strong>.</p>
</td></tr>
<tr><td style="text-align:center; padding:20px; color:#666;">
Smart Health Hub | Islamabad, Pakistan<br>
<a href="mailto:support@smarthealthhub.com" style="color:#3d3693;">support@smarthealthhub.com</a>
</td></tr>
</table></td></tr></table></body></html>"""
    return send_email(doctor_email, subject, html_content, plain_text)
