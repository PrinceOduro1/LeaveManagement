from django.core.mail import send_mail
from django.conf import settings


def send_leave_submission_email(leave_request):
    """Notify supervisor when employee submits a leave request."""
    subject = f"New Leave Request from {leave_request.employee.user.get_full_name()}"
    message = (
        f"Dear {leave_request.supervisor.user.get_full_name()},\n\n"
        f"{leave_request.employee.user.get_full_name()} has submitted a leave request.\n\n"
        f"📅 Period: {leave_request.start_date} to {leave_request.end_date}\n"
        f"📝 Reason: {leave_request.reason}\n\n"
        "Please log in to the system to review and approve or reject this request.\n\n"
        "Thank you"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [leave_request.supervisor.user.email])


def send_supervisor_approval_email(leave_request):
    """Notify HR when supervisor approves a leave."""
    if not hasattr(leave_request, "employee") or not leave_request.employee:
        return

    # Get all employees with 'HR' in their position field
    hr_emails = [
        emp.user.email
        for emp in leave_request.employee.__class__.objects.filter(position__icontains="HR")
        if emp.user.email
    ]
    if not hr_emails:
        return

    subject = f"Supervisor Approved Leave for {leave_request.employee.user.get_full_name()}"
    message = (
        f"Dear HR Team,\n\n"
        f"The supervisor {leave_request.supervisor.user.get_full_name()} has approved a leave request for "
        f"{leave_request.employee.user.get_full_name()}.\n\n"
        f"📅 Period: {leave_request.start_date} to {leave_request.end_date}\n"
        f"📝 Reason: {leave_request.reason}\n\n"
        "Please log in to complete the final HR review.\n\n"
        "Thank you,\nSystem Notification"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, hr_emails)


def send_supervisor_rejection_email(leave_request):
    """Notify employee when supervisor rejects a leave."""
    subject = "Leave Request Rejected"
    message = (
        f"Dear {leave_request.employee.user.get_full_name()},\n\n"
        f"Your leave request from {leave_request.start_date} to {leave_request.end_date} "
        f"has been rejected by your supervisor, {leave_request.supervisor.user.get_full_name()}.\n\n"
        "Please contact your supervisor for more details.\n\n"
        "Best regards,\nHR Department"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [leave_request.employee.user.email])


def send_hr_decision_email(leave_request):
    """Notify employee when HR approves or rejects."""
    # Check if employee has an email before sending
    if not leave_request.employee.user.email:
        print(f"⚠️ No email found for {leave_request.employee.user.username}, skipping HR notification.")
        return

    status = leave_request.status.upper()
    subject = f"Leave Request {status} by HR"
    message = (
        f"Dear {leave_request.employee.user.get_full_name()},\n\n"
        f"Your leave request from {leave_request.start_date} to {leave_request.end_date} "
        f"has been {leave_request.status.lower()} by HR.\n\n"
        "Thank you."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [leave_request.employee.user.email])

