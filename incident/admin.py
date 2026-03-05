from django.contrib import admin
from .models import User, IncidentReport, IncidentCategory, ReportUpdate, Notification

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'full_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']

@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ['report_number', 'title', 'reporter', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority']

@admin.register(IncidentCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color']

admin.site.register(ReportUpdate)
admin.site.register(Notification)
