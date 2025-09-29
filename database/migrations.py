"""
Database migration utilities for Automotive Price Monitor
"""
import os
import logging
from datetime import datetime
from sqlalchemy import text
from config.database import db_manager, Base
from .models import Product, PriceHistory, ScrapingLog, SiteConfig, User

logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Handle database migrations and initialization"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager or db_manager
        
    def create_database(self):
        """Create database if it doesn't exist"""
        try:
            # Connect without specifying database
            engine_url = self.db_manager.config.SQLALCHEMY_DATABASE_URI.rsplit('/', 1)[0]
            temp_engine = create_engine(engine_url)
            
            with temp_engine.connect() as connection:
                connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {self.db_manager.config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            
            logger.info(f"Database {self.db_manager.config.DB_NAME} created successfully")
            temp_engine.dispose()
            
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            raise
    
    def initialize_tables(self):
        """Initialize all database tables"""
        try:
            # Create all tables
            Base.metadata.create_all(self.db_manager.engine)
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize tables: {e}")
            raise
    
    def seed_data(self):
        """Seed database with initial data"""
        try:
            with self.db_manager.get_session() as session:
                # Create default admin user if not exists
                admin_user = session.query(User).filter_by(username='admin').first()
                if not admin_user:
                    admin_user = User(
                        username='admin',
                        email='admin@lavazembazaar.com',
                        first_name='System',
                        last_name='Administrator',
                        role='admin',
                        is_active=True,
                        is_verified=True
                    )
                    admin_user.set_password('admin123')
                    session.add(admin_user)
                    logger.info("Default admin user created")
                
                # Create site configurations
                site_configs = [
                    {
                        'site_name': 'auto-nik.com',
                        'base_url': 'https://auto-nik.com',
                        'selectors': {
                            'price': '.price, .price-value',
                            'title': 'h1, .product-title',
                            'availability': '.availability, .in-stock'
                        },
                        'request_delay': 2.0,
                        'concurrent_requests': 5,
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    },
                    {
                        'site_name': 'bmwstor.com',
                        'base_url': 'https://bmwstor.com',
                        'selectors': {
                            'price': '.price, .woocommerce-Price-amount',
                            'title': '.product-title, h1',
                            'availability': '.stock-status'
                        },
                        'request_delay': 1.5,
                        'concurrent_requests': 8,
                        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    },
                    {
                        'site_name': 'benzstor.com',
                        'base_url': 'https://benzstor.com',
                        'selectors': {
                            'price': '.price-value, .product-price',
                            'title': '.product-name, h1',
                            'availability': '.availability-status'
                        },
                        'request_delay': 2.0,
                        'concurrent_requests': 6,
                        'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                    },
                    {
                        'site_name': 'mryadaki.com',
                        'base_url': 'https://mryadaki.com',
                        'selectors': {
                            'price': '.price, .product-price-value',
                            'title': '.product-title',
                            'availability': '.stock-info'
                        },
                        'request_delay': 1.8,
                        'concurrent_requests': 10,
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    },
                    {
                        'site_name': 'carinopart.com',
                        'base_url': 'https://carinopart.com',
                        'selectors': {
                            'price': '.price-amount, .current-price',
                            'title': '.product-name',
                            'availability': '.stock-status'
                        },
                        'request_delay': 2.2,
                        'concurrent_requests': 4,
                        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15'
                    },
                    {
                        'site_name': 'japanstor.com',
                        'base_url': 'https://japanstor.com',
                        'selectors': {
                            'price': '.price, .product-price',
                            'title': '.product-title',
                            'availability': '.in-stock, .available'
                        },
                        'request_delay': 1.6,
                        'concurrent_requests': 7,
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101'
                    },
                    {
                        'site_name': 'shojapart.com',
                        'base_url': 'https://shojapart.com',
                        'selectors': {
                            'price': '.price-value, .wc-price',
                            'title': 'h1, .entry-title',
                            'availability': '.availability'
                        },
                        'request_delay': 2.4,
                        'concurrent_requests': 5,
                        'user_agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101'
                    },
                    {
                        'site_name': 'luxyadak.com',
                        'base_url': 'https://luxyadak.com',
                        'selectors': {
                            'price': '.price, .amount',
                            'title': '.product-title',
                            'availability': '.stock-available'
                        },
                        'request_delay': 1.9,
                        'concurrent_requests': 6,
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    },
                    {
                        'site_name': 'parsianlent.com',
                        'base_url': 'https://parsianlent.com',
                        'selectors': {
                            'price': '.price-current, .product-price',
                            'title': '.product-name',
                            'availability': '.availability-text'
                        },
                        'request_delay': 2.1,
                        'concurrent_requests': 5,
                        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    },
                    {
                        'site_name': 'iranrenu.com',
                        'base_url': 'https://iranrenu.com',
                        'selectors': {
                            'price': '.price, .sale-price',
                            'title': '.product-title',
                            'availability': '.stock-status'
                        },
                        'request_delay': 1.7,
                        'concurrent_requests': 8,
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    },
                    {
                        'site_name': 'automoby.ir',
                        'base_url': 'https://automoby.ir',
                        'selectors': {
                            'price': '.price-value, .current-price',
                            'title': '.item-title',
                            'availability': '.availability'
                        },
                        'request_delay': 2.3,
                        'concurrent_requests': 4,
                        'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                    },
                    {
                        'site_name': 'oil-city.ir',
                        'base_url': 'https://www.oil-city.ir',
                        'selectors': {
                            'price': '.price, .product-price',
                            'title': '.product-name',
                            'availability': '.in-stock'
                        },
                        'request_delay': 1.4,
                        'concurrent_requests': 9,
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                ]
                
                for config_data in site_configs:
                    existing_config = session.query(SiteConfig).filter_by(site_name=config_data['site_name']).first()
                    if not existing_config:
                        site_config = SiteConfig(**config_data)
                        session.add(site_config)
                
                logger.info("Site configurations seeded successfully")
                
        except Exception as e:
            logger.error(f"Failed to seed data: {e}")
            raise
    
    def run_migrations(self):
        """Run all migrations"""
        try:
            logger.info("Starting database migrations...")
            
            # Create database
            self.create_database()
            
            # Initialize tables
            self.initialize_tables()
            
            # Seed initial data
            self.seed_data()
            
            logger.info("Database migrations completed successfully")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    def execute_sql_file(self, file_path):
        """Execute SQL file"""
        if os.path.exists(file_path):
            self.db_manager.execute_sql_file(file_path)
        else:
            logger.warning(f"SQL file not found: {file_path}")


def main():
    """Main migration function"""
    try:
        migrator = DatabaseMigrator()
        migrator.run_migrations()
        
        # Also execute init_db.sql if it exists
        init_sql_path = os.path.join(os.path.dirname(__file__), 'init_db.sql')
        migrator.execute_sql_file(init_sql_path)
        
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == '__main__':
    main()
