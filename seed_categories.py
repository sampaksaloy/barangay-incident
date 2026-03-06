# seed_categories.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mywebsite.settings')
django.setup()

from incident.models import IncidentCategory

CATEGORIES = [
    {'name': 'Fire Incident', 'icon': 'bi-fire', 'color': 'danger'},
    {'name': 'Noise Complaint', 'icon': 'bi-volume-up', 'color': 'warning'},
    {'name': 'Traffic Accident', 'icon': 'bi-car-front', 'color': 'secondary'},
    {'name': 'Medical Emergency', 'icon': 'bi-plus-circle', 'color': 'danger'},
    {'name': 'Garbage/Waste', 'icon': 'bi-trash', 'color': 'success'},
    {'name': 'Flooding', 'icon': 'bi-water', 'color': 'primary'},
    {'name': 'Illegal Activity', 'icon': 'bi-shield-exclamation', 'color': 'dark'},
    {'name': 'Street Light Issue', 'icon': 'bi-lightbulb', 'color': 'info'},
]

for cat in CATEGORIES:
    obj, created = IncidentCategory.objects.get_or_create(name=cat['name'], defaults=cat)
    if created:
        print(f"Added: {cat['name']}")
    else:
        print(f"Skipped: {cat['name']} (already exists)")