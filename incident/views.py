from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from django.http import HttpResponse
from datetime import date, timedelta
import csv

from .models import User, IncidentReport, IncidentCategory, ReportUpdate, Notification
from .forms import LoginForm, RegisterForm, IncidentReportForm, AdminUpdateForm, ProfileForm


def generate_report_number():
    year = timezone.now().year
    month = timezone.now().month
    count = IncidentReport.objects.filter(created_at__year=year, created_at__month=month).count() + 1
    return f"INC-{year}{str(month).zfill(2)}-{str(count).zfill(4)}"


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.error(request, 'Admin access required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── AUTH ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        # Track if this is first login or returning
        user.last_login_count = getattr(user, 'login_count', 0) + 1
        # Use session to track
        request.session['login_count'] = request.session.get('login_count', 0) + 1
        return redirect('dashboard')
    return render(request, 'incident/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        # 1. Assign the default role so the login page recognizes them
        user.role = 'resident' 
        user.save()
        
        # 2. Log them in automatically
        login(request, user)
        
        # 3. Redirect straight to dashboard instead of a static success page
        messages.success(request, f'Welcome, {user.full_name}! Your account has been created.')
        return redirect('dashboard')
        
    return render(request, 'incident/register.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    if request.user.role == 'admin':
        return admin_dashboard(request)
    return resident_dashboard(request)


def resident_dashboard(request):
    reports = IncidentReport.objects.filter(reporter=request.user)
    total = reports.count()
    pending = reports.filter(status='pending').count()
    in_progress = reports.filter(status='in_progress').count()
    resolved = reports.filter(status='resolved').count()
    recent = reports[:5]
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    login_count = request.session.get('login_count', 1)
    is_first_login = login_count <= 1
    return render(request, 'incident/resident_dashboard.html', {
        'total': total, 'pending': pending,
        'in_progress': in_progress, 'resolved': resolved,
        'recent': recent, 'notifications': notifications,
        'is_first_login': is_first_login,
    })


def admin_dashboard(request):
    reports = IncidentReport.objects.all()
    total = reports.count()
    pending = reports.filter(status='pending').count()
    in_progress = reports.filter(status='in_progress').count()
    resolved = reports.filter(status='resolved').count()
    critical = reports.filter(priority='critical', status__in=['pending', 'in_progress']).count()
    recent = reports.select_related('reporter', 'category')[:10]

    today = date.today()
    today_count = reports.filter(created_at__date=today).count()
    this_month = reports.filter(created_at__month=today.month, created_at__year=today.year).count()

    by_category = reports.values('category__name').annotate(count=Count('id')).order_by('-count')[:5]
    by_status = reports.values('status').annotate(count=Count('id'))

    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, 'incident/admin_dashboard.html', {
        'total': total, 'pending': pending, 'in_progress': in_progress,
        'resolved': resolved, 'critical': critical, 'recent': recent,
        'today_count': today_count, 'this_month': this_month,
        'by_category': list(by_category), 'by_status': list(by_status),
        'unread_notifications': unread_notifications,
    })


# ── RESIDENT VIEWS ────────────────────────────────────────────────────────────

@login_required
def submit_report(request):
    form = IncidentReportForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user
        report.report_number = generate_report_number()
        report.save()

        ReportUpdate.objects.create(
            report=report,
            updated_by=request.user,
            message='Incident report submitted.',
            new_status='pending'
        )

        # Notify all admins
        admins = User.objects.filter(role='admin', is_active=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                report=report,
                message=f'New incident report: {report.title} from {request.user.full_name}'
            )

        messages.success(request, f'Report {report.report_number} submitted successfully!')
        return redirect('my_reports')

    categories = IncidentCategory.objects.all()
    return render(request, 'incident/submit_report.html', {'form': form, 'categories': categories})


@login_required
def my_reports(request):
    reports = IncidentReport.objects.filter(reporter=request.user).select_related('category')
    status_filter = request.GET.get('status', '')
    if status_filter:
        reports = reports.filter(status=status_filter)
    return render(request, 'incident/my_reports.html', {'reports': reports, 'status_filter': status_filter})


@login_required
def report_detail(request, pk):
    if request.user.role == 'admin':
        report = get_object_or_404(IncidentReport, pk=pk)
    else:
        report = get_object_or_404(IncidentReport, pk=pk, reporter=request.user)

    updates = report.updates.select_related('updated_by').all()

    # Mark notifications as read
    Notification.objects.filter(user=request.user, report=report, is_read=False).update(is_read=True)

    return render(request, 'incident/report_detail.html', {'report': report, 'updates': updates})


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user)
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'incident/notifications.html', {'notifications': notifications})


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'incident/profile.html', {'form': form})


# ── ADMIN VIEWS ───────────────────────────────────────────────────────────────

@login_required
@admin_required
def admin_reports(request):
    reports = IncidentReport.objects.select_related('reporter', 'category', 'assigned_to')
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    search = request.GET.get('search', '')

    if status:
        reports = reports.filter(status=status)
    if priority:
        reports = reports.filter(priority=priority)
    if search:
        reports = reports.filter(Q(title__icontains=search) | Q(reporter__full_name__icontains=search) | Q(report_number__icontains=search))

    return render(request, 'incident/admin_reports.html', {
        'reports': reports, 'status': status, 'priority': priority, 'search': search,
    })


@login_required
@admin_required
def admin_update_report(request, pk):
    report = get_object_or_404(IncidentReport, pk=pk)
    form = AdminUpdateForm(request.POST or None, instance=report)

    if request.method == 'POST' and form.is_valid():
        old_status = report.status
        updated = form.save()
        update_msg = request.POST.get('update_message', '')

        ReportUpdate.objects.create(
            report=updated,
            updated_by=request.user,
            message=update_msg or f'Status updated to {updated.get_status_display()}.',
            old_status=old_status,
            new_status=updated.status
        )

        # Notify the reporter
        Notification.objects.create(
            user=report.reporter,
            report=report,
            message=f'Your report "{report.title}" has been updated to {updated.get_status_display()}.'
        )

        messages.success(request, 'Report updated successfully!')
        return redirect('report_detail', pk=pk)

    return render(request, 'incident/admin_update_report.html', {'form': form, 'report': report})


@login_required
@admin_required
def admin_delete_report(request, pk):
    report = get_object_or_404(IncidentReport, pk=pk)
    if request.method == 'POST':
        num = report.report_number
        report.delete()
        messages.success(request, f'Report {num} deleted.')
        return redirect('admin_reports')
    return render(request, 'incident/confirm_delete.html', {'report': report})


@login_required
@admin_required
def admin_users(request):
    users = User.objects.filter(role='resident').annotate(report_count=Count('reports'))
    return render(request, 'incident/admin_users.html', {'users': users})


@login_required
@admin_required
def admin_reports_page(request):
    reports = IncidentReport.objects.all()
    today = date.today()

    # Monthly summary
    monthly = (reports
               .annotate(month=TruncMonth('created_at'))
               .values('month')
               .annotate(
                   total=Count('id'),
                   resolved=Count('id', filter=Q(status='resolved')),
                   pending=Count('id', filter=Q(status='pending')),
               )
               .order_by('-month')[:12])

    by_category = reports.values('category__name').annotate(count=Count('id')).order_by('-count')
    total = reports.count()
    resolution_rate = round(reports.filter(status='resolved').count() / total * 100, 1) if total else 0

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="incident_reports.csv"'
        writer = csv.writer(response)
        writer.writerow(['Report #', 'Title', 'Reporter', 'Category', 'Location', 'Status', 'Priority', 'Date'])
        for r in reports.select_related('reporter', 'category'):
            writer.writerow([r.report_number, r.title, r.reporter.full_name,
                             r.category.name if r.category else '', r.location,
                             r.status, r.priority, r.created_at.strftime('%Y-%m-%d')])
        return response

    return render(request, 'incident/admin_reports_summary.html', {
        'monthly': monthly, 'by_category': by_category,
        'total': total, 'resolution_rate': resolution_rate,
    })
