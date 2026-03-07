from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [('admin', 'Admin'), ('resident', 'Resident')]
    username = models.CharField(max_length=80, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='resident')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    login_count = models.PositiveIntegerField(default=0) # Add this line

    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.full_name

    def is_admin(self):
        return self.role == 'admin'


class IncidentCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='bi-exclamation-triangle')
    color = models.CharField(max_length=20, default='danger')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Incident Categories'


class IncidentReport(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    report_number = models.CharField(max_length=30, unique=True)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(IncidentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    photo = models.ImageField(upload_to='incidents/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_number} — {self.title}"

    def get_status_color(self):
        return {'pending': 'warning', 'in_progress': 'info', 'resolved': 'success', 'dismissed': 'secondary'}.get(self.status, 'secondary')

    def get_priority_color(self):
        return {'low': 'success', 'medium': 'info', 'high': 'warning', 'critical': 'danger'}.get(self.priority, 'secondary')


class ReportUpdate(models.Model):
    report = models.ForeignKey(IncidentReport, on_delete=models.CASCADE, related_name='updates')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    report = models.ForeignKey(IncidentReport, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
