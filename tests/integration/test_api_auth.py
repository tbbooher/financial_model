"""
Family Office Platform - Authentication API Integration Tests

Tests for authentication endpoints.
"""

import pytest
import json


class TestAuthAPI:
    """Integration tests for authentication endpoints."""

    def test_register_success(self, client, db_session):
        """Test successful user registration."""
        response = client.post('/api/v1/auth/register',
            data=json.dumps({
                'email': 'newuser@example.com',
                'password': 'SecurePassword123!',
                'first_name': 'New',
                'last_name': 'User'
            }),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'tokens' in data['data']
        assert 'access_token' in data['data']['tokens']

    def test_register_duplicate_email(self, client, sample_user, db_session):
        """Test registration with existing email fails."""
        response = client.post('/api/v1/auth/register',
            data=json.dumps({
                'email': 'test@example.com',  # Same as sample_user
                'password': 'AnotherPassword123!'
            }),
            content_type='application/json'
        )

        assert response.status_code == 409

    def test_register_invalid_email(self, client, db_session):
        """Test registration with invalid email fails."""
        response = client.post('/api/v1/auth/register',
            data=json.dumps({
                'email': 'invalid-email',
                'password': 'SecurePassword123!'
            }),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_register_weak_password(self, client, db_session):
        """Test registration with weak password fails."""
        response = client.post('/api/v1/auth/register',
            data=json.dumps({
                'email': 'user@example.com',
                'password': 'weak'
            }),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_login_success(self, client, sample_user, db_session):
        """Test successful login."""
        response = client.post('/api/v1/auth/login',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'TestPassword123!'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'tokens' in data['data']

    def test_login_wrong_password(self, client, sample_user, db_session):
        """Test login with wrong password fails."""
        response = client.post('/api/v1/auth/login',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'WrongPassword123!'
            }),
            content_type='application/json'
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client, db_session):
        """Test login with non-existent user fails."""
        response = client.post('/api/v1/auth/login',
            data=json.dumps({
                'email': 'nonexistent@example.com',
                'password': 'Password123!'
            }),
            content_type='application/json'
        )

        assert response.status_code == 401

    def test_get_current_user(self, client, sample_user, auth_headers, db_session):
        """Test getting current user info."""
        response = client.get('/api/v1/auth/me',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['data']['email'] == 'test@example.com'

    def test_get_current_user_unauthorized(self, client, db_session):
        """Test getting current user without auth fails."""
        response = client.get('/api/v1/auth/me')

        assert response.status_code == 401

    def test_update_profile(self, client, sample_user, auth_headers, db_session):
        """Test updating user profile."""
        response = client.put('/api/v1/auth/me',
            data=json.dumps({
                'first_name': 'Updated',
                'last_name': 'Name'
            }),
            content_type='application/json',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['first_name'] == 'Updated'

    def test_change_password(self, client, sample_user, auth_headers, db_session):
        """Test changing password."""
        response = client.post('/api/v1/auth/change-password',
            data=json.dumps({
                'current_password': 'TestPassword123!',
                'new_password': 'NewSecurePassword456!'
            }),
            content_type='application/json',
            headers=auth_headers
        )

        assert response.status_code == 200

        # Verify new password works
        login_response = client.post('/api/v1/auth/login',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'NewSecurePassword456!'
            }),
            content_type='application/json'
        )
        assert login_response.status_code == 200

    def test_refresh_token(self, client, sample_user, app, db_session):
        """Test token refresh."""
        from flask_jwt_extended import create_refresh_token

        with app.app_context():
            refresh_token = create_refresh_token(identity=str(sample_user.id))

        response = client.post('/api/v1/auth/refresh',
            headers={'Authorization': f'Bearer {refresh_token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data['data']

    def test_logout(self, client, auth_headers, db_session):
        """Test logout endpoint."""
        response = client.post('/api/v1/auth/logout',
            headers=auth_headers
        )

        assert response.status_code == 200
