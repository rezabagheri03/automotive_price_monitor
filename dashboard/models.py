"""
Dashboard-specific models and user management
"""
from datetime import datetime
from typing import Optional
from flask_login import UserMixin
from database.models import User
from config.database import db_manager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DashboardUser(UserMixin):
    """User model for Flask-Login integration"""
    
    def __init__(self, user_data: User):
        self.id = user_data.id
        self.username = user_data.username
        self.email = user_data.email
        self.first_name = user_data.first_name
        self.last_name = user_data.last_name
        self.role = user_data.role
        self.is_active_user = user_data.is_active
        self.is_verified = user_data.is_verified
        self.last_login = user_data.last_login
        self.login_count = user_data.login_count
    
    def get_id(self):
        """Return user ID as string (required by Flask-Login)"""
        return str(self.id)
    
    @property
    def is_active(self):
        """Check if user account is active"""
        return self.is_active_user
    
    @property
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    @property
    def is_authenticated(self):
        """User is always authenticated if this object exists"""
        return True
    
    @property
    def is_anonymous(self):
        """Users are not anonymous"""
        return False
    
    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.username
    
    @staticmethod
    def get(user_id: str) -> Optional['DashboardUser']:
        """Get user by ID"""
        try:
            with db_manager.get_session() as session:
                user = session.query(User).filter(
                    User.id == int(user_id),
                    User.is_active == True
                ).first()
                
                if user:
                    return DashboardUser(user)
                return None
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    @staticmethod
    def authenticate(username: str, password: str) -> Optional['DashboardUser']:
        """Authenticate user by username and password"""
        try:
            with db_manager.get_session() as session:
                user = session.query(User).filter(
                    User.username == username,
                    User.is_active == True
                ).first()
                
                if user and user.check_password(password):
                    # Update login info
                    user.last_login = datetime.utcnow()
                    user.login_count = (user.login_count or 0) + 1
                    
                    return DashboardUser(user)
                
                return None
                
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {e}")
            return None
    
    @staticmethod
    def create_user(username: str, email: str, password: str, 
                   first_name: str = None, last_name: str = None, 
                   role: str = 'user') -> Optional['DashboardUser']:
        """Create new user"""
        try:
            with db_manager.get_session() as session:
                # Check if user already exists
                existing_user = session.query(User).filter(
                    (User.username == username) | (User.email == email)
                ).first()
                
                if existing_user:
                    raise ValueError("User already exists with this username or email")
                
                # Create new user
                new_user = User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                new_user.set_password(password)
                
                session.add(new_user)
                session.flush()
                
                logger.info(f"Created new user: {username} ({email})")
                return DashboardUser(new_user)
                
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            return None
    
    def update_profile(self, **kwargs) -> bool:
        """Update user profile"""
        try:
            with db_manager.get_session() as session:
                user = session.query(User).get(self.id)
                if not user:
                    return False
                
                # Update allowed fields
                allowed_fields = ['first_name', 'last_name', 'email']
                for field, value in kwargs.items():
                    if field in allowed_fields:
                        setattr(user, field, value)
                        setattr(self, field, value)
                
                user.updated_at = datetime.utcnow()
                
                logger.info(f"Updated profile for user: {self.username}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating profile for user {self.username}: {e}")
            return False
    
    def change_password(self, new_password: str) -> bool:
        """Change user password"""
        try:
            with db_manager.get_session() as session:
                user = session.query(User).get(self.id)
                if not user:
                    return False
                
                user.set_password(new_password)
                user.updated_at = datetime.utcnow()
                
                logger.info(f"Password changed for user: {self.username}")
                return True
                
        except Exception as e:
            logger.error(f"Error changing password for user {self.username}: {e}")
            return False


class DashboardSettings:
    """Manage dashboard settings and preferences"""
    
    def __init__(self):
        self.settings = self._load_default_settings()
    
    def _load_default_settings(self) -> dict:
        """Load default dashboard settings"""
        return {
            'price_display_type': 'avg',  # avg, min, max
            'products_per_page': 25,
            'auto_refresh_interval': 300,  # seconds
            'show_price_trends': True,
            'enable_notifications': True,
            'theme': 'light',  # light, dark
            'language': 'fa',  # fa, en
            'currency_symbol': 'ریال',
            'date_format': '%Y-%m-%d',
            'time_format': '%H:%M',
            'chart_colors': ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8'],
            'dashboard_widgets': {
                'system_stats': True,
                'recent_activities': True,
                'price_trends': True,
                'site_status': True
            }
        }
    
    def get(self, key: str, default=None):
        """Get setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """Set setting value"""
        self.settings[key] = value
    
    def update(self, settings_dict: dict):
        """Update multiple settings"""
        self.settings.update(settings_dict)
    
    def get_all(self) -> dict:
        """Get all settings"""
        return self.settings.copy()
    
    def save_to_database(self, user_id: int):
        """Save settings to database (user-specific settings)"""
        # TODO: Implement user-specific settings storage
        pass
    
    def load_from_database(self, user_id: int):
        """Load settings from database"""
        # TODO: Implement user-specific settings loading
        pass


# Global dashboard settings instance
dashboard_settings = DashboardSettings()
