"""
Family Office Platform - Celery Background Tasks

This module provides asynchronous task processing for portfolio calculations,
data synchronization, and agent processing.
"""

from app.tasks.portfolio_tasks import (
    calculate_portfolio_metrics_task,
    calculate_rebalancing_task,
    update_portfolio_values_task
)
from app.tasks.data_sync_tasks import (
    sync_stock_prices_task,
    sync_market_data_task,
    sync_economic_indicators_task
)
from app.tasks.agent_tasks import (
    run_agent_analysis_task,
    run_all_agents_task,
    process_agent_queue_task
)

__all__ = [
    # Portfolio tasks
    'calculate_portfolio_metrics_task',
    'calculate_rebalancing_task',
    'update_portfolio_values_task',
    # Data sync tasks
    'sync_stock_prices_task',
    'sync_market_data_task',
    'sync_economic_indicators_task',
    # Agent tasks
    'run_agent_analysis_task',
    'run_all_agents_task',
    'process_agent_queue_task'
]
