from django.urls import path
from . import views

urlpatterns = [
    path('employee/', views.employee_dashboard, name='employee_dashboard'),
    path('submit-leave/', views.submit_leave, name='submit_leave'),
    path('supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/approve/<int:leave_id>/', views.supervisor_approve, name='supervisor_approve'),
    path('hr/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/approve/<int:leave_id>/', views.hr_approve, name='hr_approve'),
    path('hr/export-pdf/', views.export_leave_pdf, name='export_leave_pdf'),
    path('', views.login_view, name='login'),
    path('signup', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('index/', views.landing, name='landing'),
    path('report/', views.submit_daily_report, name='report'),
    path('submit-daily-report/', views.submit_daily_report, name='submit_daily_report'),

]
