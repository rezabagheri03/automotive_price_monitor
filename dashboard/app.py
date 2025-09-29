"""
Flask application factory for dashboard
"""
import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config.settings import config
from config.database import db_manager
from utils.logger import setup_logger

logger = setup_logger(__name__)


def create_app(config_name=None):
    """Create and configure Flask application"""
    
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    csrf = CSRFProtect(app)
    
    # Setup login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'لطفاً برای دسترسی به این صفحه وارد شوید.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models import DashboardUser
        return DashboardUser.get(user_id)
    
    # Register blueprints
    from .routes import main_bp, auth_bp, api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Setup error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    # Add template filters
    @app.template_filter('currency')
    def currency_filter(value):
        """Format currency values"""
        if value is None:
            return "0"
        return f"{int(value):,}"
    
    @app.template_filter('datetime')
    def datetime_filter(value, format='%Y-%m-%d %H:%M'):
        """Format datetime values"""
        if value is None:
            return ""
        return value.strftime(format)
    
    @app.template_filter('status_badge')
    def status_badge_filter(status):
        """Convert status to Bootstrap badge class"""
        status_map = {
            'ok': 'success',
            'healthy': 'success',
            'completed': 'success',
            'warning': 'warning',
            'degraded': 'warning',
            'error': 'danger',
            'unhealthy': 'danger',
            'failed': 'danger'
        }
        return status_map.get(status.lower(), 'secondary')
    
    # Context processors
    @app.context_processor
    def inject_global_vars():
        """Inject global variables into templates"""
        return {
            'app_name': 'Automotive Price Monitor',
            'app_version': '1.0.0',
            'current_year': datetime.utcnow().year
        }
    
    # Initialize database tables
    try:
        db_manager.create_tables()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    logger.info(f"Flask app created with config: {config_name}")
    return app


# Import at the end to avoid circular imports
from flask import render_template
from datetime import datetime
