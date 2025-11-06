import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

def send_welcome_email(to_email, name):
    """Send a professional, styled welcome email to a newly registered user."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_host, smtp_port, smtp_user, smtp_password]):
        print("SMTP configuration missing. Skipping email send.")
        return False

    plain_text = f"""Welcome {name},

Thank you for registering with Smart Health Hub. Your profile for {name} has been created successfully. Please log in to manage your profile and access our services.

Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Smart Health Hub</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; color: #333333; background-color: #F4F4F4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F4F4F4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #3d3693; padding: 20px; text-align: center;">
                            <h1 style="color: #FFFFFF; font-size: 24px; margin: 10px 0;">Welcome to Smart Health Hub</h1>
                        </td>
                    </tr>
                    <!-- Body -->
                    <tr>
                        <td style="padding: 30px;">
                            <h2 style="font-size: 20px; color: #3d3693; margin-top: 0;">Welcome, {name}!</h2>
                            <p style="font-size: 16px; line-height: 1.5;">
                                Thank you for registering with Smart Health Hub. Your profile for {name} has been created successfully.
                            </p>
                            <p style="font-size: 16px; line-height: 1.5;">
                                You can now log in to manage your profile, schedule appointments, and access our healthcare services.
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="http://localhost:8501" style="background-color: #3d3693; color: #FFFFFF; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-size: 16px; display: inline-block;">Log In Now</a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #F4F4F4; padding: 20px; text-align: center; font-size: 14px; color: #666666;">
                            <p style="margin: 0;">Smart Health Hub</p>
                            <p style="margin: 5px 0;">Islamabad, Pakistan</p>
                            <p style="margin: 5px 0;"><a href="mailto:support@smarthealthhub.com" style="color: #3d3693; text-decoration: none;">support@smarthealthhub.com</a></p>
                            <p style="margin: 10px 0;"><a href="#" style="color: #3d3693; text-decoration: none;">Unsubscribe</a></p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Welcome to Smart Health Hub"
    msg["From"] = smtp_user
    msg["To"] = to_email

    part1 = MIMEText(plain_text, "plain")
    part2 = MIMEText(html_content, "html")
    msg.attach(part1)
    msg.attach(part2)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"Welcome email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False
    
def send_otp_email(to_email: str, name: str, otp: str):
    """
    Send a verification OTP to the newly registered user.
    OTP is displayed as a styled header/paragraph with blue background.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_host, smtp_port, smtp_user, smtp_password]):
        print("SMTP configuration missing. Skipping OTP email send.")
        return False

    # Plain text fallback
    plain_text = f"""Hello {name},

Your verification code (OTP) is: {otp}

Enter this code to verify your account.

Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""

    # HTML styled OTP
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Health Hub OTP Verification</title>
</head>
<body style="margin:0; padding:0; font-family: Arial, Helvetica, sans-serif; background-color:#F4F4F4; color:#333;">
    <table width="100%" cellpadding="0" cellspacing="0" style="padding:20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color:#FFFFFF; border-radius:8px; padding:30px; box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="text-align:center; padding-bottom:20px;">
                            <h1 style="color:#3d3693; margin:0;">OTP Verification</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:20px; font-size:16px; line-height:1.5;">
                            Hello {name},<br><br>
                            Thank you for registering with Smart Health Hub. To verify your account, please use the following One-Time Password (OTP):
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align:center; padding:20px;">
                            <h2 style="display:inline-block; background-color:#3d3693; color:#FFFFFF; padding:15px 30px; border-radius:5px; font-size:24px; letter-spacing:2px;">
                                {otp}
                            </h2>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:20px; font-size:14px; color:#666; text-align:center;">
                            Smart Health Hub Team<br>
                            Islamabad, Pakistan<br>
                            <a href="mailto:support@smarthealthhub.com" style="color:#3d3693; text-decoration:none;">support@smarthealthhub.com</a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Smart Health Hub - OTP Verification"
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"OTP email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending OTP email to {to_email}: {e}")
        return False
    
    
def send_appointment_confirmation(patient_email, doctor_email, patient_name, patient_age, patient_gender, patient_phone, doctor_name, appointment_date, time_slot, reference_number):
    """Send appointment confirmation email to patient and notification to doctor without admit card attachment."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_host, smtp_port, smtp_user, smtp_password]):
        print("SMTP configuration missing. Skipping email send.")
        return False

    if patient_email:
        patient_plain_text = f"""Dear {patient_name},

Your appointment has been successfully registered with the following details:
- Reference Number: {reference_number}
- Patient Name: {patient_name}
- Age: {patient_age}
- Gender: {patient_gender}
- Phone Number: {patient_phone}
- Doctor Name: {doctor_name}
- Appointment Date: {appointment_date.strftime('%Y-%m-%d')}
- Time Slot: {time_slot}

Please download your admit card from the Smart Health Hub portal and bring it along with a valid ID to your appointment.

Thank you for using Smart Health Hub.
Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""

        patient_html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Appointment Confirmation</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; color: #333333; background-color: #F4F4F4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F4F4F4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="background-color: #3d3693; padding: 20px; text-align: center;">
                            <h1 style="color: #FFFFFF; font-size: 24px; margin: 10px 0;">Appointment Confirmation</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px;">
                            <h2 style="font-size: 20px; color: #3d3693; margin-top: 0;">Dear {patient_name},</h2>
                            <p style="font-size: 16px; line-height: 1.5;">
                                Your appointment has been successfully registered with the following details:
                            </p>
                            <table width="100%" cellpadding="5" style="font-size: 16px;">
                                <tr><td><strong>Reference Number:</strong></td><td>{reference_number}</td></tr>
                                <tr><td><strong>Patient Name:</strong></td><td>{patient_name}</td></tr>
                                <tr><td><strong>Age:</strong></td><td>{patient_age}</td></tr>
                                <tr><td><strong>Gender:</strong></td><td>{patient_gender}</td></tr>
                                <tr><td><strong>Phone Number:</strong></td><td>{patient_phone}</td></tr>
                                <tr><td><strong>Doctor Name:</strong></td><td>{doctor_name}</td></tr>
                                <tr><td><strong>Appointment Date:</strong></td><td>{appointment_date.strftime('%Y-%m-%d')}</td></tr>
                                <tr><td><strong>Time Slot:</strong></td><td>{time_slot}</td></tr>
                            </table>
                            <p style="font-size: 16px; line-height: 1.5;">
                                Please download your admit card from the Smart Health Hub portal and bring it along with a valid ID to your appointment.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #F4F4F4; padding: 20px; text-align: center; font-size: 14px; color: #666666;">
                            <p style="margin: 0;">Smart Health Hub</p>
                            <p style="margin: 5px 0;">Islamabad, Pakistan</p>
                            <p style="margin: 5px 0;"><a href="mailto:support@smarthealthhub.com" style="color: #3d3693; text-decoration: none;">support@smarthealthhub.com</a></p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        msg_patient = MIMEMultipart("alternative")
        msg_patient["Subject"] = "Your Appointment Confirmation - Smart Health Hub"
        msg_patient["From"] = smtp_user
        msg_patient["To"] = patient_email

        part1 = MIMEText(patient_plain_text, "plain")
        part2 = MIMEText(patient_html_content, "html")
        msg_patient.attach(part1)
        msg_patient.attach(part2)

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, patient_email, msg_patient.as_string())
            print(f"Appointment confirmation email sent to patient {patient_email}")
        except Exception as e:
            print(f"Error sending email to {patient_email}: {e}")
            return False

    if doctor_email:
        doctor_plain_text = f"""Dear {doctor_name},

A new appointment has been scheduled with the following details:
- Reference Number: {reference_number}
- Patient Name: {patient_name}
- Age: {patient_age}
- Gender: {patient_gender}
- Phone Number: {patient_phone}
- Appointment Date: {appointment_date.strftime('%Y-%m-%d')}
- Time Slot: {time_slot}

Please prepare accordingly and contact the patient if needed.

Thank you for your service with Smart Health Hub.
Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""

        doctor_html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Appointment Notification</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; color: #333333; background-color: #F4F4F4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F4F4F4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="background-color: #3d3693; padding: 20px; text-align: center;">
                            <h1 style="color: #FFFFFF; font-size: 24px; margin: 10px 0;">New Appointment Notification</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px;">
                            <h2 style="font-size: 20px; color: #3d3693; margin-top: 0;">Dear {doctor_name},</h2>
                            <p style="font-size: 16px; line-height: 1.5;">
                                A new appointment has been scheduled with the following details:
                            </p>
                            <table width="100%" cellpadding="5" style="font-size: 16px;">
                                <tr><td><strong>Reference Number:</strong></td><td>{reference_number}</td></tr>
                                <tr><td><strong>Patient Name:</strong></td><td>{patient_name}</td></tr>
                                <tr><td><strong>Age:</strong></td><td>{patient_age}</td></tr>
                                <tr><td><strong>Gender:</strong></td><td>{patient_gender}</td></tr>
                                <tr><td><strong>Phone Number:</strong></td><td>{patient_phone}</td></tr>
                                <tr><td><strong>Appointment Date:</strong></td><td>{appointment_date.strftime('%Y-%m-%d')}</td></tr>
                                <tr><td><strong>Time Slot:</strong></td><td>{time_slot}</td></tr>
                            </table>
                            <p style="font-size: 16px; line-height: 1.5;">
                                Please prepare accordingly and contact the patient if needed.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #F4F4F4; padding: 20px; text-align: center; font-size: 14px; color: #666666;">
                            <p style="margin: 0;">Smart Health Hub</p>
                            <p style="margin: 5px 0;">Islamabad, Pakistan</p>
                            <p style="margin: 5px 0;"><a href="mailto:support@smarthealthhub.com" style="color: #3d3693; text-decoration: none;">support@smarthealthhub.com</a></p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        msg_doctor = MIMEMultipart("alternative")
        msg_doctor["Subject"] = "New Appointment Notification - Smart Health Hub"
        msg_doctor["From"] = smtp_user
        msg_doctor["To"] = doctor_email

        part1 = MIMEText(doctor_plain_text, "plain")
        part2 = MIMEText(doctor_html_content, "html")
        msg_doctor.attach(part1)
        msg_doctor.attach(part2)

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, doctor_email, msg_doctor.as_string())
            print(f"Appointment notification email sent to doctor {doctor_email}")
        except Exception as e:
            print(f"Error sending email to {doctor_email}: {e}")
            return False

    return True

def send_cancellation_email(doctor_email, appointment_id):
    plain_text = f"""Dear Doctor,

An appointment (ID: {appointment_id}) has been cancelled by the patient.

Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Appointment Cancellation Notification</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; color: #333333; background-color: #F4F4F4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F4F4F4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="background-color: #3d3693; padding: 20px; text-align: center;">
                            <h1 style="color: #FFFFFF; font-size: 24px; margin: 10px 0;">Appointment Cancellation Notification</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px;">
                            <p style="font-size: 16px; line-height: 1.5;">
                                Dear Doctor,
                            </p>
                            <p style="font-size: 16px; line-height: 1.5;">
                                An appointment (ID: {appointment_id}) has been cancelled by the patient.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #F4F4F4; padding: 20px; text-align: center; font-size: 14px; color: #666666;">
                            <p style="margin: 0;">Smart Health Hub</p>
                            <p style="margin: 5px 0;">Islamabad, Pakistan</p>
                            <p style="margin: 5px 0;"><a href="mailto:support@smarthealthhub.com" style="color: #3d3693; text-decoration: none;">support@smarthealthhub.com</a></p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Appointment Cancellation Notification"
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = doctor_email
    part1 = MIMEText(plain_text, "plain")
    part2 = MIMEText(html_content, "html")
    msg.attach(part1)
    msg.attach(part2)

    try:
        with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", 587))) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            server.sendmail(os.getenv("SMTP_USER"), doctor_email, msg.as_string())
    except Exception as e:
        return False
    
    return True

def send_reschedule_email(doctor_email, appointment_id, new_date, new_time):
    plain_text = f"""Dear Doctor,

An appointment (ID: {appointment_id}) has been rescheduled to {new_date.strftime('%Y-%m-%d')} at {new_time}.

Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Appointment Reschedule Notification</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; color: #333333; background-color: #F4F4F4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F4F4F4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="background-color: #3d3693; padding: 20px; text-align: center;">
                            <h1 style="color: #FFFFFF; font-size: 24px; margin: 10px 0;">Appointment Reschedule Notification</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px;">
                            <p style="font-size: 16px; line-height: 1.5;">
                                Dear Doctor,
                            </p>
                            <p style="font-size: 16px; line-height: 1.5;">
                                An appointment (ID: {appointment_id}) has been rescheduled to {new_date.strftime('%Y-%m-%d')} at {new_time}.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #F4F4F4; padding: 20px; text-align: center; font-size: 14px; color: #666666;">
                            <p style="margin: 0;">Smart Health Hub</p>
                            <p style="margin: 5px 0;">Islamabad, Pakistan</p>
                            <p style="margin: 5px 0;"><a href="mailto:support@smarthealthhub.com" style="color: #3d3693; text-decoration: none;">support@smarthealthhub.com</a></p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Appointment Reschedule Notification"
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = doctor_email
    part1 = MIMEText(plain_text, "plain")
    part2 = MIMEText(html_content, "html")
    msg.attach(part1)
    msg.attach(part2)

    try:
        with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", 587))) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            server.sendmail(os.getenv("SMTP_USER"), doctor_email, msg.as_string())
    except Exception as e:
        return False
    
    return True

def send_cancellation_email_doctor(patient_email: str, reference_number: str):
    """
    Send a nicely formatted HTML & plain-text email to the patient
    notifying them that their appointment has been cancelled.
    """

    # --- Plain text version ---
    plain_text = f"""Dear Patient,

Your appointment with Reference Number {reference_number} has been cancelled by the doctor.

Best regards,
Smart Health Hub Team
Contact: support@smarthealthhub.com
"""

    # --- HTML version ---
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Appointment Cancellation</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; color: #333333; background-color: #F4F4F4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F4F4F4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="background-color: #3d3693; padding: 20px; text-align: center;">
                            <h1 style="color: #FFFFFF; font-size: 24px; margin: 10px 0;">Appointment Cancellation</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px;">
                            <p style="font-size: 16px; line-height: 1.5;">Dear Patient,</p>
                            <p style="font-size: 16px; line-height: 1.5;">
                                Your appointment with Reference Number <strong>{reference_number}</strong> has been cancelled by the doctor.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #F4F4F4; padding: 20px; text-align: center; font-size: 14px; color: #666666;">
                            <p style="margin: 0;">Smart Health Hub</p>
                            <p style="margin: 5px 0;">Islamabad, Pakistan</p>
                            <p style="margin: 5px 0;">
                                <a href="mailto:support@smarthealthhub.com" style="color: #3d3693; text-decoration: none;">support@smarthealthhub.com</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    # --- Create MIME message ---
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Appointment Cancellation Notification"
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = patient_email
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    # --- Send via SMTP ---
    with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", 587))) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
        server.sendmail(os.getenv("SMTP_USER"), patient_email, msg.as_string())