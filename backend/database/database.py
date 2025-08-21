import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging
from .models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database manager.
        
        Args:
            database_url: Database connection URL. If None, uses environment variable.
        """
        if database_url is None:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///gusto_monitor.db')
        
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _setup_database(self):
        """Set up database engine and session factory."""
        try:
            if self.database_url.startswith('sqlite'):
                # SQLite configuration
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=False
                )
            else:
                # PostgreSQL or other databases
                self.engine = create_engine(
                    self.database_url,
                    pool_size=20,
                    max_overflow=0,
                    echo=False
                )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"Database configured with URL: {self.database_url}")
            
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables. Use with caution!"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Get a database session with automatic cleanup.
        
        Yields:
            Session: SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """
        Get a database session without context manager.
        Note: Remember to close the session manually.
        
        Returns:
            Session: SQLAlchemy session
        """
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            from sqlalchemy import text
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

# Global database manager instance
db_manager = None

def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Returns:
        DatabaseManager: Global database manager
    """
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def init_database(database_url: str = None, create_tables: bool = True):
    """
    Initialize the database with optional table creation.
    
    Args:
        database_url: Database connection URL
        create_tables: Whether to create tables
    """
    global db_manager
    db_manager = DatabaseManager(database_url)
    
    if create_tables:
        db_manager.create_tables()
    
    # Test connection
    if not db_manager.test_connection():
        raise ConnectionError("Failed to connect to database")
    
    logger.info("Database initialized successfully")

def get_session():
    """
    Get a database session from the global manager.
    
    Returns:
        Session context manager
    """
    return get_database_manager().get_session() 