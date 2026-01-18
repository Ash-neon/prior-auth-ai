"""
User Management API Test Suite

Tests user CRUD operations including:
- Profile viewing and editing
- Permission enforcement
- Admin vs regular user behavior
- User listing and filtering
- Invalid update handling
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User, UserRole
from backend.core.security import get_password_hash


class TestGetCurrentUser:
    """Test GET /users/me endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_own_profile_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        user_token_headers: dict,
    ):
        """Test that user can retrieve their own profile."""
        response = await async_client.get(
            "/api/v1/users/me",
            headers=user_token_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == test_user.email
        assert data["id"] == str(test_user.id)
        assert data["full_name"] == test_user.full_name
        assert data["role"] == test_user.role.value
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_get_profile_without_auth(
        self,
        async_client: AsyncClient,
    ):
        """Test that unauthenticated request is denied."""
        response = await async_client.get("/api/v1/users/me")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]


class TestUpdateCurrentUser:
    """Test PATCH /users/me endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_own_profile_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        user_token_headers: dict,
    ):
        """Test that user can update their own profile."""
        new_name = "Updated Name"
        
        response = await async_client.patch(
            "/api/v1/users/me",
            headers=user_token_headers,
            json={"full_name": new_name},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == new_name
        
        # Verify in database
        await db_session.refresh(test_user)
        assert test_user.full_name == new_name
    
    @pytest.mark.asyncio
    async def test_update_own_email(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        user_token_headers: dict,
    ):
        """Test that user can change their email."""
        new_email = "newemail@example.com"
        
        response = await async_client.patch(
            "/api/v1/users/me",
            headers=user_token_headers,
            json={"email": new_email},
        )
        
        assert response.status_code == 200
        assert response.json()["email"] == new_email
        
        await db_session.refresh(test_user)
        assert test_user.email == new_email
    
    @pytest.mark.asyncio
    async def test_update_email_already_exists(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        user_token_headers: dict,
    ):
        """Test that duplicate email is rejected."""
        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Other User",
            role=UserRole.USER,
        )
        db_session.add(other_user)
        await db_session.commit()
        
        # Try to change to existing email
        response = await async_client.patch(
            "/api/v1/users/me",
            headers=user_token_headers,
            json={"email": "other@example.com"},
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_user_cannot_change_own_role(
        self,
        async_client: AsyncClient,
        test_user: User,
        user_token_headers: dict,
    ):
        """Test that regular user cannot escalate their own role."""
        response = await async_client.patch(
            "/api/v1/users/me",
            headers=user_token_headers,
            json={"role": "admin"},
        )
        
        assert response.status_code == 403
        assert "Cannot change your own role" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_user_cannot_change_own_active_status(
        self,
        async_client: AsyncClient,
        test_user: User,
        user_token_headers: dict,
    ):
        """Test that user cannot deactivate their own account."""
        response = await async_client.patch(
            "/api/v1/users/me",
            headers=user_token_headers,
            json={"is_active": False},
        )
        
        assert response.status_code == 403
        assert "Cannot change your own active status" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_user_cannot_make_self_superuser(
        self,
        async_client: AsyncClient,
        test_user: User,
        user_token_headers: dict,
    ):
        """Test that user cannot grant themselves superuser status."""
        response = await async_client.patch(
            "/api/v1/users/me",
            headers=user_token_headers,
            json={"is_superuser": True},
        )
        
        assert response.status_code == 403
        assert "Cannot change your own superuser status" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_update_preferences(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        user_token_headers: dict,
    ):
        """Test updating user preferences."""
        preferences = {
            "theme": "dark",
            "notifications": True,
            "language": "en",
        }
        
        response = await async_client.patch(
            "/api/v1/users/me",
            headers=user_token_headers,
            json={"preferences": preferences},
        )
        
        assert response.status_code == 200
        assert response.json()["preferences"] == preferences
        
        await db_session.refresh(test_user)
        assert test_user.preferences == preferences


class TestListUsers:
    """Test GET /users endpoint (admin only)."""
    
    @pytest.mark.asyncio
    async def test_admin_can_list_users(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        admin_token_headers: dict,
    ):
        """Test that admin can list all users."""
        # Create some test users
        for i in range(3):
            user = User(
                email=f"user{i}@example.com",
                hashed_password=get_password_hash("testpass123"),
                full_name=f"User {i}",
                role=UserRole.USER,
            )
            db_session.add(user)
        await db_session.commit()
        
        response = await async_client.get(
            "/api/v1/users",
            headers=admin_token_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "users" in data
        assert "total" in data
        assert len(data["users"]) >= 3
        assert data["total"] >= 3
    
    @pytest.mark.asyncio
    async def test_regular_user_cannot_list_users(
        self,
        async_client: AsyncClient,
        user_token_headers: dict,
    ):
        """Test that regular user cannot list users."""
        response = await async_client.get(
            "/api/v1/users",
            headers=user_token_headers,
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_list_users_with_pagination(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        admin_token_headers: dict,
    ):
        """Test user listing pagination."""
        # Create 10 users
        for i in range(10):
            user = User(
                email=f"paginate{i}@example.com",
                hashed_password=get_password_hash("testpass123"),
                full_name=f"Paginate User {i}",
                role=UserRole.USER,
            )
            db_session.add(user)
        await db_session.commit()
        
        # First page
        response = await async_client.get(
            "/api/v1/users?skip=0&limit=5",
            headers=admin_token_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 5
        assert data["skip"] == 0
        assert data["limit"] == 5
        
        # Second page
        response = await async_client.get(
            "/api/v1/users?skip=5&limit=5",
            headers=admin_token_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) >= 5
    
    @pytest.mark.asyncio
    async def test_list_users_filter_by_role(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        admin_token_headers: dict,
    ):
        """Test filtering users by role."""
        # Create users with different roles
        analyst = User(
            email="analyst@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Analyst User",
            role=UserRole.ANALYST,
        )
        db_session.add(analyst)
        await db_session.commit()
        
        response = await async_client.get(
            "/api/v1/users?role=analyst",
            headers=admin_token_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned users should be analysts
        for user in data["users"]:
            assert user["role"] == "analyst"
    
    @pytest.mark.asyncio
    async def test_list_users_filter_by_active_status(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        admin_token_headers: dict,
    ):
        """Test filtering users by active status."""
        # Create inactive user
        inactive = User(
            email="inactive@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Inactive User",
            role=UserRole.USER,
            is_active=False,
        )
        db_session.add(inactive)
        await db_session.commit()
        
        # Get only inactive users
        response = await async_client.get(
            "/api/v1/users?is_active=false",
            headers=admin_token_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned users should be inactive
        for user in data["users"]:
            assert user["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_list_users_search(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        admin_token_headers: dict,
    ):
        """Test searching users by email or name."""
        # Create user with unique name
        user = User(
            email="searchable@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Unique Searchable Name",
            role=UserRole.USER,
        )
        db_session.add(user)
        await db_session.commit()
        
        # Search by name
        response = await async_client.get(
            "/api/v1/users?search=Searchable",
            headers=admin_token_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        emails = [u["email"] for u in data["users"]]
        assert "searchable@example.com" in emails


class TestCreateUser:
    """Test POST /users endpoint (admin only)."""
    
    @pytest.mark.asyncio
    async def test_admin_can_create_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        admin_token_headers: dict,
    ):
        """Test that admin can create new users."""
        user_data = {
            "email": "newuser@example.com",
            "password": "securepass123",
            "full_name": "New User",
            "role": "user",
        }
        
        response = await async_client.post(
            "/api/v1/users",
            headers=admin_token_headers,
            json=user_data,
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["role"] == user_data["role"]
        assert "password" not in data
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_user(
        self,
        async_client: AsyncClient,
        user_token_headers: dict,
    ):
        """Test that regular user cannot create users."""
        user_data = {
            "email": "blocked@example.com",
            "password": "securepass123",
            "full_name": "Blocked User",
            "role": "user",
        }
        
        response = await async_client.post(
            "/api/v1/users",
            headers=user_token_headers,
            json=user_data,
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self,
        async_client: AsyncClient,
        test_user: User,
        admin_token_headers: dict,
    ):
        """Test that duplicate email is rejected."""
        user_data = {
            "email": test_user.email,
            "password": "securepass123",
            "full_name": "Duplicate Email",
            "role": "user",
        }
        
        response = await async_client.post(
            "/api/v1/users",
            headers=admin_token_headers,
            json=user_data,
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_regular_admin_cannot_create_admin_user(
        self,
        async_client: AsyncClient,
        admin_token_headers: dict,
    ):
        """Test that regular admin cannot create admin users."""
        user_data = {
            "email": "wannabeadmin@example.com",
            "password": "securepass123",
            "full_name": "Wannabe Admin",
            "role": "admin",
        }
        
        response = await async_client.post(
            "/api/v1/users",
            headers=admin_token_headers,
            json=user_data,
        )
        
        assert response.status_code == 403
        assert "super admin" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_super_admin_can_create_admin(
        self,
        async_client: AsyncClient,
        super_admin_token_headers: dict,
    ):
        """Test that super admin can create admin users."""
        user_data = {
            "email": "newadmin@example.com",
            "password": "securepass123",
            "full_name": "New Admin",
            "role": "admin",
        }
        
        response = await async_client.post(
            "/api/v1/users",
            headers=super_admin_token_headers,
            json=user_data,
        )
        
        assert response.status_code == 201
        assert response.json()["role"] == "admin"
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_email(
        self,
        async_client: AsyncClient,
        admin_token_headers: dict,
    ):
        """Test that invalid email format is rejected."""
        user_data = {
            "email": "notanemail",
            "password": "securepass123",
            "full_name": "Invalid Email",
            "role": "user",
        }
        
        response = await async_client.post(
            "/api/v1/users",
            headers=admin_token_headers,
            json=user_data,
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_user_weak_password(
        self,
        async_client: AsyncClient,
        admin_token_headers: dict,
    ):
        """Test that weak password is rejected."""
        user_data = {
            "email": "weakpass@example.com",
            "password": "123",  # Too short
            "full_name": "Weak Password",
            "role": "user",
        }
        
        response = await async_client.post(
            "/api/v1/users",
            headers=admin_token_headers,
            json=user_data,
        )
        
        assert response.status_code == 422


class TestUpdateUser:
    """Test PATCH /users/{user_id} endpoint (admin only)."""
    
    @pytest.mark.asyncio
    async def test_admin_can_update_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        admin_token_headers: dict,
    ):
        """Test that admin can update any user."""
        new_name = "Admin Updated Name"
        
        response = await async_client.patch(
            f"/api/v1/users/{test_user.id}",
            headers=admin_token_headers,
            json={"full_name": new_name},
        )
        
        assert response.status_code == 200
        assert response.json()["full_name"] == new_name
        
        await db_session.refresh(test_user)
        assert test_user.full_name == new_name
    
    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_other_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        user_token_headers: dict,
    ):
        """Test that regular user cannot update other users."""
        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Other User",
            role=UserRole.USER,
        )
        db_session.add(other_user)
        await db_session.commit()
        
        response = await async_client.patch(
            f"/api/v1/users/{other_user.id}",
            headers=user_token_headers,
            json={"full_name": "Hacked Name"},
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_can_deactivate_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        admin_token_headers: dict,
    ):
        """Test that admin can deactivate users."""
        response = await async_client.patch(
            f"/api/v1/users/{test_user.id}",
            headers=admin_token_headers,
            json={"is_active": False},
        )
        
        assert response.status_code == 200
        assert response.json()["is_active"] is False
        
        await db_session.refresh(test_user)
        assert test_user.is_active is False
    
    @pytest.mark.asyncio
    async def test_regular_admin_cannot_update_admin_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        admin_token_headers: dict,
    ):
        """Test that regular admin cannot modify admin users."""
        # Create another admin
        other_admin = User(
            email="otheradmin@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Other Admin",
            role=UserRole.ADMIN,
        )
        db_session.add(other_admin)
        await db_session.commit()
        
        response = await async_client.patch(
            f"/api/v1/users/{other_admin.id}",
            headers=admin_token_headers,
            json={"full_name": "Modified Admin"},
        )
        
        assert response.status_code == 403
        assert "super admin" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_super_admin_can_update_admin(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        super_admin_token_headers: dict,
    ):
        """Test that super admin can modify admin users."""
        # Create admin
        admin = User(
            email="updateableadmin@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Updateable Admin",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        
        new_name = "Super Admin Updated"
        response = await async_client.patch(
            f"/api/v1/users/{admin.id}",
            headers=super_admin_token_headers,
            json={"full_name": new_name},
        )
        
        assert response.status_code == 200
        assert response.json()["full_name"] == new_name
    
    @pytest.mark.asyncio
    async def test_admin_change_user_role(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        super_admin_token_headers: dict,
    ):
        """Test that super admin can change user roles."""
        response = await async_client.patch(
            f"/api/v1/users/{test_user.id}",
            headers=super_admin_token_headers,
            json={"role": "analyst"},
        )
        
        assert response.status_code == 200
        assert response.json()["role"] == "analyst"
        
        await db_session.refresh(test_user)
        assert test_user.role == UserRole.ANALYST
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_user(
        self,
        async_client: AsyncClient,
        admin_token_headers: dict,
    ):
        """Test updating non-existent user returns 404."""
        from uuid import uuid4
        
        fake_id = uuid4()
        response = await async_client.patch(
            f"/api/v1/users/{fake_id}",
            headers=admin_token_headers,
            json={"full_name": "Ghost User"},
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_admin_reset_user_password(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        admin_token_headers: dict,
    ):
        """Test that admin can reset user passwords."""
        new_password = "newadminsetpass123"
        
        response = await async_client.patch(
            f"/api/v1/users/{test_user.id}",
            headers=admin_token_headers,
            json={"password": new_password},
        )
        
        assert response.status_code == 200
        
        # Verify password was changed
        await db_session.refresh(test_user)
        from backend.core.security import verify_password
        assert verify_password(new_password, test_user.hashed_password)


class TestDeleteUser:
    """Test DELETE /users/{user_id} endpoint (super admin only)."""
    
    @pytest.mark.asyncio
    async def test_super_admin_can_delete_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        super_admin_token_headers: dict,
    ):
        """Test that super admin can delete users."""
        # Create user to delete
        user = User(
            email="todelete@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="To Delete",
            role=UserRole.USER,
        )
        db_session.add(user)
        await db_session.commit()
        
        user_id = user.id
        
        response = await async_client.delete(
            f"/api/v1/users/{user_id}",
            headers=super_admin_token_headers,
        )
        
        assert response.status_code == 204
        
        # Verify user is deleted
        from sqlalchemy import select
        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        deleted_user = result.scalar_one_or_none()
        
        assert deleted_user is None
    
    @pytest.mark.asyncio
    async def test_regular_admin_cannot_delete_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        admin_token_headers: dict,
    ):
        """Test that regular admin cannot delete users."""
        response = await async_client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=admin_token_headers,
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_cannot_delete_self(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        super_admin_token_headers: dict,
    ):
        """Test that users cannot delete their own account."""
        # Get super admin user
        from sqlalchemy import select
        stmt = select(User).where(User.role == UserRole.SUPER_ADMIN)
        result = await db_session.execute(stmt)
        super_admin = result.scalar_one()
        
        response = await async_client.delete(
            f"/api/v1/users/{super_admin.id}",
            headers=super_admin_token_headers,
        )
        
        assert response.status_code == 400
        assert "cannot delete your own account" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_user(
        self,
        async_client: AsyncClient,
        super_admin_token_headers: dict,
    ):
        """Test deleting non-existent user returns 404."""
        from uuid import uuid4
        
        fake_id = uuid4()
        response = await async_client.delete(
            f"/api/v1/users/{fake_id}",
            headers=super_admin_token_headers,
        )
        
        assert response.status_code == 404


class TestInvalidUpdates:
    """Test handling of invalid update requests."""
    
    @pytest.mark.asyncio
    async def test_update_with_invalid_json(
        self,
        async_client: AsyncClient,
        test_user: User,
        user_token_headers: dict,
    ):
        """Test that malformed JSON is rejected."""
        response = await async_client.patch(
            "/api/v1/users/me",
            headers=user_token_headers,
            content=b"{invalid json}",
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_update_with_invalid_field_types(
        self,
        async_client: AsyncClient,
        test_user: User,
        user_token_headers: dict,
    ):
        """Test that invalid field types are rejected."""
        response = await async_client.patch(
            "/api/v1/users/me",
            headers=user_token_headers,
            json={
                "is_active": "not_a_boolean",
                "role": 12345,
            },
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_update_with_invalid_email_format(
        self,
        async_client: AsyncClient,
        test_user: User,
        user_token_headers: dict,
    ):
        """Test that invalid email format is rejected."""
        response = await async_client.patch(
            "/api/v1/users/me",
            headers=user_token_headers,
            json={"email": "not-an-email"},
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_update_with_unknown_fields(
        self,
        async_client: AsyncClient,
        test_user: User,
        user_token_headers: dict,
    ):
        """Test that unknown fields are ignored."""
        response = await async_client.patch(
            "/api/v1/users/me",
            headers=user_token_headers,
            json={
                "full_name": "Valid Name",
                "unknown_field": "should be ignored",
                "another_unknown": 123,
            },
        )
        
        # Should succeed but ignore unknown fields
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Valid Name"
        assert "unknown_field" not in data