"""
Dashboard package for Automotive Price Monitor
"""
from .app import create_app
from .models import DashboardUser
from .routes import main_bp, auth_bp, api_bp
from .forms import LoginForm, ProductForm, SettingsForm

__all__ = [
    'create_app',
    'DashboardUser',
    'main_bp',
    'auth_bp', 
    'api_bp',
    'LoginForm',
    'ProductForm',
    'SettingsForm'
]
