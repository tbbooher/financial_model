"""
Family Office Platform - CFA Agent

Chartered Financial Analyst agent for investment analysis,
portfolio metrics, and security recommendations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List

from flask import current_app

from app.agents.base_agent import BaseAgent, AgentResponse
from app.services.capm_service import CAPMService
from app.services.risk_service import RiskService


class CFAAgent(BaseAgent):
    """
    Chartered Financial Analyst Agent.

    Responsibilities:
    - Analyze portfolio allocation and risk metrics
    - Provide investment recommendations
    - Monitor market conditions and opportunities
    - Generate professional investment reports
    - Track performance against benchmarks
    """

    def __init__(self, user_id: str, portfolio_data: Dict[str, Any]):
        """Initialize CFA agent with CAPM and Risk services."""
        super().__init__(user_id, portfolio_data)
        self.capm_service = CAPMService()
        self.risk_service = RiskService(portfolio_data)

    def analyze(self) -> AgentResponse:
        """
        Perform comprehensive investment analysis.

        Returns:
            AgentResponse with investment analysis results
        """
        try:
            self.logger.info(f"Starting CFA analysis for user {self.user_id}")

            # Perform various analyses
            portfolio_metrics = self._calculate_portfolio_metrics()
            risk_analysis = self._perform_risk_analysis()
            capm_analysis = self._perform_capm_analysis()
            allocation_analysis = self._analyze_allocation()

            # Generate recommendations
            recommendations = self.get_recommendations()

            # Calculate confidence
            confidence_factors = {
                'data_quality': self._assess_data_quality(),
                'market_stability': self._assess_market_conditions(),
                'portfolio_size': min(self._get_portfolio_value() / 1000000, 1.0),
                'diversification': self._assess_diversification()
            }

            # Generate reasoning
            reasoning = self._generate_analysis_reasoning(
                portfolio_metrics, risk_analysis, capm_analysis
            )

            self._log_analysis('comprehensive_investment_analysis', {
                'metrics': portfolio_metrics,
                'risk': risk_analysis,
                'capm': capm_analysis
            })

            return AgentResponse(
                agent_type=self.agent_type,
                recommendations=recommendations,
                confidence_score=self._calculate_confidence(confidence_factors),
                reasoning=reasoning,
                data_sources=['market_data', 'portfolio_holdings', 'risk_models', 'capm_model'],
                metadata={
                    'portfolio_metrics': portfolio_metrics,
                    'risk_analysis': risk_analysis,
                    'capm_analysis': capm_analysis,
                    'allocation_analysis': allocation_analysis
                }
            )

        except Exception as e:
            self.logger.error(f"CFA analysis failed: {str(e)}")
            raise

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate investment recommendations.

        Returns:
            List of investment recommendations
        """
        recommendations = []

        # Check allocation and rebalancing needs
        allocation_recs = self._generate_allocation_recommendations()
        recommendations.extend(allocation_recs)

        # Check individual securities
        security_recs = self._generate_security_recommendations()
        recommendations.extend(security_recs)

        # Check risk exposure
        risk_recs = self._generate_risk_recommendations()
        recommendations.extend(risk_recs)

        # Sort by priority
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))

        return recommendations

    def _calculate_portfolio_metrics(self) -> Dict[str, float]:
        """Calculate key portfolio performance metrics."""
        try:
            # Get return data
            total_return = self._calculate_total_return()
            volatility = self._calculate_volatility()

            # Calculate risk-adjusted metrics
            risk_free_rate = float(current_app.config.get('DEFAULT_RISK_FREE_RATE', 0.02))
            sharpe_ratio = self.risk_service.calculate_sharpe_ratio()

            # Get beta from CAPM
            portfolio_beta = self.capm_service.calculate_portfolio_beta(self.portfolio_data)

            # Calculate alpha (Jensen's Alpha)
            expected_return = self.capm_service.calculate_expected_return(portfolio_beta)
            alpha = total_return - expected_return

            # Calculate Treynor ratio
            treynor_ratio = self.risk_service.calculate_treynor_ratio(beta=portfolio_beta)

            # Get max drawdown
            drawdown_data = self.risk_service.calculate_max_drawdown()

            return {
                'total_return_1y': round(total_return, 4),
                'volatility': round(volatility, 4),
                'sharpe_ratio': round(sharpe_ratio, 4),
                'beta': round(portfolio_beta, 4),
                'alpha': round(alpha, 4),
                'treynor_ratio': round(treynor_ratio, 4),
                'max_drawdown': drawdown_data.get('max_drawdown', 0),
                'information_ratio': self._calculate_information_ratio()
            }

        except Exception as e:
            self.logger.warning(f"Error calculating portfolio metrics: {e}")
            return {
                'total_return_1y': 0.0,
                'volatility': 0.15,
                'sharpe_ratio': 0.0,
                'beta': 1.0,
                'alpha': 0.0,
                'treynor_ratio': 0.0,
                'max_drawdown': 0.0,
                'information_ratio': 0.0
            }

    def _perform_risk_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive risk analysis."""
        try:
            var_95 = self.risk_service.calculate_var(confidence_level=0.95)
            var_99 = self.risk_service.calculate_var(confidence_level=0.99)
            cvar = self.risk_service.calculate_cvar(confidence_level=0.95)

            return {
                'var_95': var_95,
                'var_99': var_99,
                'cvar_95': cvar,
                'risk_level': self._determine_risk_level()
            }
        except Exception as e:
            self.logger.warning(f"Error in risk analysis: {e}")
            return {
                'var_95': {'var_percentage': 0},
                'var_99': {'var_percentage': 0},
                'cvar_95': {'cvar_percentage': 0},
                'risk_level': 'unknown'
            }

    def _perform_capm_analysis(self) -> Dict[str, Any]:
        """Perform CAPM analysis on portfolio."""
        try:
            portfolio_beta = self.capm_service.calculate_portfolio_beta(self.portfolio_data)
            expected_return = self.capm_service.calculate_expected_return(portfolio_beta)
            sml = self.capm_service.generate_security_market_line()
            asset_analysis = self.capm_service.analyze_asset_pricing(self.portfolio_data)

            return {
                'portfolio_beta': portfolio_beta,
                'expected_return': expected_return,
                'security_market_line': sml,
                'asset_pricing_analysis': asset_analysis
            }
        except Exception as e:
            self.logger.warning(f"Error in CAPM analysis: {e}")
            return {
                'portfolio_beta': 1.0,
                'expected_return': 0.08,
                'security_market_line': {},
                'asset_pricing_analysis': []
            }

    def _analyze_allocation(self) -> Dict[str, Any]:
        """Analyze current asset allocation."""
        allocation = self.portfolio_data.get('asset_allocation', {}) or \
                    self.portfolio_data.get('breakdown', {})

        total_value = self._get_portfolio_value()

        # Calculate percentages
        allocation_pct = {}
        for asset_type, value in allocation.items():
            if total_value > 0:
                allocation_pct[asset_type] = round(value / total_value * 100, 2)

        # Determine target based on risk tolerance
        risk_tolerance = self._get_risk_tolerance()
        target_allocation = self._get_target_allocation(risk_tolerance)

        # Calculate drift
        drift = {}
        for asset_type in set(list(allocation_pct.keys()) + list(target_allocation.keys())):
            current = allocation_pct.get(asset_type, 0)
            target = target_allocation.get(asset_type, 0)
            drift[asset_type] = round(current - target, 2)

        return {
            'current': allocation_pct,
            'target': target_allocation,
            'drift': drift,
            'needs_rebalancing': any(abs(d) > 5 for d in drift.values())
        }

    def _generate_allocation_recommendations(self) -> List[Dict[str, Any]]:
        """Generate allocation-based recommendations."""
        recommendations = []
        allocation_analysis = self._analyze_allocation()

        if allocation_analysis['needs_rebalancing']:
            drift = allocation_analysis['drift']
            significant_drifts = {k: v for k, v in drift.items() if abs(v) > 5}

            if significant_drifts:
                recommendations.append(self._create_recommendation(
                    rec_type='rebalancing',
                    priority='high',
                    description='Portfolio rebalancing recommended due to allocation drift',
                    details={
                        'current_allocation': allocation_analysis['current'],
                        'target_allocation': allocation_analysis['target'],
                        'drift': significant_drifts
                    },
                    expected_impact='Reduce risk and maintain target risk profile'
                ))

        return recommendations

    def _generate_security_recommendations(self) -> List[Dict[str, Any]]:
        """Generate individual security recommendations."""
        recommendations = []

        try:
            # Get CAPM-based analysis
            capm_analysis = self.capm_service.analyze_asset_pricing(self.portfolio_data)

            undervalued = []
            overvalued = []

            for asset in capm_analysis:
                if 'error' in asset:
                    continue

                valuation = asset.get('valuation', 'fairly_valued')
                if valuation in ['undervalued', 'significantly_undervalued']:
                    undervalued.append(asset)
                elif valuation in ['overvalued', 'significantly_overvalued']:
                    overvalued.append(asset)

            if overvalued:
                recommendations.append(self._create_recommendation(
                    rec_type='security_review',
                    priority='medium',
                    description=f'Review {len(overvalued)} potentially overvalued positions',
                    details={
                        'overvalued_securities': [
                            {'symbol': a['symbol'], 'alpha': a.get('alpha', 0)}
                            for a in overvalued
                        ]
                    },
                    expected_impact='Potential reallocation to better-valued securities'
                ))

            if undervalued:
                recommendations.append(self._create_recommendation(
                    rec_type='opportunity',
                    priority='low',
                    description=f'{len(undervalued)} holdings appear undervalued per CAPM',
                    details={
                        'undervalued_securities': [
                            {'symbol': a['symbol'], 'alpha': a.get('alpha', 0)}
                            for a in undervalued
                        ]
                    },
                    expected_impact='Consider increasing allocation to undervalued positions'
                ))

        except Exception as e:
            self.logger.warning(f"Error generating security recommendations: {e}")

        return recommendations

    def _generate_risk_recommendations(self) -> List[Dict[str, Any]]:
        """Generate risk-based recommendations."""
        recommendations = []

        risk_level = self._determine_risk_level()
        risk_tolerance = self._get_risk_tolerance()

        # Check if risk level matches tolerance
        risk_mismatch = False
        if risk_tolerance == 'conservative' and risk_level in ['high', 'very_high']:
            risk_mismatch = True
        elif risk_tolerance == 'aggressive' and risk_level in ['low', 'very_low']:
            risk_mismatch = True

        if risk_mismatch:
            recommendations.append(self._create_recommendation(
                rec_type='risk_adjustment',
                priority='high',
                description=f'Portfolio risk ({risk_level}) does not match your tolerance ({risk_tolerance})',
                details={
                    'current_risk_level': risk_level,
                    'target_risk_tolerance': risk_tolerance
                },
                expected_impact='Align portfolio risk with investment objectives'
            ))

        return recommendations

    def _calculate_total_return(self) -> float:
        """Calculate total portfolio return."""
        performance = self.portfolio_data.get('performance', {})
        if performance:
            return float(performance.get('total_return', 0))

        # Calculate from cost basis if available
        assets = self._get_assets()
        total_value = sum(a.get('current_value', 0) for a in assets)
        total_cost = sum(a.get('cost_basis', 0) for a in assets)

        if total_cost > 0:
            return (total_value - total_cost) / total_cost

        return 0.0

    def _calculate_volatility(self) -> float:
        """Calculate portfolio volatility."""
        performance = self.portfolio_data.get('performance', {})
        return float(performance.get('volatility', 0.15))

    def _calculate_information_ratio(self) -> float:
        """Calculate information ratio (alpha / tracking error)."""
        # Simplified - would need tracking error calculation
        return 0.0

    def _determine_risk_level(self) -> str:
        """Determine current portfolio risk level."""
        try:
            var_data = self.risk_service.calculate_var(confidence_level=0.95)
            var_pct = abs(var_data.get('var_percentage', 0))

            if var_pct > 5:
                return 'very_high'
            elif var_pct > 3:
                return 'high'
            elif var_pct > 2:
                return 'moderate'
            elif var_pct > 1:
                return 'low'
            else:
                return 'very_low'
        except:
            return 'moderate'

    def _assess_diversification(self) -> float:
        """Assess portfolio diversification."""
        assets = self._get_assets()
        if len(assets) < 2:
            return 0.3

        # Check number of different asset types
        asset_types = set(a.get('asset_type', '') for a in assets)
        type_score = min(len(asset_types) / 5, 1.0)

        # Check number of holdings
        holding_score = min(len(assets) / 20, 1.0)

        # Check concentration (top holding %)
        total_value = self._get_portfolio_value()
        if total_value > 0:
            max_position = max(a.get('current_value', 0) for a in assets)
            concentration = max_position / total_value
            concentration_score = 1 - concentration
        else:
            concentration_score = 0.5

        return (type_score + holding_score + concentration_score) / 3

    def _get_target_allocation(self, risk_tolerance: str) -> Dict[str, float]:
        """Get target allocation based on risk tolerance."""
        targets = {
            'conservative': {
                'cash': 15,
                'investments': 50,
                'real_estate': 25,
                'startup_equity': 5,
                'vehicles': 3,
                'personal_property': 2
            },
            'moderate': {
                'cash': 10,
                'investments': 60,
                'real_estate': 20,
                'startup_equity': 7,
                'vehicles': 2,
                'personal_property': 1
            },
            'aggressive': {
                'cash': 5,
                'investments': 70,
                'real_estate': 15,
                'startup_equity': 8,
                'vehicles': 1,
                'personal_property': 1
            }
        }
        return targets.get(risk_tolerance, targets['moderate'])

    def _generate_analysis_reasoning(
        self,
        metrics: Dict[str, float],
        risk: Dict[str, Any],
        capm: Dict[str, Any]
    ) -> str:
        """Generate human-readable analysis reasoning."""
        parts = []

        # Portfolio performance
        total_return = metrics.get('total_return_1y', 0)
        if total_return > 0.10:
            parts.append(f"Strong portfolio performance with {total_return:.1%} return")
        elif total_return > 0:
            parts.append(f"Positive portfolio performance with {total_return:.1%} return")
        else:
            parts.append(f"Portfolio has experienced negative returns of {total_return:.1%}")

        # Risk assessment
        beta = metrics.get('beta', 1.0)
        if beta > 1.2:
            parts.append("Portfolio has higher than market risk (high beta)")
        elif beta < 0.8:
            parts.append("Portfolio is more defensive than market (low beta)")
        else:
            parts.append("Portfolio risk is in line with market")

        # Alpha
        alpha = metrics.get('alpha', 0)
        if alpha > 0.02:
            parts.append("Generating positive alpha (outperforming risk-adjusted expectations)")
        elif alpha < -0.02:
            parts.append("Negative alpha suggests underperformance relative to risk taken")

        # Sharpe ratio
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe > 1:
            parts.append("Excellent risk-adjusted returns (Sharpe > 1)")
        elif sharpe > 0.5:
            parts.append("Good risk-adjusted returns")
        else:
            parts.append("Risk-adjusted returns could be improved")

        return ". ".join(parts) + "."
