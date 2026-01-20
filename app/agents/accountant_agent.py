"""
Family Office Platform - Accountant Agent

Tax specialist agent for tax optimization, compliance,
and financial record keeping.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List

from app.agents.base_agent import BaseAgent, AgentResponse


class AccountantAgent(BaseAgent):
    """
    Accountant Agent for Tax and Compliance.

    Responsibilities:
    - Tax loss harvesting recommendations
    - Quarterly tax planning
    - Deduction optimization
    - Compliance monitoring
    - Tax-efficient asset location strategies
    - Capital gains management
    """

    def __init__(self, user_id: str, portfolio_data: Dict[str, Any]):
        """Initialize Accountant agent."""
        super().__init__(user_id, portfolio_data)

    def analyze(self) -> AgentResponse:
        """
        Perform comprehensive tax analysis.

        Returns:
            AgentResponse with tax analysis results
        """
        try:
            self.logger.info(f"Starting Accountant analysis for user {self.user_id}")

            # Perform analyses
            tax_loss_harvesting = self._analyze_tax_loss_harvesting()
            capital_gains = self._analyze_capital_gains()
            asset_location = self._analyze_asset_location()
            estimated_taxes = self._estimate_tax_liability()
            deductions = self._identify_deduction_opportunities()

            # Generate recommendations
            recommendations = self.get_recommendations()

            # Calculate confidence
            confidence_factors = {
                'data_quality': self._assess_data_quality(),
                'data_completeness': self._assess_tax_data_completeness(),
                'tax_law_currency': 0.9  # Assume current tax law knowledge
            }

            reasoning = self._generate_tax_reasoning(
                tax_loss_harvesting, capital_gains, estimated_taxes
            )

            self._log_analysis('comprehensive_tax_analysis', {
                'harvesting': tax_loss_harvesting,
                'gains': capital_gains,
                'estimated_taxes': estimated_taxes
            })

            return AgentResponse(
                agent_type=self.agent_type,
                recommendations=recommendations,
                confidence_score=self._calculate_confidence(confidence_factors),
                reasoning=reasoning,
                data_sources=['portfolio_holdings', 'transaction_history', 'tax_records', 'cost_basis_data'],
                metadata={
                    'tax_loss_harvesting': tax_loss_harvesting,
                    'capital_gains_analysis': capital_gains,
                    'asset_location': asset_location,
                    'estimated_taxes': estimated_taxes,
                    'deduction_opportunities': deductions
                }
            )

        except Exception as e:
            self.logger.error(f"Accountant analysis failed: {str(e)}")
            raise

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate tax optimization recommendations.

        Returns:
            List of tax recommendations
        """
        recommendations = []

        # Tax loss harvesting recommendations
        harvesting_recs = self._generate_harvesting_recommendations()
        recommendations.extend(harvesting_recs)

        # Capital gains recommendations
        gains_recs = self._generate_gains_recommendations()
        recommendations.extend(gains_recs)

        # Asset location recommendations
        location_recs = self._generate_location_recommendations()
        recommendations.extend(location_recs)

        # Quarterly planning recommendations
        planning_recs = self._generate_planning_recommendations()
        recommendations.extend(planning_recs)

        # Sort by priority
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))

        return recommendations

    def _analyze_tax_loss_harvesting(self) -> Dict[str, Any]:
        """Analyze opportunities for tax loss harvesting."""
        assets = self._get_assets()

        losers = []
        total_unrealized_loss = Decimal('0.00')

        for asset in assets:
            unrealized = asset.get('unrealized_gain_loss', 0)
            if unrealized < 0:
                losers.append({
                    'symbol': asset.get('symbol', 'Unknown'),
                    'name': asset.get('name', ''),
                    'current_value': asset.get('current_value', 0),
                    'cost_basis': asset.get('cost_basis', 0),
                    'unrealized_loss': abs(unrealized),
                    'loss_percentage': asset.get('unrealized_gain_loss_percent', 0)
                })
                total_unrealized_loss += Decimal(str(abs(unrealized)))

        # Sort by loss amount
        losers.sort(key=lambda x: x['unrealized_loss'], reverse=True)

        # Calculate potential tax savings (assuming 25% combined rate)
        tax_rate = Decimal('0.25')
        potential_savings = total_unrealized_loss * tax_rate

        # Annual loss limit
        annual_limit = Decimal('3000')  # Against ordinary income

        return {
            'candidates': losers[:10],  # Top 10 loss positions
            'total_unrealized_loss': float(total_unrealized_loss),
            'potential_tax_savings': float(potential_savings),
            'annual_loss_limit': float(annual_limit),
            'capital_loss_carryforward_potential': float(max(0, total_unrealized_loss - annual_limit)),
            'harvesting_recommended': total_unrealized_loss > 1000  # Recommend if > $1000
        }

    def _analyze_capital_gains(self) -> Dict[str, Any]:
        """Analyze capital gains exposure."""
        assets = self._get_assets()

        short_term_gains = Decimal('0.00')
        long_term_gains = Decimal('0.00')
        unrealized_gains = Decimal('0.00')

        winners = []

        for asset in assets:
            unrealized = asset.get('unrealized_gain_loss', 0)
            if unrealized > 0:
                unrealized_gains += Decimal(str(unrealized))

                # Determine holding period (simplified - would check purchase date)
                holding_period = 'long_term'  # Assume long-term for now

                winners.append({
                    'symbol': asset.get('symbol', 'Unknown'),
                    'name': asset.get('name', ''),
                    'unrealized_gain': unrealized,
                    'holding_period': holding_period,
                    'current_value': asset.get('current_value', 0)
                })

        # Sort by gain amount
        winners.sort(key=lambda x: x['unrealized_gain'], reverse=True)

        # Estimate tax on gains
        short_term_rate = Decimal('0.35')  # Ordinary income rate
        long_term_rate = Decimal('0.20')  # Long-term capital gains rate

        estimated_tax = long_term_gains * long_term_rate + short_term_gains * short_term_rate

        return {
            'total_unrealized_gains': float(unrealized_gains),
            'short_term_gains': float(short_term_gains),
            'long_term_gains': float(long_term_gains + unrealized_gains),
            'estimated_tax_if_realized': float(estimated_tax),
            'top_gainers': winners[:10],
            'tax_rates': {
                'short_term': float(short_term_rate),
                'long_term': float(long_term_rate)
            }
        }

    def _analyze_asset_location(self) -> Dict[str, Any]:
        """Analyze asset location efficiency."""
        assets = self._get_assets()

        # Categorize assets by tax efficiency
        tax_inefficient = []  # Should be in tax-advantaged (bonds, REITs)
        tax_efficient = []     # Can be in taxable (stocks, index funds)

        for asset in assets:
            asset_type = asset.get('asset_type', '')

            if asset_type in ['bond', 'reit']:
                tax_inefficient.append(asset)
            elif asset_type in ['stock', 'etf']:
                tax_efficient.append(asset)

        # Analyze current location (simplified)
        # In production, would check which account type each asset is in

        return {
            'tax_inefficient_assets': len(tax_inefficient),
            'tax_efficient_assets': len(tax_efficient),
            'optimization_opportunity': len(tax_inefficient) > 0,
            'recommendations': [
                'Place bonds and REITs in tax-advantaged accounts',
                'Hold growth stocks in taxable accounts',
                'Keep index funds in taxable accounts for tax efficiency'
            ]
        }

    def _estimate_tax_liability(self) -> Dict[str, Any]:
        """Estimate current year tax liability from investments."""
        # Get realized gains from transactions (simplified)
        capital_gains = self._analyze_capital_gains()

        # Estimate dividend income
        assets = self._get_assets()
        total_value = sum(a.get('current_value', 0) for a in assets)
        estimated_dividend_yield = 0.02  # 2%
        estimated_dividends = total_value * estimated_dividend_yield

        # Real estate income
        real_estate = self.portfolio_data.get('real_estate', [])
        rental_income = sum(
            (p.get('monthly_income', 0) - p.get('monthly_expenses', 0)) * 12
            for p in real_estate
            if p.get('property_type') == 'rental'
        )

        # Tax estimates
        dividend_tax = estimated_dividends * 0.20  # Qualified dividend rate
        rental_tax = rental_income * 0.25  # Ordinary income rate

        return {
            'estimated_dividends': round(estimated_dividends, 2),
            'estimated_rental_income': round(rental_income, 2),
            'unrealized_capital_gains': capital_gains['total_unrealized_gains'],
            'estimated_dividend_tax': round(dividend_tax, 2),
            'estimated_rental_tax': round(rental_tax, 2),
            'total_estimated_investment_tax': round(dividend_tax + rental_tax, 2),
            'tax_year': datetime.now().year
        }

    def _identify_deduction_opportunities(self) -> Dict[str, Any]:
        """Identify potential tax deduction opportunities."""
        # Real estate related deductions
        real_estate = self.portfolio_data.get('real_estate', [])

        mortgage_interest = sum(
            (p.get('mortgage_balance', 0) * (p.get('mortgage_rate', 0.04)))
            for p in real_estate
        )

        property_taxes = sum(
            p.get('property_tax_annual', 0) for p in real_estate
        )

        deductions = {
            'investment_related': [
                {
                    'type': 'Investment advisory fees',
                    'note': 'No longer deductible after 2017 tax reform'
                },
                {
                    'type': 'Margin interest',
                    'note': 'Deductible up to net investment income'
                }
            ],
            'real_estate_related': [
                {
                    'type': 'Mortgage interest',
                    'estimated_amount': round(mortgage_interest, 2),
                    'note': 'Deductible on primary and one second home'
                },
                {
                    'type': 'Property taxes',
                    'estimated_amount': round(property_taxes, 2),
                    'note': 'SALT deduction capped at $10,000'
                }
            ],
            'charitable': [
                {
                    'type': 'Appreciated stock donations',
                    'note': 'Donate appreciated shares to avoid capital gains'
                },
                {
                    'type': 'Donor advised fund',
                    'note': 'Bunch donations for itemizing benefit'
                }
            ]
        }

        return deductions

    def _generate_harvesting_recommendations(self) -> List[Dict[str, Any]]:
        """Generate tax loss harvesting recommendations."""
        recommendations = []
        analysis = self._analyze_tax_loss_harvesting()

        if analysis['harvesting_recommended']:
            recommendations.append(self._create_recommendation(
                rec_type='tax_loss_harvesting',
                priority='high',
                description=f"Harvest ${analysis['total_unrealized_loss']:,.0f} in tax losses",
                details={
                    'candidates': analysis['candidates'][:5],
                    'potential_savings': analysis['potential_tax_savings']
                },
                expected_impact=f"Potential tax savings of ${analysis['potential_tax_savings']:,.0f}"
            ))

            # Wash sale warning
            recommendations.append(self._create_recommendation(
                rec_type='wash_sale_warning',
                priority='medium',
                description='Avoid wash sale rule violations',
                details={
                    'rule': 'Cannot repurchase substantially identical security within 30 days',
                    'alternatives': 'Consider similar but not identical replacements'
                },
                expected_impact='Preserve tax loss deduction'
            ))

        return recommendations

    def _generate_gains_recommendations(self) -> List[Dict[str, Any]]:
        """Generate capital gains management recommendations."""
        recommendations = []
        analysis = self._analyze_capital_gains()

        if analysis['total_unrealized_gains'] > 50000:
            recommendations.append(self._create_recommendation(
                rec_type='capital_gains_planning',
                priority='medium',
                description='Significant unrealized gains - plan any sales carefully',
                details={
                    'total_gains': analysis['total_unrealized_gains'],
                    'top_positions': analysis['top_gainers'][:3]
                },
                expected_impact='Minimize tax impact of any required sales'
            ))

        return recommendations

    def _generate_location_recommendations(self) -> List[Dict[str, Any]]:
        """Generate asset location recommendations."""
        recommendations = []
        analysis = self._analyze_asset_location()

        if analysis['optimization_opportunity']:
            recommendations.append(self._create_recommendation(
                rec_type='asset_location',
                priority='medium',
                description='Optimize asset location for tax efficiency',
                details={
                    'recommendations': analysis['recommendations']
                },
                expected_impact='Improved after-tax returns through proper asset location'
            ))

        return recommendations

    def _generate_planning_recommendations(self) -> List[Dict[str, Any]]:
        """Generate quarterly tax planning recommendations."""
        recommendations = []

        # Quarterly estimated tax reminder
        current_quarter = (datetime.now().month - 1) // 3 + 1
        recommendations.append(self._create_recommendation(
            rec_type='quarterly_planning',
            priority='low',
            description=f'Q{current_quarter} estimated tax payment review',
            details={
                'q1_due': 'April 15',
                'q2_due': 'June 15',
                'q3_due': 'September 15',
                'q4_due': 'January 15'
            },
            expected_impact='Avoid underpayment penalties'
        ))

        return recommendations

    def _assess_tax_data_completeness(self) -> float:
        """Assess completeness of tax-relevant data."""
        score = 0.0

        # Check for cost basis data
        assets = self._get_assets()
        assets_with_cost_basis = sum(1 for a in assets if a.get('cost_basis'))
        if assets:
            score += 0.3 * (assets_with_cost_basis / len(assets))

        # Check for transaction history
        if self.portfolio_data.get('transactions'):
            score += 0.3

        # Check for real estate data
        if self.portfolio_data.get('real_estate'):
            score += 0.2

        # Check for account data
        if self.portfolio_data.get('accounts'):
            score += 0.2

        return score

    def _generate_tax_reasoning(
        self,
        harvesting: Dict[str, Any],
        gains: Dict[str, Any],
        taxes: Dict[str, Any]
    ) -> str:
        """Generate tax analysis reasoning."""
        parts = []

        # Harvesting opportunities
        if harvesting['harvesting_recommended']:
            parts.append(f"Identified ${harvesting['total_unrealized_loss']:,.0f} in harvestable losses")
        else:
            parts.append("No significant tax loss harvesting opportunities at this time")

        # Gains exposure
        if gains['total_unrealized_gains'] > 0:
            parts.append(f"Portfolio has ${gains['total_unrealized_gains']:,.0f} in unrealized gains")

        # Estimated taxes
        parts.append(f"Estimated investment-related tax liability: ${taxes['total_estimated_investment_tax']:,.0f}")

        return ". ".join(parts) + "."
