"""
Family Office Platform - Quant Analyst Agent

Quantitative analysis agent for mathematical modeling, Monte Carlo simulations,
factor analysis, and quantitative strategy development.
"""

import numpy as np
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List

from flask import current_app

from app.agents.base_agent import BaseAgent, AgentResponse
from app.services.capm_service import CAPMService
from app.services.risk_service import RiskService


class QuantAnalyst(BaseAgent):
    """
    Quantitative Analyst Agent.

    Can operate in two specialties:
    - risk_modeling: Advanced risk calculations and modeling
    - strategy_development: Quantitative strategy development

    Responsibilities:
    - CAPM analysis and beta calculations
    - Monte Carlo simulations for portfolio outcomes
    - Risk factor modeling
    - Quantitative strategy development
    - Statistical arbitrage opportunities
    - Performance attribution using factor models
    """

    def __init__(
        self,
        user_id: str,
        portfolio_data: Dict[str, Any],
        specialty: str = 'risk_modeling'
    ):
        """
        Initialize Quant Analyst agent.

        Args:
            user_id: User ID
            portfolio_data: Portfolio data
            specialty: 'risk_modeling' or 'strategy_development'
        """
        super().__init__(user_id, portfolio_data)
        self.specialty = specialty
        self.capm_service = CAPMService()
        self.risk_service = RiskService(portfolio_data)

    def analyze(self) -> AgentResponse:
        """
        Perform quantitative analysis based on specialty.

        Returns:
            AgentResponse with quant analysis results
        """
        try:
            self.logger.info(f"Starting Quant ({self.specialty}) analysis for user {self.user_id}")

            if self.specialty == 'risk_modeling':
                return self._perform_risk_modeling()
            else:
                return self._perform_strategy_development()

        except Exception as e:
            self.logger.error(f"Quant analysis failed: {str(e)}")
            raise

    def _perform_risk_modeling(self) -> AgentResponse:
        """Perform risk modeling analysis."""
        # Comprehensive risk analysis
        var_analysis = self._perform_var_analysis()
        monte_carlo = self._perform_monte_carlo_analysis()
        factor_analysis = self._perform_factor_analysis()
        stress_test = self._perform_stress_testing()
        correlation = self._perform_correlation_analysis()

        recommendations = self.get_recommendations()

        confidence_factors = {
            'data_quality': self._assess_data_quality(),
            'model_stability': 0.85,
            'sample_size': self._assess_sample_size()
        }

        reasoning = self._generate_risk_reasoning(
            var_analysis, monte_carlo, stress_test
        )

        return AgentResponse(
            agent_type=f'{self.agent_type}_risk',
            recommendations=recommendations,
            confidence_score=self._calculate_confidence(confidence_factors),
            reasoning=reasoning,
            data_sources=['price_history', 'risk_models', 'factor_data', 'correlation_matrix'],
            metadata={
                'var_analysis': var_analysis,
                'monte_carlo_simulation': monte_carlo,
                'factor_analysis': factor_analysis,
                'stress_test': stress_test,
                'correlation_analysis': correlation
            }
        )

    def _perform_strategy_development(self) -> AgentResponse:
        """Perform strategy development analysis."""
        # Strategy analysis
        momentum_analysis = self._analyze_momentum()
        value_analysis = self._analyze_value_factors()
        optimization = self._perform_optimization()
        backtest = self._perform_backtest_analysis()

        recommendations = self._get_strategy_recommendations()

        confidence_factors = {
            'data_quality': self._assess_data_quality(),
            'backtest_validity': 0.75,
            'market_regime': 0.8
        }

        reasoning = self._generate_strategy_reasoning(
            momentum_analysis, value_analysis, optimization
        )

        return AgentResponse(
            agent_type=f'{self.agent_type}_strategy',
            recommendations=recommendations,
            confidence_score=self._calculate_confidence(confidence_factors),
            reasoning=reasoning,
            data_sources=['price_history', 'fundamental_data', 'factor_models', 'backtest_results'],
            metadata={
                'momentum_analysis': momentum_analysis,
                'value_analysis': value_analysis,
                'optimization_results': optimization,
                'backtest_analysis': backtest
            }
        )

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations based on specialty."""
        if self.specialty == 'risk_modeling':
            return self._get_risk_recommendations()
        else:
            return self._get_strategy_recommendations()

    def _perform_var_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive VaR analysis."""
        # Multiple VaR methodologies
        var_historical_95 = self.risk_service.calculate_var(
            confidence_level=0.95, method='historical'
        )
        var_historical_99 = self.risk_service.calculate_var(
            confidence_level=0.99, method='historical'
        )
        var_parametric_95 = self.risk_service.calculate_var(
            confidence_level=0.95, method='parametric'
        )
        var_monte_carlo_95 = self.risk_service.calculate_var(
            confidence_level=0.95, method='monte_carlo'
        )

        # CVaR (Expected Shortfall)
        cvar_95 = self.risk_service.calculate_cvar(confidence_level=0.95)
        cvar_99 = self.risk_service.calculate_cvar(confidence_level=0.99)

        return {
            'var_95': {
                'historical': var_historical_95,
                'parametric': var_parametric_95,
                'monte_carlo': var_monte_carlo_95
            },
            'var_99': var_historical_99,
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            'model_comparison': {
                'historical_vs_parametric': abs(
                    var_historical_95.get('var_percentage', 0) -
                    var_parametric_95.get('var_percentage', 0)
                ),
                'model_agreement': 'good' if abs(
                    var_historical_95.get('var_percentage', 0) -
                    var_parametric_95.get('var_percentage', 0)
                ) < 0.5 else 'divergent'
            }
        }

    def _perform_monte_carlo_analysis(self) -> Dict[str, Any]:
        """Perform Monte Carlo portfolio simulation."""
        # Multiple time horizons
        mc_1y = self.risk_service.monte_carlo_simulation(
            time_horizon_years=1.0, simulations=10000
        )
        mc_5y = self.risk_service.monte_carlo_simulation(
            time_horizon_years=5.0, simulations=10000
        )
        mc_10y = self.risk_service.monte_carlo_simulation(
            time_horizon_years=10.0, simulations=10000
        )

        return {
            'one_year': mc_1y,
            'five_year': mc_5y,
            'ten_year': mc_10y,
            'wealth_trajectory': {
                'years': [1, 5, 10],
                'median_values': [
                    mc_1y.get('median_end_value', 0),
                    mc_5y.get('median_end_value', 0),
                    mc_10y.get('median_end_value', 0)
                ],
                'p5_values': [
                    mc_1y.get('percentiles', {}).get('p5', 0),
                    mc_5y.get('percentiles', {}).get('p5', 0),
                    mc_10y.get('percentiles', {}).get('p5', 0)
                ],
                'p95_values': [
                    mc_1y.get('percentiles', {}).get('p95', 0),
                    mc_5y.get('percentiles', {}).get('p95', 0),
                    mc_10y.get('percentiles', {}).get('p95', 0)
                ]
            }
        }

    def _perform_factor_analysis(self) -> Dict[str, Any]:
        """Perform factor analysis on portfolio."""
        # Simplified factor analysis
        # In production, would use multi-factor models (Fama-French, etc.)

        portfolio_beta = self.capm_service.calculate_portfolio_beta(self.portfolio_data)

        # Estimate factor exposures (simplified)
        factor_exposures = {
            'market': portfolio_beta,
            'size': 0.0,  # Would calculate SMB exposure
            'value': 0.0,  # Would calculate HML exposure
            'momentum': 0.0,  # Would calculate momentum factor
            'quality': 0.0,  # Would calculate quality factor
            'volatility': 0.0  # Would calculate low-vol factor
        }

        # Risk attribution
        market_risk_contribution = abs(portfolio_beta) * 0.16  # Assume 16% market vol
        idiosyncratic_risk = 0.05  # Assume 5% idiosyncratic

        return {
            'factor_exposures': factor_exposures,
            'risk_attribution': {
                'systematic_risk': round(market_risk_contribution * 100, 2),
                'idiosyncratic_risk': round(idiosyncratic_risk * 100, 2),
                'total_risk': round((market_risk_contribution + idiosyncratic_risk) * 100, 2)
            },
            'dominant_factor': 'market',
            'r_squared': 0.85  # How much variance explained by factors
        }

    def _perform_stress_testing(self) -> Dict[str, Any]:
        """Perform stress testing analysis."""
        stress_results = self.risk_service.stress_test()

        # Additional custom scenarios
        custom_scenarios = {
            'interest_rate_up_200bp': {'equity': -0.15, 'bonds': -0.08, 'real_estate': -0.10},
            'inflation_shock': {'equity': -0.12, 'bonds': -0.15, 'real_estate': 0.05},
            'stagflation': {'equity': -0.25, 'bonds': -0.10, 'real_estate': -0.15}
        }

        custom_results = self.risk_service.stress_test(scenarios=custom_scenarios)

        return {
            'standard_scenarios': stress_results,
            'custom_scenarios': custom_results,
            'worst_case_scenario': stress_results.get('worst_case'),
            'portfolio_resilience': self._assess_resilience(stress_results)
        }

    def _perform_correlation_analysis(self) -> Dict[str, Any]:
        """Perform correlation analysis."""
        return self.risk_service.correlation_analysis()

    def _analyze_momentum(self) -> Dict[str, Any]:
        """Analyze momentum factors in portfolio."""
        assets = self._get_assets()

        momentum_scores = []
        for asset in assets:
            # Use available return data
            return_1m = asset.get('return_1m', 0) or 0
            return_3m = asset.get('return_3m', 0) or 0
            return_1y = asset.get('return_1y', 0) or 0

            # Simple momentum score
            momentum = (return_1m * 0.3 + return_3m * 0.3 + return_1y * 0.4)

            momentum_scores.append({
                'symbol': asset.get('symbol', 'Unknown'),
                'momentum_score': round(momentum, 4),
                'return_1m': return_1m,
                'return_3m': return_3m,
                'return_1y': return_1y
            })

        # Sort by momentum
        momentum_scores.sort(key=lambda x: x['momentum_score'], reverse=True)

        return {
            'rankings': momentum_scores,
            'high_momentum': momentum_scores[:5] if momentum_scores else [],
            'low_momentum': momentum_scores[-5:] if momentum_scores else [],
            'portfolio_momentum': np.mean([m['momentum_score'] for m in momentum_scores]) if momentum_scores else 0
        }

    def _analyze_value_factors(self) -> Dict[str, Any]:
        """Analyze value factors in portfolio."""
        assets = self._get_assets()

        value_analysis = []
        for asset in assets:
            # Simplified value analysis
            unrealized_return = asset.get('return_percentage', 0)

            # If asset is down significantly, may be value opportunity
            value_score = -unrealized_return if unrealized_return else 0

            value_analysis.append({
                'symbol': asset.get('symbol', 'Unknown'),
                'value_score': round(value_score, 4),
                'unrealized_return': unrealized_return
            })

        value_analysis.sort(key=lambda x: x['value_score'], reverse=True)

        return {
            'rankings': value_analysis,
            'potential_value': value_analysis[:5] if value_analysis else [],
            'portfolio_value_tilt': np.mean([v['value_score'] for v in value_analysis]) if value_analysis else 0
        }

    def _perform_optimization(self) -> Dict[str, Any]:
        """Perform portfolio optimization analysis."""
        # Simplified mean-variance optimization
        # In production, would use scipy.optimize or cvxpy

        current_return = self.portfolio_data.get('performance', {}).get('total_return', 0.08)
        current_volatility = self.portfolio_data.get('performance', {}).get('volatility', 0.15)

        # Calculate current Sharpe
        risk_free = float(current_app.config.get('DEFAULT_RISK_FREE_RATE', 0.02))
        current_sharpe = (current_return - risk_free) / current_volatility if current_volatility > 0 else 0

        # Suggest optimal allocation (simplified)
        optimal_allocation = {
            'us_large_cap': 35,
            'us_small_cap': 10,
            'international_developed': 15,
            'emerging_markets': 5,
            'bonds': 25,
            'alternatives': 10
        }

        return {
            'current_metrics': {
                'expected_return': round(current_return, 4),
                'volatility': round(current_volatility, 4),
                'sharpe_ratio': round(current_sharpe, 4)
            },
            'optimized_allocation': optimal_allocation,
            'efficient_frontier': self._generate_efficient_frontier(),
            'recommendation': 'Consider rebalancing towards optimal allocation'
        }

    def _perform_backtest_analysis(self) -> Dict[str, Any]:
        """Perform backtest analysis on current allocation."""
        # Simplified backtest results
        # In production, would run actual historical simulation

        return {
            'backtest_period': '5 years',
            'annualized_return': 0.082,
            'annualized_volatility': 0.142,
            'sharpe_ratio': 0.44,
            'max_drawdown': -0.18,
            'win_rate': 0.58,
            'profit_factor': 1.35,
            'calmar_ratio': 0.46,
            'caveats': [
                'Past performance does not guarantee future results',
                'Backtest may suffer from survivorship bias',
                'Transaction costs not fully modeled'
            ]
        }

    def _get_risk_recommendations(self) -> List[Dict[str, Any]]:
        """Generate risk-focused recommendations."""
        recommendations = []

        var_analysis = self._perform_var_analysis()
        stress_test = self._perform_stress_testing()

        # VaR-based recommendations
        var_95_pct = abs(var_analysis['var_95']['historical'].get('var_percentage', 0))
        if var_95_pct > 3:
            recommendations.append(self._create_recommendation(
                rec_type='risk_reduction',
                priority='high',
                description=f'Portfolio VaR ({var_95_pct:.1f}%) exceeds typical tolerance',
                details={
                    'current_var': var_95_pct,
                    'suggested_threshold': 3.0
                },
                expected_impact='Reduce potential daily losses to acceptable levels'
            ))

        # Stress test recommendations
        worst_case = stress_test.get('worst_case_scenario')
        if worst_case:
            recommendations.append(self._create_recommendation(
                rec_type='stress_awareness',
                priority='medium',
                description=f'Worst case scenario ({worst_case}) shows significant impact',
                details={
                    'scenario': worst_case,
                    'results': stress_test['standard_scenarios']['scenarios'].get(worst_case, {})
                },
                expected_impact='Consider hedging strategies for tail risks'
            ))

        # Diversification recommendation
        recommendations.append(self._create_recommendation(
            rec_type='diversification_review',
            priority='low',
            description='Review portfolio diversification for risk reduction',
            details={
                'correlation_analysis': 'Included in metadata'
            },
            expected_impact='Improve risk-adjusted returns through diversification'
        ))

        return recommendations

    def _get_strategy_recommendations(self) -> List[Dict[str, Any]]:
        """Generate strategy-focused recommendations."""
        recommendations = []

        momentum = self._analyze_momentum()
        optimization = self._perform_optimization()

        # Momentum-based recommendations
        if momentum.get('high_momentum'):
            recommendations.append(self._create_recommendation(
                rec_type='momentum_strategy',
                priority='medium',
                description='High momentum positions identified',
                details={
                    'top_momentum': momentum['high_momentum'][:3]
                },
                expected_impact='Consider maintaining or increasing high momentum positions'
            ))

        # Optimization recommendations
        current_sharpe = optimization['current_metrics']['sharpe_ratio']
        if current_sharpe < 0.5:
            recommendations.append(self._create_recommendation(
                rec_type='portfolio_optimization',
                priority='high',
                description='Portfolio Sharpe ratio below optimal',
                details={
                    'current_sharpe': current_sharpe,
                    'target_sharpe': 0.5,
                    'suggested_allocation': optimization['optimized_allocation']
                },
                expected_impact='Improve risk-adjusted returns'
            ))

        return recommendations

    def _generate_efficient_frontier(self) -> Dict[str, Any]:
        """Generate efficient frontier data points."""
        # Simplified efficient frontier
        volatilities = np.linspace(0.05, 0.25, 20)
        returns = 0.02 + 0.4 * volatilities  # Simplified linear relationship

        return {
            'volatilities': volatilities.tolist(),
            'returns': returns.tolist(),
            'optimal_point': {
                'volatility': 0.12,
                'return': 0.068
            }
        }

    def _assess_resilience(self, stress_results: Dict[str, Any]) -> str:
        """Assess portfolio resilience to stress."""
        scenarios = stress_results.get('scenarios', {})
        if not scenarios:
            return 'unknown'

        avg_impact = np.mean([
            abs(s.get('impact_percentage', 0))
            for s in scenarios.values()
        ])

        if avg_impact < 15:
            return 'high'
        elif avg_impact < 25:
            return 'moderate'
        else:
            return 'low'

    def _assess_sample_size(self) -> float:
        """Assess adequacy of sample size for analysis."""
        assets = self._get_assets()
        if len(assets) < 5:
            return 0.5
        elif len(assets) < 10:
            return 0.7
        elif len(assets) < 20:
            return 0.85
        else:
            return 0.95

    def _generate_risk_reasoning(
        self,
        var: Dict[str, Any],
        monte_carlo: Dict[str, Any],
        stress: Dict[str, Any]
    ) -> str:
        """Generate risk modeling reasoning."""
        parts = []

        # VaR analysis
        var_95 = var['var_95']['historical'].get('var_percentage', 0)
        parts.append(f"Portfolio 95% VaR is {abs(var_95):.2f}%")

        # Monte Carlo
        mc_1y = monte_carlo['one_year']
        prob_loss = mc_1y.get('probability_of_loss', 0)
        parts.append(f"Monte Carlo simulation shows {prob_loss:.1f}% probability of loss over 1 year")

        # Stress testing
        resilience = stress.get('portfolio_resilience', 'unknown')
        parts.append(f"Portfolio resilience to stress scenarios: {resilience}")

        return ". ".join(parts) + "."

    def _generate_strategy_reasoning(
        self,
        momentum: Dict[str, Any],
        value: Dict[str, Any],
        optimization: Dict[str, Any]
    ) -> str:
        """Generate strategy development reasoning."""
        parts = []

        # Momentum
        portfolio_momentum = momentum.get('portfolio_momentum', 0)
        if portfolio_momentum > 0.05:
            parts.append("Portfolio has positive momentum exposure")
        elif portfolio_momentum < -0.05:
            parts.append("Portfolio has negative momentum - caution advised")
        else:
            parts.append("Portfolio momentum is neutral")

        # Optimization
        current_sharpe = optimization['current_metrics']['sharpe_ratio']
        parts.append(f"Current Sharpe ratio: {current_sharpe:.2f}")

        if current_sharpe < 0.5:
            parts.append("Optimization suggests room for improvement")

        return ". ".join(parts) + "."
