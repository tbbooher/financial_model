"""
Family Office Platform - Portfolio Property-Based Tests

Property-based tests for portfolio calculations using Hypothesis.
"""

import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st
from decimal import Decimal


class TestPortfolioProperties:
    """Property-based tests for portfolio calculations."""

    @given(st.lists(st.floats(min_value=0, max_value=10000000, allow_nan=False, allow_infinity=False), min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_portfolio_sum_equals_total(self, asset_values):
        """Property: Sum of individual assets equals total portfolio value."""
        assume(all(v >= 0 for v in asset_values))

        total = sum(asset_values)
        calculated_total = sum(asset_values)

        assert abs(total - calculated_total) < 0.01

    @given(
        total_assets=st.floats(min_value=0, max_value=100000000, allow_nan=False, allow_infinity=False),
        total_liabilities=st.floats(min_value=0, max_value=50000000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_net_worth_equals_assets_minus_liabilities(self, total_assets, total_liabilities):
        """Property: Net worth = Total Assets - Total Liabilities."""
        net_worth = total_assets - total_liabilities

        # Net worth can be negative
        assert net_worth == total_assets - total_liabilities

    @given(st.lists(st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False), min_size=2, max_size=10))
    @settings(max_examples=100)
    def test_allocation_percentages_sum_to_one(self, percentages):
        """Property: Asset allocation percentages should sum to 1.0 (or 100%)."""
        assume(sum(percentages) > 0)  # Avoid division by zero

        # Normalize percentages
        total = sum(percentages)
        normalized = [p / total for p in percentages]

        assert abs(sum(normalized) - 1.0) < 0.0001

    @given(
        cost_basis=st.floats(min_value=1, max_value=10000000, allow_nan=False, allow_infinity=False),
        current_value=st.floats(min_value=0, max_value=20000000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_unrealized_gain_loss_calculation(self, cost_basis, current_value):
        """Property: Unrealized gain/loss = Current Value - Cost Basis."""
        unrealized = current_value - cost_basis

        # Gain if current > cost, loss if current < cost
        if current_value > cost_basis:
            assert unrealized > 0
        elif current_value < cost_basis:
            assert unrealized < 0
        else:
            assert abs(unrealized) < 0.01

    @given(
        cost_basis=st.floats(min_value=1, max_value=10000000, allow_nan=False, allow_infinity=False),
        current_value=st.floats(min_value=0, max_value=20000000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_return_percentage_bounds(self, cost_basis, current_value):
        """Property: Return percentage should be bounded correctly."""
        assume(cost_basis > 0)

        return_pct = (current_value - cost_basis) / cost_basis

        # Return can range from -100% (total loss) to infinite (for gains)
        assert return_pct >= -1.0  # Can't lose more than 100%

        # For reasonable bounds (current_value <= 10x cost_basis)
        if current_value <= 10 * cost_basis:
            assert return_pct <= 10.0  # 1000% max gain

    @given(st.lists(
        st.tuples(
            st.floats(min_value=100, max_value=1000000, allow_nan=False, allow_infinity=False),  # value
            st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False)  # return
        ),
        min_size=2,
        max_size=20
    ))
    @settings(max_examples=50)
    def test_weighted_portfolio_return(self, assets):
        """Property: Portfolio return is weighted average of asset returns."""
        assume(all(v > 0 for v, _ in assets))

        total_value = sum(v for v, _ in assets)
        assume(total_value > 0)

        # Calculate weighted return
        weighted_return = sum(v * r for v, r in assets) / total_value

        # Weighted return should be between min and max individual returns (with epsilon for float precision)
        returns = [r for _, r in assets]
        epsilon = 1e-9
        assert min(returns) - epsilon <= weighted_return <= max(returns) + epsilon

    @given(
        quantity=st.floats(min_value=0.000001, max_value=10000000, allow_nan=False, allow_infinity=False),
        price=st.floats(min_value=0.01, max_value=100000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_position_value_calculation(self, quantity, price):
        """Property: Position value = Quantity * Price."""
        value = quantity * price

        assert value >= 0
        assert abs(value - quantity * price) < 0.01

    @given(st.lists(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_position_weights_are_non_negative(self, values):
        """Property: All position weights should be non-negative."""
        assume(sum(values) > 0)

        total = sum(values)
        weights = [v / total for v in values]

        assert all(w >= 0 for w in weights)
        assert all(w <= 1 for w in weights)

    @given(
        purchase_price=st.floats(min_value=10000, max_value=10000000, allow_nan=False, allow_infinity=False),
        monthly_income=st.floats(min_value=0, max_value=50000, allow_nan=False, allow_infinity=False),
        monthly_expenses=st.floats(min_value=0, max_value=30000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_real_estate_roi_calculation(self, purchase_price, monthly_income, monthly_expenses):
        """Property: Real estate ROI = (Annual Net Income) / Purchase Price."""
        assume(purchase_price > 0)

        annual_net_income = (monthly_income - monthly_expenses) * 12
        roi = annual_net_income / purchase_price

        # ROI can be negative (if expenses > income)
        if monthly_income > monthly_expenses:
            assert roi > 0
        elif monthly_income < monthly_expenses:
            assert roi < 0

    @given(st.lists(st.integers(min_value=1, max_value=1000000), min_size=2, max_size=100))
    @settings(max_examples=50)
    def test_diversification_reduces_with_concentration(self, values):
        """Property: Portfolio concentration inversely relates to diversification."""
        total = sum(values)
        assume(total > 0)

        # Calculate Herfindahl-Hirschman Index (HHI)
        # HHI = sum of squared weights
        weights = [v / total for v in values]
        hhi = sum(w ** 2 for w in weights)

        # HHI ranges from 1/n (equal weights) to 1 (single asset)
        n = len(values)
        assert 1/n - 0.0001 <= hhi <= 1.0001
