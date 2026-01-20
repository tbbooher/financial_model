"""
Family Office Platform - Agent Processing Tasks

Celery tasks for running AI agent analyses and processing agent queues.
"""

from celery import shared_task
from datetime import datetime
import logging

from app import db
from app.models import AgentTask
from app.services.portfolio_service import PortfolioService
from app.agents.agent_manager import AgentManager
from app.utils.exceptions import AgentError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_agent_analysis_task(self, user_id: str, agent_type: str, task_type: str = 'full_analysis'):
    """
    Run analysis using a specific agent asynchronously.

    Args:
        user_id: User UUID string
        agent_type: Type of agent to run (cfa, cfp, cio, accountant, quant_risk, quant_strategy)
        task_type: Type of analysis task

    Returns:
        dict: Agent analysis results
    """
    try:
        logger.info(f"Starting {agent_type} agent analysis for user {user_id}")

        # Get portfolio data
        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        # Run agent analysis
        manager = AgentManager(user_id=user_id, portfolio_data=portfolio_data)
        response = manager.run_analysis(
            agent_type=agent_type,
            task_type=task_type,
            save_task=True
        )

        logger.info(f"{agent_type} agent analysis completed for user {user_id}")

        return {
            'user_id': user_id,
            'agent_type': agent_type,
            'response': response.to_dict(),
            'completed_at': datetime.utcnow().isoformat()
        }

    except AgentError as e:
        logger.error(f"Agent {agent_type} analysis failed for user {user_id}: {e}")

        # Update task status if exists
        task = AgentTask.query.filter_by(
            user_id=user_id,
            agent_type=agent_type,
            status='processing'
        ).first()

        if task:
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            db.session.commit()

        raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"Agent analysis task failed: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def run_all_agents_task(self, user_id: str):
    """
    Run all available agents for comprehensive analysis.

    Args:
        user_id: User UUID string

    Returns:
        dict: Results from all agents
    """
    try:
        logger.info(f"Starting comprehensive agent analysis for user {user_id}")

        # Get portfolio data
        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        # Run all analyses
        manager = AgentManager(user_id=user_id, portfolio_data=portfolio_data)
        results = manager.run_all_analyses(save_tasks=True)

        # Convert responses to dict
        response_data = {}
        for agent_type, response in results.items():
            response_data[agent_type] = response.to_dict()

        logger.info(f"Comprehensive agent analysis completed for user {user_id}")

        return {
            'user_id': user_id,
            'agents_run': list(results.keys()),
            'results': response_data,
            'completed_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Comprehensive agent analysis failed for user {user_id}: {e}")
        raise self.retry(exc=e)


@shared_task
def process_agent_queue_task():
    """
    Process pending agent tasks from the queue.

    Returns:
        dict: Processing results
    """
    try:
        logger.info("Processing agent task queue")

        # Get pending tasks
        pending_tasks = AgentTask.query.filter_by(status='pending').order_by(
            AgentTask.created_at.asc()
        ).limit(10).all()

        processed = []
        failed = []

        for task in pending_tasks:
            try:
                # Update status to processing
                task.status = 'processing'
                db.session.commit()

                # Get portfolio data
                portfolio_service = PortfolioService(str(task.user_id))
                portfolio_data = portfolio_service.get_portfolio_data()

                # Run analysis
                manager = AgentManager(
                    user_id=str(task.user_id),
                    portfolio_data=portfolio_data
                )
                response = manager.run_analysis(
                    agent_type=task.agent_type,
                    task_type=task.task_type,
                    save_task=False  # Don't create new task
                )

                # Update task with results
                task.status = 'completed'
                task.output_summary = response.reasoning[:500] if response.reasoning else None
                task.full_output = response.to_dict()
                task.confidence_score = response.confidence_score
                task.completed_at = datetime.utcnow()
                db.session.commit()

                processed.append({
                    'task_id': str(task.id),
                    'agent_type': task.agent_type,
                    'status': 'completed'
                })

            except Exception as e:
                task.status = 'failed'
                task.error_message = str(e)
                task.retry_count = (task.retry_count or 0) + 1
                task.completed_at = datetime.utcnow()
                db.session.commit()

                failed.append({
                    'task_id': str(task.id),
                    'agent_type': task.agent_type,
                    'error': str(e)
                })

        logger.info(f"Agent queue processing completed. "
                   f"Processed: {len(processed)}, Failed: {len(failed)}")

        return {
            'processed': processed,
            'failed': failed,
            'processed_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Agent queue processing failed: {e}")
        raise


@shared_task
def retry_failed_tasks_task():
    """
    Retry failed agent tasks that haven't exceeded max retries.

    Returns:
        dict: Retry results
    """
    try:
        logger.info("Retrying failed agent tasks")

        max_retries = 3

        # Get failed tasks eligible for retry
        failed_tasks = AgentTask.query.filter(
            AgentTask.status == 'failed',
            AgentTask.retry_count < max_retries
        ).all()

        retried = []

        for task in failed_tasks:
            # Reset to pending for reprocessing
            task.status = 'pending'
            task.error_message = None
            retried.append(str(task.id))

        db.session.commit()

        logger.info(f"Reset {len(retried)} failed tasks for retry")

        return {
            'retried_count': len(retried),
            'task_ids': retried,
            'retried_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed task retry failed: {e}")
        raise


@shared_task
def cleanup_old_tasks_task(days_old: int = 30):
    """
    Clean up old completed and failed tasks.

    Args:
        days_old: Delete tasks older than this many days

    Returns:
        dict: Cleanup results
    """
    try:
        logger.info(f"Cleaning up tasks older than {days_old} days")

        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days_old)

        deleted = AgentTask.query.filter(
            AgentTask.created_at < cutoff,
            AgentTask.status.in_(['completed', 'failed', 'cancelled'])
        ).delete()

        db.session.commit()

        logger.info(f"Deleted {deleted} old tasks")

        return {
            'deleted_count': deleted,
            'cutoff_date': cutoff.isoformat(),
            'cleaned_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Task cleanup failed: {e}")
        db.session.rollback()
        raise


@shared_task
def get_consolidated_recommendations_task(user_id: str, agent_types: list = None):
    """
    Get consolidated recommendations from multiple agents.

    Args:
        user_id: User UUID string
        agent_types: Optional list of agent types to include

    Returns:
        dict: Consolidated recommendations
    """
    try:
        logger.info(f"Getting consolidated recommendations for user {user_id}")

        # Get portfolio data
        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        # Get recommendations
        manager = AgentManager(user_id=user_id, portfolio_data=portfolio_data)
        recommendations = manager.get_consolidated_recommendations(
            agent_types=agent_types,
            max_recommendations=50
        )

        logger.info(f"Got {len(recommendations)} consolidated recommendations for user {user_id}")

        return {
            'user_id': user_id,
            'recommendations': recommendations,
            'count': len(recommendations),
            'retrieved_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get consolidated recommendations: {e}")
        raise


@shared_task
def schedule_periodic_analysis_task():
    """
    Schedule periodic analysis for all active users.

    Returns:
        dict: Scheduling results
    """
    try:
        logger.info("Scheduling periodic analysis for all users")

        from app.models import User

        active_users = User.query.filter_by(is_active=True).all()
        scheduled = []

        for user in active_users:
            # Create task entries for each agent
            agent_types = ['cfa', 'cfp', 'cio', 'accountant', 'quant_risk']

            for agent_type in agent_types:
                task = AgentTask(
                    user_id=user.id,
                    agent_type=agent_type,
                    task_type='periodic_analysis',
                    status='pending'
                )
                db.session.add(task)
                scheduled.append({
                    'user_id': str(user.id),
                    'agent_type': agent_type
                })

        db.session.commit()

        logger.info(f"Scheduled {len(scheduled)} periodic analyses")

        return {
            'scheduled_count': len(scheduled),
            'scheduled_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to schedule periodic analysis: {e}")
        db.session.rollback()
        raise
