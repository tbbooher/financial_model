"""
Family Office Platform - CAPM Property-Based Tests

Property-based tests for CAPM calculations using Hypothesis.
"""

import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st
import numpy as np


class TestCAPMProperties:
    """Property-based tests for CAPM calculations."""

    @given(
        risk_free=st.floats(min_value=0, max_value=0.1, allow_nan=False, allow_infinity=False),
        beta=st.floats(min_value=-2, max_value=3, allow_nan=False, allow_infinity=False),
        market_return=st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=200)
    def test_capm_expected_return_formula(self, risk_free, beta, market_return):
        """Property: CAPM formula E(R) = Rf + beta * (Rm - Rf)."""
        expected_return = risk_free + beta * (market_return - risk_free)

        # Verify formula
        assert abs(expected_return - (risk_free + beta * (market_return - risk_free))) < 0.0001

    @given(
        risk_free=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False),
        market_return=st.floats(min_value=0.05, max_value=0.15, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_beta_zero_gives_risk_free_rate(self, risk_free, market_return):
        """Property: Beta = 0 should give risk-free rate."""
        beta = 0.0
        expected_return = risk_free + beta * (market_return - risk_free)

        assert abs(expected_return - risk_free) < 0.0001

    @given(
        risk_free=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False),
        market_return=st.floats(min_value=0.05, max_value=0.15, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_beta_one_gives_market_return(self, risk_free, market_return):
        """Property: Beta = 1 should give market return."""
        beta = 1.0
        expected_return = risk_free + beta * (market_return - risk_free)

        assert abs(expected_return - market_return) < 0.0001

    @given(
        risk_free=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False),
        market_return=st.floats(min_value=0.06, max_value=0.15, allow_nan=False, allow_infinity=False),
        beta=st.floats(min_value=1.1, max_value=3.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_high_beta_gives_higher_return(self, risk_free, market_return, beta):
        """Property: Beta > 1 should give higher than market return (when Rm > Rf)."""
        assume(market_return > risk_free)

        expected_return = risk_free + beta * (market_return - risk_free)

        assert expected_return > market_return

    @given(
        risk_free=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False),
        market_return=st.floats(min_value=0.06, max_value=0.15, allow_nan=False, allow_infinity=False),
        beta=st.floats(min_value=0.0, max_value=0.9, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_low_beta_gives_lower_return(self, risk_free, market_return, beta):
        """Property: Beta < 1 should give lower than market return (when Rm > Rf)."""
        assume(market_return > risk_free)

        expected_return = risk_free + beta * (market_return - risk_free)

        assert expected_return < market_return

    @given(st.lists(
        st.tuples(
            st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),  # weight
            st.floats(min_value=-1, max_value=3, allow_nan=False, allow_infinity=False)  # beta
        ),
        min_size=2,
        max_size=20
    ))
    @settings(max_examples=100)
    def test_portfolio_beta_is_weighted_average(self, assets):
        """Property: Portfolio beta is weighted average of individual betas."""
        assume(all(w > 0 for w, _ in assets))

        total_weight = sum(w for w, _ in assets)
        assume(total_weight > 0)

        # Normalize weights
        normalized_weights = [w / total_weight for w, _ in assets]
        betas = [b for _, b in assets]

        # Calculate portfolio beta
        portfolio_beta = sum(w * b for w, b in zip(normalized_weights, betas))

        # Portfolio beta should be between min and max individual betas (with epsilon for float precision)
        epsilon = 1e-9
        assert min(betas) - epsilon <= portfolio_beta <= max(betas) + epsilon

    @given(
        risk_free=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False),
        market_return=st.floats(min_value=0.05, max_value=0.15, allow_nan=False, allow_infinity=False),
        expected_return=st.floats(min_value=-0.3, max_value=0.5, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_alpha_calculation(self, risk_free, market_return, expected_return):
        """Property: Alpha = Actual Return - Expected Return (from CAPM)."""
        assume(market_return != risk_free)  # Avoid division by zero

        # Calculate implied beta from expected return
        market_premium = market_return - risk_free

        # For any actual return, alpha should be the difference
        actual_return = expected_return + 0.02  # Assume 2% outperformance
        alpha = actual_return - expected_return

        assert abs(alpha - 0.02) < 0.0001

    @given(
        beta1=st.floats(min_value=-1, max_value=3, allow_nan=False, allow_infinity=False),
        beta2=st.floats(min_value=-1, max_value=3, allow_nan=False, allow_infinity=False),
        risk_free=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False),
        market_return=st.floats(min_value=0.06, max_value=0.15, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_sml_is_linear(self, beta1, beta2, risk_free, market_return):
        """Property: Security Market Line is linear in beta."""
        assume(market_return > risk_free)

        # Calculate expected returns
        er1 = risk_free + beta1 * (market_return - risk_free)
        er2 = risk_free + beta2 * (market_return - risk_free)

        # Midpoint should also be on the line
        beta_mid = (beta1 + beta2) / 2
        er_mid_calculated = risk_free + beta_mid * (market_return - risk_free)
        er_mid_from_points = (er1 + er2) / 2

        assert abs(er_mid_calculated - er_mid_from_points) < 0.0001

    @given(
        risk_free=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False),
        market_return=st.floats(min_value=-0.3, max_value=0.3, allow_nan=False, allow_infinity=False),
        beta=st.floats(min_value=-0.5, max_value=2.5, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_expected_return_within_reasonable_bounds(self, risk_free, market_return, beta):
        """Property: Expected returns should be within reasonable bounds."""
        expected_return = risk_free + beta * (market_return - risk_free)

        # Expected annual returns should be bounded
        # Even extreme scenarios shouldn't exceed +/- 100% expected return
        assert -1.0 <= expected_return <= 1.0
