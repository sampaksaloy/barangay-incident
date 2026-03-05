from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Resident
    path('report/submit/', views.submit_report, name='submit_report'),
    path('report/my/', views.my_reports, name='my_reports'),
    path('report/<int:pk>/', views.report_detail, name='report_detail'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('profile/', views.profile_view, name='profile'),

    # Admin
    path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
    path('admin-panel/reports/<int:pk>/update/', views.admin_update_report, name='admin_update_report'),
    path('admin-panel/reports/<int:pk>/delete/', views.admin_delete_report, name='admin_delete_report'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/summary/', views.admin_reports_page, name='admin_reports_summary'),
]
