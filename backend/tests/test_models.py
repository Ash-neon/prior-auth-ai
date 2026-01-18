"""
Database Model Tests
====================

Test database models, relationships, and model methods.

Author: Prior Auth AI Team
Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from backend.models import (
    User, Clinic, AuditLog,
    UserRole, UserStatus, ClinicStatus, AuditAction
)


@pytest.mark.unit
class TestUserModel:
    """Test User model."""
    
    def test_create_user(self, db, test_clinic):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role=UserRole.STAFF,
            status=UserStatus.ACTIVE,
            clinic_id=test_clinic.id
        )
        user.set_password("TestPassword123!")
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.password_hash is not None
    
    def test_user_email_unique(self, db, test_clinic):
        """Test that user email must be unique."""
        user1 = User(
            email="duplicate@example.com",
            role=UserRole.STAFF,
            clinic_id=test_clinic.id
        )
        user1.set_password("password")
        
        db.add(user1)
        db.commit()
        
        # Try to create another user with same email
        user2 = User(
            email="duplicate@example.com",
            role=UserRole.STAFF,
            clinic_id=test_clinic.id
        )
        user2.set_password("password")
        
        db.add(user2)
        
        with pytest.raises(IntegrityError):
            db.commit()
    
    def test_user_password_hashing(self, db, test_clinic):
        """Test password hashing."""
        user = User(
            email="test@example.com",
            role=UserRole.STAFF,
            clinic_id=test_clinic.id
        )
        
        plain_password = "MySecretPassword123!"
        user.set_password(plain_password)
        
        # Password should be hashed
        assert user.password_hash != plain_password
        
        # Should verify correctly
        assert user.verify_password(plain_password) is True
        assert user.verify_password("WrongPassword") is False
    
    def test_user_full_name(self, db, test_clinic):
        """Test full_name property."""
        user = User(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            role=UserRole.STAFF,
            clinic_id=test_clinic.id
        )
        
        assert user.full_name == "John Doe"
        
        # Without name, should return email
        user.first_name = None
        user.last_name = None
        assert user.full_name == "test@example.com"
    
    def test_user_can_login(self, db, test_clinic):
        """Test can_login property."""
        user = User(
            email="test@example.com",
            role=UserRole.STAFF,
            status=UserStatus.ACTIVE,
            is_active=True,
            clinic_id=test_clinic.id
        )
        user.set_password("password")
        
        db.add(user)
        db.commit()
        
        # Active user should be able to login
        assert user.can_login is True
        
        # Inactive user should not
        user.is_active = False
        assert user.can_login is False
        
        # Suspended user should not
        user.is_active = True
        user.status = UserStatus.SUSPENDED
        assert user.can_login is False
    
    def test_user_login_tracking(self, db, test_clinic):
        """Test login success/failure tracking."""
        user = User(
            email="test@example.com",
            role=UserRole.STAFF,
            clinic_id=test_clinic.id
        )
        user.set_password("password")
        
        db.add(user)
        db.commit()
        
        # Record successful login
        user.record_login_success()
        
        assert user.last_login_at is not None
        assert user.failed_login_attempts == 0
        
        # Record failed attempts
        for _ in range(3):
            user.record_login_failure()
        
        assert user.failed_login_attempts == 3
        
        # After 5 failures, should be locked
        user.record_login_failure()
        user.record_login_failure()
        
        assert user.failed_login_attempts == 5
        assert user.is_locked is True
        assert user.can_login is False
    
    def test_user_has_permission(self, db, test_clinic):
        """Test role-based permissions."""
        admin = User(
            email="admin@example.com",
            role=UserRole.ADMIN,
            clinic_id=test_clinic.id
        )
        
        clinician = User(
            email="clinician@example.com",
            role=UserRole.CLINICIAN,
            clinic_id=test_clinic.id
        )
        
        staff = User(
            email="staff@example.com",
            role=UserRole.STAFF,
            clinic_id=test_clinic.id
        )
        
        viewer = User(
            email="viewer@example.com",
            role=UserRole.VIEWER,
            clinic_id=test_clinic.id
        )
        
        # Admin has all permissions
        assert admin.has_permission(UserRole.ADMIN) is True
        assert admin.has_permission(UserRole.CLINICIAN) is True
        assert admin.has_permission(UserRole.STAFF) is True
        assert admin.has_permission(UserRole.VIEWER) is True
        
        # Clinician has clinician, staff, viewer
        assert clinician.has_permission(UserRole.ADMIN) is False
        assert clinician.has_permission(UserRole.CLINICIAN) is True
        assert clinician.has_permission(UserRole.STAFF) is True
        assert clinician.has_permission(UserRole.VIEWER) is True
        
        # Staff has staff and viewer
        assert staff.has_permission(UserRole.ADMIN) is False
        assert staff.has_permission(UserRole.CLINICIAN) is False
        assert staff.has_permission(UserRole.STAFF) is True
        assert staff.has_permission(UserRole.VIEWER) is True
        
        # Viewer only has viewer
        assert viewer.has_permission(UserRole.ADMIN) is False
        assert viewer.has_permission(UserRole.CLINICIAN) is False
        assert viewer.has_permission(UserRole.STAFF) is False
        assert viewer.has_permission(UserRole.VIEWER) is True
    
    def test_user_to_dict_excludes_sensitive(self, db, test_clinic):
        """Test that to_dict excludes sensitive fields."""
        user = User(
            email="test@example.com",
            role=UserRole.STAFF,
            clinic_id=test_clinic.id
        )
        user.set_password("SecretPassword123!")
        user.mfa_secret = "secret_totp_key"
        
        db.add(user)
        db.commit()
        
        user_dict = user.to_dict()
        
        # Sensitive fields should not be in dict
        assert "password_hash" not in user_dict
        assert "mfa_secret" not in user_dict
        
        # Regular fields should be present
        assert user_dict["email"] == "test@example.com"
        assert user_dict["role"] == UserRole.STAFF.value


@pytest.mark.unit
class TestClinicModel:
    """Test Clinic model."""
    
    def test_create_clinic(self, db):
        """Test creating a clinic."""
        clinic = Clinic(
            name="Test Clinic",
            npi="1234567890",
            status=ClinicStatus.ACTIVE
        )
        
        db.add(clinic)
        db.commit()
        db.refresh(clinic)
        
        assert clinic.id is not None
        assert clinic.name == "Test Clinic"
        assert clinic.npi == "1234567890"
    
    def test_clinic_npi_unique(self, db):
        """Test that NPI must be unique."""
        clinic1 = Clinic(name="Clinic 1", npi="1234567890")
        db.add(clinic1)
        db.commit()
        
        clinic2 = Clinic(name="Clinic 2", npi="1234567890")
        db.add(clinic2)
        
        with pytest.raises(IntegrityError):
            db.commit()
    
    def test_clinic_subscription_active(self, db):
        """Test subscription_active property."""
        clinic = Clinic(
            name="Test Clinic",
            status=ClinicStatus.ACTIVE,
            subscription_expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        db.add(clinic)
        db.commit()
        
        assert clinic.subscription_active is True
        
        # Expired subscription
        clinic.subscription_expires_at = datetime.utcnow() - timedelta(days=1)
        assert clinic.subscription_active is False
    
    def test_clinic_feature_management(self, db):
        """Test feature enable/disable."""
        clinic = Clinic(
            name="Test Clinic",
            features_enabled=["feature1", "feature2"]
        )
        
        db.add(clinic)
        db.commit()
        
        # Check features
        assert clinic.has_feature("feature1") is True
        assert clinic.has_feature("feature3") is False
        
        # Enable feature
        clinic.enable_feature("feature3")
        assert clinic.has_feature("feature3") is True
        
        # Disable feature
        clinic.disable_feature("feature1")
        assert clinic.has_feature("feature1") is False
    
    def test_clinic_settings_management(self, db):
        """Test settings get/set."""
        clinic = Clinic(
            name="Test Clinic",
            settings={"timezone": "UTC", "auto_submit": True}
        )
        
        db.add(clinic)
        db.commit()
        
        # Get settings
        assert clinic.get_setting("timezone") == "UTC"
        assert clinic.get_setting("auto_submit") is True
        assert clinic.get_setting("nonexistent", "default") == "default"
        
        # Set setting
        clinic.set_setting("new_setting", "value")
        assert clinic.get_setting("new_setting") == "value"
    
    def test_clinic_address_string(self, db):
        """Test address string formatting."""
        clinic = Clinic(
            name="Test Clinic",
            address={
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip": "02101"
            }
        )
        
        address = clinic.get_address_string()
        
        assert "123 Main St" in address
        assert "Boston" in address
        assert "MA" in address
        assert "02101" in address


@pytest.mark.unit
class TestAuditLogModel:
    """Test AuditLog model."""
    
    def test_create_audit_log(self, db, test_admin_user):
        """Test creating an audit log entry."""
        log = AuditLog.log(
            db=db,
            action=AuditAction.LOGIN,
            description="User logged in",
            user_id=str(test_admin_user.id),
            ip_address="192.168.1.1"
        )
        
        assert log.id is not None
        assert log.action == AuditAction.LOGIN
        assert log.description == "User logged in"
        assert log.success is True
    
    def test_audit_log_with_details(self, db, test_admin_user):
        """Test audit log with additional details."""
        log = AuditLog.log(
            db=db,
            action=AuditAction.PA_CREATED,
            description="Created PA #PA-2026-001",
            user_id=str(test_admin_user.id),
            resource_type="prior_authorization",
            resource_id="pa-123",
            details={
                "pa_number": "PA-2026-001",
                "payer": "Blue Cross",
                "procedure": "99213"
            }
        )
        
        assert log.resource_type == "prior_authorization"
        assert log.resource_id == "pa-123"
        assert log.details["pa_number"] == "PA-2026-001"
    
    def test_audit_log_failed_action(self, db, test_admin_user):
        """Test logging a failed action."""
        log = AuditLog.log(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            description="Failed login attempt",
            user_id=str(test_admin_user.id),
            success=False,
            error_message="Invalid password"
        )
        
        assert log.success is False
        assert log.error_message == "Invalid password"
    
    def test_get_logs_by_user(self, db, test_admin_user):
        """Test retrieving logs by user."""
        # Create multiple logs
        for i in range(5):
            AuditLog.log(
                db=db,
                action=AuditAction.PA_VIEWED,
                description=f"Viewed PA #{i}",
                user_id=str(test_admin_user.id)
            )
        
        logs = AuditLog.get_by_user(db, str(test_admin_user.id), limit=10)
        
        assert len(logs) == 5
        assert all(log.user_id == test_admin_user.id for log in logs)
    
    def test_get_phi_access_logs(self, db, test_admin_user, test_clinic):
        """Test retrieving PHI access logs."""
        # Create PHI access logs
        AuditLog.log(
            db=db,
            action=AuditAction.PATIENT_VIEWED,
            description="Viewed patient record",
            user_id=str(test_admin_user.id),
            clinic_id=str(test_clinic.id)
        )
        
        AuditLog.log(
            db=db,
            action=AuditAction.DOCUMENT_DOWNLOADED,
            description="Downloaded clinical document",
            user_id=str(test_admin_user.id),
            clinic_id=str(test_clinic.id)
        )
        
        # Get PHI logs
        start = datetime.utcnow() - timedelta(hours=1)
        end = datetime.utcnow() + timedelta(hours=1)
        
        logs = AuditLog.get_phi_access_logs(
            db, start, end, clinic_id=str(test_clinic.id)
        )
        
        assert len(logs) == 2
        assert all(log.clinic_id == test_clinic.id for log in logs)


@pytest.mark.unit
class TestModelRelationships:
    """Test model relationships."""
    
    def test_user_clinic_relationship(self, db, test_clinic, test_admin_user):
        """Test User-Clinic relationship."""
        assert test_admin_user.clinic is not None
        assert test_admin_user.clinic.id == test_clinic.id
        assert test_admin_user in test_clinic.users
    
    def test_clinic_users_relationship(self, db, test_clinic, user_factory):
        """Test Clinic can access its users."""
        # Create multiple users for clinic
        users = [user_factory(clinic_id=test_clinic.id) for _ in range(3)]
        
        db.refresh(test_clinic)
        
        assert len(test_clinic.users) >= 3
        
        for user in users:
            assert user in test_clinic.users


@pytest.mark.unit
class TestBaseModelMethods:
    """Test BaseModel utility methods."""
    
    def test_model_to_dict(self, db, test_admin_user):
        """Test to_dict method."""
        user_dict = test_admin_user.to_dict()
        
        assert isinstance(user_dict, dict)
        assert user_dict["email"] == test_admin_user.email
        assert user_dict["id"] == str(test_admin_user.id)
    
    def test_model_soft_delete(self, db, test_admin_user):
        """Test soft delete."""
        assert test_admin_user.is_deleted is False
        assert test_admin_user.deleted_at is None
        
        test_admin_user.soft_delete()
        
        assert test_admin_user.is_deleted is True
        assert test_admin_user.deleted_at is not None
    
    def test_get_by_id(self, db, test_admin_user):
        """Test get_by_id class method."""
        found_user = User.get_by_id(db, str(test_admin_user.id))
        
        assert found_user is not None
        assert found_user.id == test_admin_user.id
    
    def test_get_all_with_pagination(self, db, test_clinic, user_factory):
        """Test get_all with pagination."""
        # Create 10 users
        for _ in range(10):
            user_factory()
        
        # Get first page
        page1 = User.get_all(db, skip=0, limit=5)
        assert len(page1) == 5
        
        # Get second page
        page2 = User.get_all(db, skip=5, limit=5)
        assert len(page2) == 5
        
        # Pages should have different users
        page1_ids = {u.id for u in page1}
        page2_ids = {u.id for u in page2}
        assert page1_ids.isdisjoint(page2_ids)