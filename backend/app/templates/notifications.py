"""
Notification message templates
"""
from typing import Dict, Any
from datetime import datetime


def format_phone_number(phone: str) -> str:
    """Format phone number to E.164 format"""
    if not phone:
        return ""
    
    # Remove spaces, dashes, parentheses
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Add + if missing
    if not phone.startswith("+"):
        # Assume Lesotho if no country code (+266)
        if len(phone) == 8:
            phone = f"+266{phone}"
        else:
            phone = f"+{phone}"
    
    return phone


class NotificationTemplates:
    """SMS and Email templates for different events"""
    
    @staticmethod
    def check_in_success(employee_name: str, time: str) -> Dict[str, str]:
        """Template for successful check-in"""
        return {
            "sms": f"Check-in successful! Welcome {employee_name}. Time: {time}",
            "email_subject": "Check-in Confirmation",
            "email_body": f"Dear {employee_name},\n\nYour check-in has been recorded successfully at {time}.\n\nThank you!",
            "email_html": f"""
                <h2>Check-in Confirmation</h2>
                <p>Dear {employee_name},</p>
                <p>Your check-in has been recorded successfully at <strong>{time}</strong>.</p>
                <p>Thank you!</p>
            """
        }
    
    @staticmethod
    def check_out_success(employee_name: str, time: str, hours_worked: float) -> Dict[str, str]:
        """Template for successful check-out"""
        return {
            "sms": f"Check-out recorded! {employee_name}, you worked {hours_worked:.1f} hours. Time: {time}",
            "email_subject": "Check-out Confirmation",
            "email_body": f"Dear {employee_name},\n\nYour check-out has been recorded at {time}.\nHours worked: {hours_worked:.1f}\n\nThank you!",
            "email_html": f"""
                <h2>Check-out Confirmation</h2>
                <p>Dear {employee_name},</p>
                <p>Your check-out has been recorded at <strong>{time}</strong>.</p>
                <p>Hours worked: <strong>{hours_worked:.1f} hours</strong></p>
                <p>Thank you!</p>
            """
        }
    
    @staticmethod
    def geofence_violation(employee_name: str, distance: float) -> Dict[str, str]:
        """Template for geofence violation alert"""
        return {
            "sms": f"ALERT: {employee_name} checked in {distance:.0f}m outside geofence. Supervisor notified.",
            "email_subject": "Geofence Violation Alert",
            "email_body": f"Alert: {employee_name} attempted check-in {distance:.0f} meters outside the designated geofence area.",
            "email_html": f"""
                <h2 style="color: red;">Geofence Violation Alert</h2>
                <p><strong>{employee_name}</strong> attempted check-in <strong>{distance:.0f} meters</strong> outside the designated geofence area.</p>
                <p>Please review the attendance record.</p>
            """
        }
    
    @staticmethod
    def new_qr_code(employee_name: str, employee_number: str) -> Dict[str, str]:
        """Template for new QR code generation"""
        return {
            "sms": f"New QR code generated for {employee_name} ({employee_number}). Check your email for details.",
            "email_subject": "New QR Code Generated",
            "email_body": f"Dear {employee_name},\n\nA new QR code has been generated for your attendance tracking.\nEmployee Number: {employee_number}\n\nPlease download it from the system.",
            "email_html": f"""
                <h2>New QR Code Generated</h2>
                <p>Dear {employee_name},</p>
                <p>A new QR code has been generated for your attendance tracking.</p>
                <p>Employee Number: <strong>{employee_number}</strong></p>
                <p>Please log in to the system to download your QR code.</p>
            """
        }
    
    @staticmethod
    def daily_summary(department: str, total: int, present: int, absent: int) -> Dict[str, str]:
        """Template for daily attendance summary"""
        attendance_rate = (present / total * 100) if total > 0 else 0
        
        return {
            "sms": f"{department} Summary: {present}/{total} present ({attendance_rate:.0f}%). {absent} absent.",
            "email_subject": f"Daily Attendance Summary - {department}",
            "email_body": f"""Daily Attendance Summary for {department}

Total Employees: {total}
Present: {present}
Absent: {absent}
Attendance Rate: {attendance_rate:.1f}%

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}""",
            "email_html": f"""
                <h2>Daily Attendance Summary - {department}</h2>
                <table border="1" cellpadding="10">
                    <tr><td><strong>Total Employees</strong></td><td>{total}</td></tr>
                    <tr><td><strong>Present</strong></td><td style="color: green;">{present}</td></tr>
                    <tr><td><strong>Absent</strong></td><td style="color: red;">{absent}</td></tr>
                    <tr><td><strong>Attendance Rate</strong></td><td><strong>{attendance_rate:.1f}%</strong></td></tr>
                </table>
                <p><small>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</small></p>
            """
        }


templates = NotificationTemplates()
