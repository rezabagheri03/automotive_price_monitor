"""
Database configuration and connection management
"""
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from .settings import Config

logger = logging.getLogger(__name__)

# Create base class for models
Base = declarative_base()


class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.engine = None
        self.session_factory = None
        self.Session = None
        self._setup_database()
    
    def _setup_database(self):
        """Initialize database engine and session factory"""
        try:
            # Create engine with connection pooling
            self.engine = create_engine(
                self.config.SQLALCHEMY_DATABASE_URI,
                **self.config.SQLALCHEMY_ENGINE_OPTIONS,
                echo=self.config.FLASK_ENV == 'development'
            )
            
            # Create session factory
            self.session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(self.session_factory)
            
            logger.info("Database connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        try:
            Base.metadata.drop_all(self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def execute_sql_file(self, file_path):
        """Execute SQL commands from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                sql_commands = file.read()
            
            with self.engine.connect() as connection:
                # Split commands by semicolon and execute each
                for command in sql_commands.split(';'):
                    command = command.strip()
                    if command:
                        connection.execute(text(command))
                        
            logger.info(f"SQL file executed successfully: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to execute SQL file {file_path}: {e}")
            raise
    
    def get_table_row_count(self, table_name):
        """Get row count for a table"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get row count for {table_name}: {e}")
            return 0
    
    def backup_database(self, backup_path):
        """Create database backup (requires mysqldump)"""
        import subprocess
        import os
        
        try:
            # Create backup directory if it doesn't exist
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Build mysqldump command
            cmd = [
                'mysqldump',
                f'--host={self.config.DB_HOST}',
                f'--port={self.config.DB_PORT}',
                f'--user={self.config.DB_USER}',
                f'--password={self.config.DB_PASSWORD}',
                '--single-transaction',
                '--routines',
                '--triggers',
                self.config.DB_NAME
            ]
            
            # Execute backup
            with open(backup_path, 'w') as backup_file:
                subprocess.run(cmd, stdout=backup_file, check=True)
            
            logger.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def close(self):
        """Close database connections"""
        if self.Session:
            self.Session.remove()
        if self.engine:
            self.engine.dispose()
        logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()
