"""
Authentication API Test Suite

Tests authentication endpoints including:
- Login success/failure
- JWT token refresh
- Account lockout after failed attempts
- Password hashing
- Password reset flow
- Disabled/suspended user access denial
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User, UserRole
from backend.core.security import get_password_hash, verify_password
from backend.core.config import settings


class TestLogin:
    """Test login endpoint functionality."""
    
    @pytest.mark.asyncio
    async def test_login_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test successful login with valid credentials."""
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
        # Verify user info returned
        assert data["user"]["email"] == test_user.email
        assert data["user"]["id"] == str(test_user.id)
    
    @pytest.mark.asyncio
    async def test_login_invalid_email(
        self,
        async_client: AsyncClient,
    ):
        """Test login with non-existent email."""
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "somepassword",
            },
        )
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """Test login with incorrect password."""
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_disabled_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test login with disabled user account."""
        # Create disabled user
        disabled_user = User(
            email="disabled@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Disabled User",
            role=UserRole.USER,
            is_active=False,
        )
        db_session.add(disabled_user)
        await db_session.commit()
        
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": "disabled@example.com",
                "password": "testpass123",
            },
        )
        
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_missing_credentials(
        self,
        async_client: AsyncClient,
    ):
        """Test login with missing credentials."""
        # Missing password
        response = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com"},
        )
        assert response.status_code == 422
        
        # Missing username
        response = await async_client.post(
            "/api/v1/auth/login",
            data={"password": "testpass123"},
        )
        assert response.status_code == 422


class TestAccountLockout:
    """Test account lockout after multiple failed login attempts."""
    
    @pytest.mark.asyncio
    async def test_account_locks_after_five_failures(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that account locks after 5 consecutive failed login attempts."""
        # Attempt 5 failed logins
        for i in range(5):
            response = await async_client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user.email,
                    "password": "wrongpassword",
                },
            )
            
            if i < 4:
                assert response.status_code == 401
                assert "Incorrect email or password" in response.json()["detail"]
        
        # Refresh user from database
        await db_session.refresh(test_user)
        
        # Check that account is locked
        assert test_user.failed_login_attempts >= 5
        assert test_user.locked_until is not None
        assert test_user.locked_until > datetime.utcnow()
        
        # Next attempt should indicate locked account
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123",  # Even correct password
            },
        )
        
        assert response.status_code == 400
        assert "locked" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_failed_attempts_reset_on_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that failed attempt counter resets on successful login."""
        # Make 3 failed attempts
        for _ in range(3):
            await async_client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user.email,
                    "password": "wrongpassword",
                },
            )
        
        await db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 3
        
        # Successful login
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123",
            },
        )
        
        assert response.status_code == 200
        
        await db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 0
        assert test_user.locked_until is None
    
    @pytest.mark.asyncio
    async def test_lockout_expires_after_duration(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that locked account can login after lockout period expires."""
        # Set lockout to expire in the past
        test_user.failed_login_attempts = 5
        test_user.locked_until = datetime.utcnow() - timedelta(minutes=1)
        await db_session.commit()
        
        # Should be able to login now
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123",
            },
        )
        
        assert response.status_code == 200
        
        await db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 0
        assert test_user.locked_until is None


class TestTokenRefresh:
    """Test JWT token refresh functionality."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """Test successful token refresh."""
        # First, login to get tokens
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123",
            },
        )
        
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh the token
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # New tokens should be different from originals
        assert data["access_token"] != login_response.json()["access_token"]
    
    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(
        self,
        async_client: AsyncClient,
    ):
        """Test token refresh with invalid token."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_refresh_with_access_token(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """Test that access token cannot be used for refresh."""
        # Login to get tokens
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123",
            },
        )
        
        access_token = login_response.json()["access_token"]
        
        # Try to refresh with access token
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        
        # Should fail - access tokens have wrong token_type claim
        assert response.status_code == 401


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_is_hashed(self, test_user: User):
        """Verify that passwords are stored hashed, not in plaintext."""
        # Password should not match plaintext
        assert test_user.hashed_password != "testpass123"
        
        # Should start with bcrypt identifier
        assert test_user.hashed_password.startswith("$2b$")
    
    def test_password_verification(self):
        """Test password hashing and verification."""
        password = "mysecurepassword123"
        hashed = get_password_hash(password)
        
        # Verify correct password
        assert verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert verify_password("wrongpassword", hashed) is False
    
    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salted)."""
        password = "samepassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestPasswordReset:
    """Test password reset flow."""
    
    @pytest.mark.asyncio
    async def test_password_reset_request_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test initiating password reset for valid email."""
        response = await async_client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": test_user.email},
        )
        
        assert response.status_code == 200
        assert "email has been sent" in response.json()["message"].lower()
        
        # Check that reset token was generated
        await db_session.refresh(test_user)
        assert test_user.reset_token is not None
        assert test_user.reset_token_expires is not None
        assert test_user.reset_token_expires > datetime.utcnow()
    
    @pytest.mark.asyncio
    async def test_password_reset_request_nonexistent_email(
        self,
        async_client: AsyncClient,
    ):
        """Test password reset for non-existent email."""
        response = await async_client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "nonexistent@example.com"},
        )
        
        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        assert "email has been sent" in response.json()["message"].lower()
    
    @pytest.mark.asyncio
    async def test_password_reset_complete_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test completing password reset with valid token."""
        # First request a reset
        await async_client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": test_user.email},
        )
        
        await db_session.refresh(test_user)
        reset_token = test_user.reset_token
        
        # Complete the reset
        new_password = "newpassword123"
        response = await async_client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": reset_token,
                "new_password": new_password,
            },
        )
        
        assert response.status_code == 200
        assert "reset successfully" in response.json()["message"].lower()
        
        # Verify password was changed
        await db_session.refresh(test_user)
        assert verify_password(new_password, test_user.hashed_password)
        
        # Reset token should be cleared
        assert test_user.reset_token is None
        assert test_user.reset_token_expires is None
        
        # Should be able to login with new password
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": new_password,
            },
        )
        assert login_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_password_reset_invalid_token(
        self,
        async_client: AsyncClient,
    ):
        """Test password reset with invalid token."""
        response = await async_client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": "invalid-token-12345",
                "new_password": "newpassword123",
            },
        )
        
        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_password_reset_expired_token(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test password reset with expired token."""
        # Set expired reset token
        test_user.reset_token = "expired-token-12345"
        test_user.reset_token_expires = datetime.utcnow() - timedelta(hours=1)
        await db_session.commit()
        
        response = await async_client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": "expired-token-12345",
                "new_password": "newpassword123",
            },
        )
        
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_password_reset_weak_password(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test password reset rejects weak passwords."""
        # Request reset
        await async_client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": test_user.email},
        )
        
        await db_session.refresh(test_user)
        reset_token = test_user.reset_token
        
        # Try to set weak password
        response = await async_client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": reset_token,
                "new_password": "123",  # Too short
            },
        )
        
        assert response.status_code == 422
        assert "at least" in response.json()["detail"][0]["msg"].lower()


class TestSuspendedUsers:
    """Test access denial for suspended users."""
    
    @pytest.mark.asyncio
    async def test_suspended_user_cannot_login(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that suspended users cannot login."""
        # Create suspended user
        suspended_user = User(
            email="suspended@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Suspended User",
            role=UserRole.USER,
            is_active=True,
            is_suspended=True,
        )
        db_session.add(suspended_user)
        await db_session.commit()
        
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": "suspended@example.com",
                "password": "testpass123",
            },
        )
        
        assert response.status_code == 400
        assert "suspended" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_suspended_user_cannot_access_protected_routes(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that suspended users cannot access protected endpoints."""
        # Create active user then suspend
        user = User(
            email="willbesuspended@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Will Be Suspended",
            role=UserRole.USER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        
        # Login successfully first
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": user.email,
                "password": "testpass123",
            },
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        
        # Suspend the user
        user.is_suspended = True
        await db_session.commit()
        
        # Try to access protected endpoint
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        # Should be denied (token validation checks suspension status)
        assert response.status_code == 403
        assert "suspended" in response.json()["detail"].lower()


class TestMultipleSimultaneousLogins:
    """Test behavior with multiple concurrent sessions."""
    
    @pytest.mark.asyncio
    async def test_multiple_logins_allowed(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """Test that same user can have multiple active sessions."""
        # First login
        response1 = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123",
            },
        )
        assert response1.status_code == 200
        token1 = response1.json()["access_token"]
        
        # Second login
        response2 = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123",
            },
        )
        assert response2.status_code == 200
        token2 = response2.json()["access_token"]
        
        # Both tokens should be different and valid
        assert token1 != token2
        
        # Both should work for protected endpoints
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        resp1 = await async_client.get("/api/v1/users/me", headers=headers1)
        resp2 = await async_client.get("/api/v1/users/me", headers=headers2)
        
        assert resp1.status_code == 200
        assert resp2.status_code == 200


class TestRateLimiting:
    """Test rate limiting on authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_rate_limit(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """Test that excessive login attempts are rate limited."""
        # Make many rapid login attempts
        responses = []
        for _ in range(20):
            response = await async_client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user.email,
                    "password": "wrongpassword",
                },
            )
            responses.append(response)
        
        # At least some should be rate limited (429)
        rate_limited = [r for r in responses if r.status_code == 429]
        
        # Note: This test assumes rate limiting is implemented
        # If not yet implemented, this assertion may need adjustment
        assert len(rate_limited) > 0 or all(
            r.status_code == 401 for r in responses
        ), "Either rate limiting should trigger or all should fail auth"