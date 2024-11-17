import os
import sys
from pathlib import Path

# Add the parent directory to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.core.init_db import init_db
from alembic.config import Config
from alembic import command


def run_migrations():
    """Run database migrations."""
    try:
        # Get the path to the alembic.ini file
        alembic_ini = str(Path(__file__).parent.parent / "alembic.ini")
        
        # Create Alembic configuration object
        alembic_cfg = Config(alembic_ini)
        
        # Run the migration
        command.upgrade(alembic_cfg, "head")
        print("Database migrations completed successfully.")
        
        return True
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False


def initialize_db():
    """Initialize database with default data."""
    try:
        db = SessionLocal()
        init_db(db)
        print("Database initialized successfully.")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting database initialization...")
    
    # Run migrations
    if run_migrations():
        # Initialize database with default data
        initialize_db()
    else:
        print("Failed to run migrations. Database initialization aborted.")