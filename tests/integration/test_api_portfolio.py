"""
Family Office Platform - Portfolio API Integration Tests

Tests for portfolio management endpoints.
"""

import pytest
import json


class TestPortfolioAPI:
    """Integration tests for portfolio endpoints."""

    def test_get_portfolio_summary(self, client, sample_user, sample_assets, sample_real_estate, auth_headers, db_session):
        """Test getting portfolio summary."""
        response = client.get('/api/v1/portfolio/summary',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'net_worth' in data['data']
        assert 'total_assets' in data['data']
        assert 'breakdown' in data['data']

    def test_get_portfolio_summary_unauthorized(self, client, db_session):
        """Test getting summary without auth fails."""
        response = client.get('/api/v1/portfolio/summary')

        assert response.status_code == 401

    def test_get_portfolio_performance(self, client, sample_user, sample_assets, auth_headers, db_session):
        """Test getting portfolio performance."""
        response = client.get('/api/v1/portfolio/performance?period=1Y',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['period'] == '1Y'

    def test_get_portfolio_performance_invalid_period(self, client, auth_headers, db_session):
        """Test getting performance with invalid period."""
        response = client.get('/api/v1/portfolio/performance?period=INVALID',
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_get_holdings(self, client, sample_user, sample_assets, auth_headers, db_session):
        """Test getting asset holdings."""
        response = client.get('/api/v1/portfolio/holdings',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert len(data['data']) == len(sample_assets)

    def test_get_holdings_filtered(self, client, sample_user, sample_assets, auth_headers, db_session):
        """Test getting holdings filtered by asset type."""
        response = client.get('/api/v1/portfolio/holdings?asset_type=stock',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        # Should only return stocks
        for holding in data['data']:
            assert holding['asset_type'] == 'stock'

    def test_get_accounts(self, client, sample_user, sample_account, auth_headers, db_session):
        """Test getting accounts."""
        response = client.get('/api/v1/portfolio/accounts',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert len(data['data']) >= 1

    def test_get_real_estate(self, client, sample_user, sample_real_estate, auth_headers, db_session):
        """Test getting real estate holdings."""
        response = client.get('/api/v1/portfolio/real-estate',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert len(data['data']) == len(sample_real_estate)

    def test_calculate_rebalancing(self, client, sample_user, sample_assets, auth_headers, db_session):
        """Test calculating rebalancing recommendations."""
        response = client.post('/api/v1/portfolio/rebalance',
            headers=auth_headers,
            json={}  # Send empty JSON body
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'current_allocation' in data['data']
        assert 'target_allocation' in data['data']

    def test_calculate_rebalancing_custom_target(self, client, sample_user, sample_assets, auth_headers, db_session):
        """Test calculating rebalancing with custom target."""
        response = client.post('/api/v1/portfolio/rebalance',
            data=json.dumps({
                'target_allocation': {
                    'stocks': 0.50,
                    'bonds': 0.30,
                    'real_estate': 0.20
                }
            }),
            headers=auth_headers,
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'

    def test_get_allocation(self, client, sample_user, sample_assets, auth_headers, db_session):
        """Test getting asset allocation."""
        response = client.get('/api/v1/portfolio/allocation',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'allocation' in data['data']
        assert 'total_assets' in data['data']

    def test_get_portfolio_data(self, client, sample_user, sample_assets, sample_real_estate, auth_headers, db_session):
        """Test getting comprehensive portfolio data."""
        response = client.get('/api/v1/portfolio/data',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'total_value' in data['data'] or 'net_worth' in data['data']
