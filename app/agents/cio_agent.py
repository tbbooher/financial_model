"""
Family Office Platform - CIO Agent

Chief Investment Officer agent for strategic portfolio management,
investment policy, and high-level allocation decisions.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List

from flask import current_app

from app.agents.base_agent import BaseAgent, AgentResponse
from app.services.capm_service import CAPMService
from app.services.risk_service import RiskService


class CIOAgent(BaseAgent):
    """
    Chief Investment Officer Agent.

    Responsibilities:
    - Strategic asset allocation decisions
    - Risk management oversight
    - Investment policy statement creation
    - Portfolio rebalancing recommendations
    - Market outlook and strategy adjustments
    - Performance benchmarking and evaluation
    """

    def __init__(self, user_id: str, portfolio_data: Dict[str, Any]):
        """Initialize CIO agent."""
        super().__init__(user_id, portfolio_data)
        self.capm_service = CAPMService()
        self.risk_service = RiskService(portfolio_data)

    def analyze(self) -> AgentResponse:
        """
        Perform strategic investment analysis.

        Returns:
            AgentResponse with strategic analysis results
        """
        try:
            self.logger.info(f"Starting CIO analysis for user {self.user_id}")

            # Perform strategic analyses
            strategic_allocation = self._strategic_asset_allocation()
            risk_oversight = self._risk_management_oversight()
            policy_review = self._review_investment_policy()
            market_outlook = self._assess_market_outlook()
            performance_eval = self._evaluate_performance()

            # Generate recommendations
            recommendations = self.get_recommendations()

            # Calculate confidence
            confidence_factors = {
                'data_quality': self._assess_data_quality(),
                'market_analysis': 0.75,
                'strategic_clarity': 0.8
            }

            reasoning = self._generate_strategic_reasoning(
                strategic_allocation, risk_oversight, market_outlook
            )

            self._log_analysis('strategic_investment_review', {
                'allocation': strategic_allocation,
                'risk': risk_oversight,
                'market': market_outlook
            })

            return AgentResponse(
                agent_type=self.agent_type,
                recommendations=recommendations,
                confidence_score=self._calculate_confidence(confidence_factors),
                reasoning=reasoning,
                data_sources=['market_data', 'economic_indicators', 'portfolio_analytics', 'risk_models'],
                metadata={
                    'strategic_allocation': strategic_allocation,
                    'risk_oversight': risk_oversight,
                    'investment_policy': policy_review,
                    'market_outlook': market_outlook,
                    'performance_evaluation': performance_eval
                }
            )

        except Exception as e:
            self.logger.error(f"CIO analysis failed: {str(e)}")
            raise

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate strategic recommendations.

        Returns:
            List of strategic recommendations
        """
        recommendations = []

        # Strategic allocation recommendations
        allocation_recs = self._generate_allocation_strategy()
        recommendations.extend(allocation_recs)

        # Risk management recommendations
        risk_recs = self._generate_risk_strategy()
        recommendations.extend(risk_recs)

        # Market positioning recommendations
        market_recs = self._generate_market_positioning()
        recommendations.extend(market_recs)

        # Rebalancing recommendations
        rebalancing_recs = self._generate_rebalancing_strategy()
        recommendations.extend(rebalancing_recs)

        # Sort by priority
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))

        return recommendations

    def _strategic_asset_allocation(self) -> Dict[str, Any]:
        """Determine strategic asset allocation."""
        risk_tolerance = self._get_risk_tolerance()
        total_value = self._get_portfolio_value()

        # Define strategic allocation based on risk tolerance
        strategic_allocations = {
            'conservative': {
                'equities': {'target': 40, 'range': (35, 45)},
                'fixed_income': {'target': 40, 'range': (35, 45)},
                'alternatives': {'target': 10, 'range': (5, 15)},
                'cash': {'target': 10, 'range': (5, 15)}
            },
            'moderate': {
                'equities': {'target': 60, 'range': (55, 65)},
                'fixed_income': {'target': 25, 'range': (20, 30)},
                'alternatives': {'target': 10, 'range': (5, 15)},
                'cash': {'target': 5, 'range': (3, 10)}
            },
            'aggressive': {
                'equities': {'target': 80, 'range': (75, 85)},
                'fixed_income': {'target': 10, 'range': (5, 15)},
                'alternatives': {'target': 8, 'range': (5, 12)},
                'cash': {'target': 2, 'range': (0, 5)}
            }
        }

        target_allocation = strategic_allocations.get(risk_tolerance, strategic_allocations['moderate'])

        # Calculate current allocation
        current_allocation = self._calculate_current_allocation()

        # Identify deviations
        deviations = {}
        for asset_class, targets in target_allocation.items():
            current = current_allocation.get(asset_class, 0)
            target = targets['target']
            min_val, max_val = targets['range']

            deviations[asset_class] = {
                'current': current,
                'target': target,
                'deviation': current - target,
                'within_range': min_val <= current <= max_val
            }

        return {
            'risk_profile': risk_tolerance,
            'strategic_allocation': target_allocation,
            'current_allocation': current_allocation,
            'deviations': deviations,
            'rebalancing_needed': any(not d['within_range'] for d in deviations.values()),
            'total_portfolio_value': total_value
        }

    def _risk_management_oversight(self) -> Dict[str, Any]:
        """Perform risk management oversight."""
        # Get various risk metrics
        var_95 = self.risk_service.calculate_var(confidence_level=0.95)
        cvar = self.risk_service.calculate_cvar(confidence_level=0.95)
        max_drawdown = self.risk_service.calculate_max_drawdown()

        # Define risk limits
        risk_limits = {
            'max_single_position': 10,  # 10% max
            'max_sector_concentration': 25,  # 25% max
            'max_daily_var': 3,  # 3% max
            'max_drawdown_tolerance': 20  # 20% max
        }

        # Check for breaches
        breaches = []

        # Check position concentration
        assets = self._get_assets()
        total_value = self._get_portfolio_value()
        if total_value > 0:
            for asset in assets:
                position_pct = (asset.get('current_value', 0) / total_value) * 100
                if position_pct > risk_limits['max_single_position']:
                    breaches.append({
                        'type': 'position_concentration',
                        'asset': asset.get('symbol', asset.get('name')),
                        'current': position_pct,
                        'limit': risk_limits['max_single_position']
                    })

        # Check VaR
        var_pct = abs(var_95.get('var_percentage', 0))
        if var_pct > risk_limits['max_daily_var']:
            breaches.append({
                'type': 'var_breach',
                'current': var_pct,
                'limit': risk_limits['max_daily_var']
            })

        return {
            'var_95': var_95,
            'cvar_95': cvar,
            'max_drawdown': max_drawdown,
            'risk_limits': risk_limits,
            'breaches': breaches,
            'risk_status': 'elevated' if breaches else 'normal'
        }

    def _review_investment_policy(self) -> Dict[str, Any]:
        """Review and generate investment policy statement."""
        risk_tolerance = self._get_risk_tolerance()

        # Investment objectives based on risk profile
        objectives = {
            'conservative': {
                'primary_objective': 'Capital preservation with modest growth',
                'return_target': '4-6% annually',
                'volatility_tolerance': 'Low (< 10% annual)',
                'income_focus': 'High'
            },
            'moderate': {
                'primary_objective': 'Balanced growth and income',
                'return_target': '6-8% annually',
                'volatility_tolerance': 'Moderate (10-15% annual)',
                'income_focus': 'Moderate'
            },
            'aggressive': {
                'primary_objective': 'Maximum long-term growth',
                'return_target': '8-10%+ annually',
                'volatility_tolerance': 'High (15%+ annual)',
                'income_focus': 'Low'
            }
        }

        policy = objectives.get(risk_tolerance, objectives['moderate'])

        return {
            'risk_profile': risk_tolerance,
            'investment_objectives': policy,
            'time_horizon': 'Long-term (10+ years)',
            'liquidity_needs': 'Moderate',
            'constraints': [
                'No speculative investments',
                'Diversification required across asset classes',
                'ESG considerations optional',
                'Tax efficiency prioritized'
            ],
            'review_frequency': 'Annual',
            'last_reviewed': datetime.now(timezone.utc).isoformat()
        }

    def _assess_market_outlook(self) -> Dict[str, Any]:
        """Assess current market outlook."""
        # In production, this would integrate with market data APIs
        # Using placeholder assessment

        return {
            'overall_outlook': 'neutral',
            'equity_outlook': {
                'us_large_cap': 'neutral',
                'us_small_cap': 'slightly_positive',
                'international_developed': 'neutral',
                'emerging_markets': 'cautious'
            },
            'fixed_income_outlook': {
                'government_bonds': 'cautious',
                'corporate_bonds': 'neutral',
                'high_yield': 'selective'
            },
            'alternative_outlook': {
                'real_estate': 'neutral',
                'commodities': 'neutral',
                'private_equity': 'selective'
            },
            'key_risks': [
                'Interest rate uncertainty',
                'Inflation persistence',
                'Geopolitical tensions',
                'Economic slowdown risk'
            ],
            'opportunities': [
                'Quality dividend stocks',
                'Short-duration bonds',
                'Value stocks',
                'Real assets for inflation hedge'
            ],
            'assessment_date': datetime.now(timezone.utc).isoformat()
        }

    def _evaluate_performance(self) -> Dict[str, Any]:
        """Evaluate portfolio performance vs benchmarks."""
        performance = self.portfolio_data.get('performance', {})

        total_return = float(performance.get('total_return', 0))
        benchmark_return = float(performance.get('benchmark_return', 0.10))

        # Calculate relative performance
        relative_performance = total_return - benchmark_return

        # Performance rating
        if relative_performance > 0.03:
            rating = 'Excellent'
        elif relative_performance > 0.01:
            rating = 'Above Average'
        elif relative_performance > -0.01:
            rating = 'Average'
        elif relative_performance > -0.03:
            rating = 'Below Average'
        else:
            rating = 'Needs Attention'

        return {
            'total_return': total_return,
            'benchmark_return': benchmark_return,
            'relative_performance': relative_performance,
            'performance_rating': rating,
            'benchmark': 'S&P 500 Total Return',
            'evaluation_period': '1 Year'
        }

    def _generate_allocation_strategy(self) -> List[Dict[str, Any]]:
        """Generate strategic allocation recommendations."""
        recommendations = []
        allocation = self._strategic_asset_allocation()

        if allocation['rebalancing_needed']:
            deviations = allocation['deviations']
            significant_deviations = {
                k: v for k, v in deviations.items()
                if not v['within_range']
            }

            recommendations.append(self._create_recommendation(
                rec_type='strategic_rebalancing',
                priority='high',
                description='Strategic allocation has drifted outside policy ranges',
                details={
                    'deviations': significant_deviations,
                    'target_allocation': allocation['strategic_allocation']
                },
                expected_impact='Restore portfolio to strategic allocation targets'
            ))

        return recommendations

    def _generate_risk_strategy(self) -> List[Dict[str, Any]]:
        """Generate risk management recommendations."""
        recommendations = []
        risk = self._risk_management_oversight()

        if risk['breaches']:
            recommendations.append(self._create_recommendation(
                rec_type='risk_mitigation',
                priority='urgent',
                description='Risk limit breaches detected - immediate attention required',
                details={
                    'breaches': risk['breaches']
                },
                expected_impact='Reduce portfolio risk to within acceptable limits'
            ))

        if risk['risk_status'] == 'elevated':
            recommendations.append(self._create_recommendation(
                rec_type='risk_review',
                priority='high',
                description='Portfolio risk level elevated - review risk exposures',
                details={
                    'var_95': risk['var_95'],
                    'cvar_95': risk['cvar_95']
                },
                expected_impact='Identify and address sources of elevated risk'
            ))

        return recommendations

    def _generate_market_positioning(self) -> List[Dict[str, Any]]:
        """Generate market positioning recommendations."""
        recommendations = []
        outlook = self._assess_market_outlook()

        # General market positioning based on outlook
        recommendations.append(self._create_recommendation(
            rec_type='market_positioning',
            priority='medium',
            description=f"Market outlook is {outlook['overall_outlook']} - review positioning",
            details={
                'key_risks': outlook['key_risks'],
                'opportunities': outlook['opportunities']
            },
            expected_impact='Position portfolio for current market environment'
        ))

        return recommendations

    def _generate_rebalancing_strategy(self) -> List[Dict[str, Any]]:
        """Generate rebalancing recommendations."""
        recommendations = []

        # Check if quarterly rebalancing is due
        recommendations.append(self._create_recommendation(
            rec_type='periodic_rebalancing',
            priority='low',
            description='Conduct quarterly portfolio rebalancing review',
            details={
                'frequency': 'Quarterly',
                'method': 'Calendar-based with threshold triggers',
                'threshold': '5% deviation from target'
            },
            expected_impact='Maintain strategic allocation and manage risk'
        ))

        return recommendations

    def _calculate_current_allocation(self) -> Dict[str, float]:
        """Calculate current allocation across asset classes."""
        allocation = self.portfolio_data.get('asset_allocation', {}) or \
                    self.portfolio_data.get('breakdown', {})

        total = sum(allocation.values()) if allocation else 0
        if total == 0:
            return {'equities': 60, 'fixed_income': 25, 'alternatives': 10, 'cash': 5}

        # Map specific asset types to broad categories
        equities = allocation.get('investments', 0) * 0.8  # Assume 80% of investments are equities
        fixed_income = allocation.get('investments', 0) * 0.2
        alternatives = allocation.get('real_estate', 0) + allocation.get('startup_equity', 0)
        cash = allocation.get('cash', 0)

        allocation_sum = equities + fixed_income + alternatives + cash
        if allocation_sum == 0:
            allocation_sum = 1

        return {
            'equities': round((equities / allocation_sum) * 100, 1),
            'fixed_income': round((fixed_income / allocation_sum) * 100, 1),
            'alternatives': round((alternatives / allocation_sum) * 100, 1),
            'cash': round((cash / allocation_sum) * 100, 1)
        }

    def _generate_strategic_reasoning(
        self,
        allocation: Dict[str, Any],
        risk: Dict[str, Any],
        outlook: Dict[str, Any]
    ) -> str:
        """Generate strategic reasoning explanation."""
        parts = []

        # Allocation status
        if allocation['rebalancing_needed']:
            parts.append("Portfolio allocation has drifted from strategic targets")
        else:
            parts.append("Portfolio allocation is within strategic ranges")

        # Risk status
        if risk['risk_status'] == 'elevated':
            parts.append("Risk metrics indicate elevated portfolio risk")
        else:
            parts.append("Risk levels are within acceptable parameters")

        # Market outlook
        parts.append(f"Current market outlook is {outlook['overall_outlook']}")

        parts.append("CIO strategic review completed")

        return ". ".join(parts) + "."
