"""
Database Initialization Script
===============================

Initialize the database with:
- Run all Alembic migrations
- Create default admin user
- Create sample clinic (optional)
- Verify database connectivity

Usage:
    python -m backend.scripts.init_db
    python -m backend.scripts.init_db --seed-sample-data

Author: Prior Auth AI Team
Version: 1.0.0
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text
from alembic import command
from alembic.config import Config

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.db.session import engine, SessionLocal
from backend.models import User, Clinic, UserRole, UserStatus, ClinicStatus

logger = get_logger(__name__)


def run_migrations():
    """Run Alembic migrations to create/update schema."""
    logger.info("Running database migrations...")
    
    try:
        # Create Alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        logger.info("✓ Migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def verify_connection():
    """Verify database connection."""
    logger.info("Verifying database connection...")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        logger.info("✓ Database connection successful")
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def create_default_admin(db: SessionLocal):
    """
    Create default admin user if not exists.
    
    Args:
        db: Database session
    """
    logger.info("Creating default admin user...")
    
    # Check if admin exists
    admin_email = settings.FIRST_SUPERUSER_EMAIL or "admin@priorauth.ai"
    existing_admin = User.get_by_email(db, admin_email)
    
    if existing_admin:
        logger.info(f"✓ Admin user already exists: {admin_email}")
        return existing_admin
    
    # Create admin user
    admin = User(
        email=admin_email,
        first_name="System",
        last_name="Administrator",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
        email_verified=True
    )
    
    # Set password
    default_password = settings.FIRST_SUPERUSER_PASSWORD or "changeme123"
    admin.set_password(default_password)
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    logger.info(f"✓ Admin user created: {admin_email}")
    logger.warning(f"  Default password: {default_password}")
    logger.warning("  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY IN PRODUCTION!")
    
    return admin


def create_sample_clinic(db: SessionLocal, admin_user: User):
    """
    Create a sample clinic for testing.
    
    Args:
        db: Database session
        admin_user: Admin user to associate with clinic
    """
    logger.info("Creating sample clinic...")
    
    # Check if sample clinic exists
    existing_clinic = Clinic.get_by_npi(db, "1234567890")
    
    if existing_clinic:
        logger.info("✓ Sample clinic already exists")
        return existing_clinic
    
    # Create sample clinic
    clinic = Clinic(
        name="Sample Medical Clinic",
        npi="1234567890",
        tax_id="12-3456789",
        address={
            "street": "123 Medical Plaza",
            "city": "Boston",
            "state": "MA",
            "zip": "02101"
        },
        phone="+1-555-123-4567",
        fax="+1-555-123-4568",
        email="contact@sampleclinic.com",
        status=ClinicStatus.ACTIVE,
        is_active=True,
        subscription_tier="trial",
        max_users=10,
        max_pas_per_month=100,
        features_enabled=[
            "ai_extraction",
            "multi_channel_submission",
            "analytics"
        ],
        settings={
            "timezone": "America/New_York",
            "default_priority": "routine",
            "auto_submit": False
        }
    )
    
    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    
    # Associate admin with clinic
    admin_user.clinic_id = clinic.id
    db.commit()
    
    logger.info(f"✓ Sample clinic created: {clinic.name} (NPI: {clinic.npi})")
    logger.info(f"  Admin user linked to clinic")
    
    return clinic


def verify_schema():
    """Verify that all tables were created."""
    logger.info("Verifying database schema...")
    
    try:
        with engine.connect() as conn:
            # Check for main tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN ('clinics', 'users', 'audit_logs')
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            
            expected_tables = ['audit_logs', 'clinics', 'users']
            
            if set(tables) == set(expected_tables):
                logger.info(f"✓ All required tables exist: {', '.join(tables)}")
                return True
            else:
                missing = set(expected_tables) - set(tables)
                logger.error(f"✗ Missing tables: {', '.join(missing)}")
                return False
                
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return False


def init_database(seed_sample_data: bool = False):
    """
    Initialize the complete database.
    
    Args:
        seed_sample_data: Whether to create sample clinic and data
    """
    logger.info("="*60)
    logger.info("Prior Authorization AI - Database Initialization")
    logger.info("="*60)
    logger.info("")
    
    # Step 1: Verify connection
    if not verify_connection():
        logger.error("✗ Database initialization failed")
        return False
    
    logger.info("")
    
    # Step 2: Run migrations
    if not run_migrations():
        logger.error("✗ Database initialization failed")
        return False
    
    logger.info("")
    
    # Step 3: Verify schema
    if not verify_schema():
        logger.error("✗ Database initialization failed")
        return False
    
    logger.info("")
    
    # Step 4: Create default admin
    db = SessionLocal()
    try:
        admin_user = create_default_admin(db)
        logger.info("")
        
        # Step 5: Optionally create sample data
        if seed_sample_data:
            create_sample_clinic(db, admin_user)
            logger.info("")
        
        logger.info("="*60)
        logger.info("✓ Database initialization completed successfully!")
        logger.info("="*60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Start the backend server: uvicorn main:app --reload")
        logger.info("  2. Access API docs: http://localhost:8000/docs")
        logger.info(f"  3. Login with: {admin_user.email}")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize Prior Authorization AI database"
    )
    parser.add_argument(
        "--seed-sample-data",
        action="store_true",
        help="Create sample clinic and test data"
    )
    
    args = parser.parse_args()
    
    success = init_database(seed_sample_data=args.seed_sample_data)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()