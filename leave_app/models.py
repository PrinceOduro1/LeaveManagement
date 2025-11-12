from django.db import models
from django.contrib.auth.models import User
from datetime import date

# Employee data
class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100, blank=True)
    annual_leave_days = models.IntegerField(default=30) # yearly allocation
    leave_days_taken = models.IntegerField(default=0)
    last_reset_year = models.IntegerField(default=date.today().year)

    @property
    def remaining_leave_days(self):
        return self.annual_leave_days - self.leave_days_taken
    
    @property
    def remaining_leave_days(self):
        """
        Auto-carry over unused days to the new year.
        Example: If 10 days remain in 2025, 2026 starts with 30 + 10 days.
        """
        current_year = date.today().year

        # Check if year changed
        if self.last_reset_year < current_year:
            # Calculate unused days from previous year
            unused_days = max(self.annual_leave_days - self.leave_days_taken, 0)

            # Add unused to new year allocation
            self.annual_leave_days = 30 + unused_days  # 30 is base yearly allocation

            # Reset counters for the new year
            self.leave_days_taken = 0
            self.last_reset_year = current_year
            self.save()

        return self.annual_leave_days - self.leave_days_taken

    def __str__(self):
        return self.user.get_full_name() or self.user.username


# Supervisor data
class Supervisor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.department})"


# Leave request
class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending Supervisor Approval'),
        ('Supervisor Approved', 'Approved by Supervisor'),
        ('Supervisor Rejected', 'Rejected by Supervisor'),
        ('HR Approved', 'Approved by HR'),
        ('HR Rejected', 'Rejected by HR'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    supervisor_comment = models.TextField(blank=True)
    hr_comment = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    date_requested = models.DateField(default=date.today)

    @property
    def leave_days_requested(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.status}"


#dialy report database entities
class DailyReport(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    summary = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.date}"