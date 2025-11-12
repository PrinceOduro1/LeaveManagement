from django.contrib import admin
from .models import Employee, Supervisor, LeaveRequest
from django.contrib import messages

# --- Employee Admin ---
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'department',
        'position',
        'annual_leave_days',
        'leave_days_taken',
        'remaining_leave_days_display'
    )
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'department', 'position')
    list_filter = ('department',)
    
    # ✅ Register the reset action here
    actions = ['reset_leave_balances']

    @admin.action(description="🔄 Reset selected employees' leave balances to standard allocation")
    def reset_leave_balances(self, request, queryset):
        for emp in queryset:
            standard_allocation = 30  # Standard yearly allocation
            emp.annual_leave_days = standard_allocation
            emp.leave_days_taken = 0
            emp.save()
        messages.success(request, "✅ Selected employees' leave balances have been reset to the standard allocation.")

    def remaining_leave_days_display(self, obj):
        return obj.remaining_leave_days
    remaining_leave_days_display.short_description = 'Remaining Days'


# --- Supervisor Admin ---
@admin.register(Supervisor)
class SupervisorAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'department')


# --- Leave Request Admin ---
@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'supervisor', 'start_date', 'end_date', 'leave_days_requested',
        'status', 'date_requested'
    )
    search_fields = (
        'employee__user__first_name', 'employee__user__last_name',
        'supervisor__user__first_name', 'supervisor__user__last_name'
    )
    list_filter = ('status', 'supervisor__department', 'date_requested')
    readonly_fields = ('leave_days_requested',)

    def leave_days_requested(self, obj):
        return obj.leave_days_requested
    leave_days_requested.short_description = 'Days Requested'
