from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from datetime import date
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .models import Employee, Supervisor, LeaveRequest
from django.db import transaction
from django.contrib.auth.models import User
from .emails import send_leave_submission_email,send_supervisor_approval_email, send_supervisor_rejection_email,send_hr_decision_email
from .models import Employee, Supervisor, LeaveRequest,DailyReport

@login_required
# Employee Dashboard
def employee_dashboard(request):
    employee = get_object_or_404(Employee, user=request.user)
    leaves = LeaveRequest.objects.filter(employee=employee).order_by('-date_requested')
    return render(request, 'employee_dashboard.html', {'employee': employee, 'leaves': leaves})

@login_required
# Submit Leave Request
def submit_leave(request):
    employee = get_object_or_404(Employee, user=request.user)
    supervisor = get_object_or_404(Supervisor, department=employee.department)

    if request.method == 'POST':
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        reason = request.POST.get('reason')

        leave_request = LeaveRequest.objects.create(
            employee=employee,
            supervisor=supervisor,
            start_date=start,
            end_date=end,
            reason=reason,
            status='Pending'
        )
        send_leave_submission_email(leave_request)
        messages.success(request, 'Leave request submitted successfully.')
        return redirect('employee_dashboard')

    return render(request, 'submit_leave.html')

from datetime import date, datetime
from django.utils.dateparse import parse_date

@login_required
def supervisor_dashboard(request):
    supervisor = get_object_or_404(Supervisor, user=request.user)
    view_type = request.GET.get('from', 'leave')  # default view is 'leave'

    if view_type == 'daily':
        # 📅 Daily Report View
        selected_date = request.GET.get('date')
        filter_date = parse_date(selected_date) if selected_date else date.today()

        reports = DailyReport.objects.filter(
            supervisor=supervisor,
            date=filter_date
        ).order_by('-submitted_at')

        return render(
            request,
            'supervisor_daily.html',
            {'reports': reports, 'selected_date': filter_date}
        )

    else:
        # 📝 Leave Request View — filter by supervisor’s department
        requests = LeaveRequest.objects.filter(
            supervisor=supervisor, status='Pending'
        ).order_by('-date_requested')

        all_requests = LeaveRequest.objects.filter(
            employee__department=supervisor.department
        ).order_by('-date_requested')

        return render(
            request,
            'supervisor_dashboard.html',
            {'requests': requests, 'all_requests': all_requests}
        )



@login_required
# Supervisor Approve/Reject
def supervisor_approve(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('comment', '')

        if action == 'approve':
            leave.status = 'Supervisor Approved'
            send_supervisor_approval_email(leave)
        elif action == 'reject':
            leave.status = 'Supervisor Rejected'
            send_supervisor_rejection_email(leave)

        leave.supervisor_comment = comment
        leave.save()
        messages.success(request, f'Leave request {action}d successfully.')
    return redirect('supervisor_dashboard')

from django.http import HttpResponseForbidden

@login_required
def hr_dashboard(request):
    # Check if logged-in user is staff and belongs to HR department
    if not request.user.is_staff:
        messages.error(request, "Access denied. Only HR staff can view this page.")
        return redirect('login')

    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, "Access denied. You are not registered as an HR staff.")
        return redirect('login')

    if employee.department != 'Human Resource & Administration':
        messages.error(request, "Access denied. You are not in the HR department.")
        return redirect('login')

    # ✅ Passed all checks: show HR dashboard
    requests = LeaveRequest.objects.filter(status='Supervisor Approved').order_by('-date_requested')
    return render(request, 'hr_dashboard.html', {'requests': requests})


# HR Approve/Reject
def hr_approve(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('comment', '')

        if action == 'approve':
            leave.status = 'HR Approved'
            emp = leave.employee
            emp.leave_days_taken += leave.leave_days_requested
            emp.save()
        else:
            leave.status = 'HR Rejected'

        leave.hr_comment = comment
        leave.save()
        send_hr_decision_email(leave)
        messages.success(request, f'Leave request {action}d successfully.')
    return redirect('hr_dashboard')


# HR Export PDF
def export_leave_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="approved_leave_requests.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    y = 800
    p.setFont("Helvetica", 12)
    p.drawString(200, y, "HR Approved Leave Requests")
    y -= 30

    approved_leaves = LeaveRequest.objects.filter(status='HR Approved').order_by('-date_requested')
    for leave in approved_leaves:
        p.drawString(100, y, f"{leave.employee.user.get_full_name()} ({leave.employee.department}) - {leave.start_date} to {leave.end_date} ({leave.leave_days_requested} days)")
        y -= 20
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 12)
            y = 800

    p.save()
    return response


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            # Redirect based on role
            if hasattr(user, 'employee'):
                return redirect('landing')
            elif hasattr(user, 'supervisor'):
                return redirect('landing')
            else:
                return redirect('landing')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('employeeid')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        department = request.POST.get('department')
        position = request.POST.get('position')

        # Prevent duplicate usernames
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('signup')

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

            # Create Employee profile automatically
            Employee.objects.create(
                user=user,
                department=department,
                position=position,
            )

        messages.success(request, "Account created successfully! You can now log in.")
        return redirect('login')

    return render(request, 'signup.html')

def landing(request):
    return render(request, 'landing.html')

@login_required
def submit_daily_report(request):
    employee = get_object_or_404(Employee, user=request.user)
    supervisor = Supervisor.objects.filter(department=employee.department).first()

    if request.method == 'POST':
        summary = request.POST.get('summary')

        report = DailyReport.objects.create(
            employee=employee,
            supervisor=supervisor,
            summary=summary,
        )

        messages.success(request, 'Daily report submitted successfully')
        return redirect('landing')

    return render(request, 'daily_report.html')