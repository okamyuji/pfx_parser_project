from django.urls import path
from .views import parse_pfx

urlpatterns = [
    path('parse_pfx/', parse_pfx, name='parse_pfx'),
]
