"""
Family Office Platform - Agent Task Model

Defines the AgentTask model for tracking AI agent analysis tasks,
their inputs, outputs, and status.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.dialects.postgresql import UUID

from app import db


class AgentTask(db.Model):
    """
    AI Agent task tracking model.

    Records all agent analysis tasks including:
    - Task configuration and inputs
    - Analysis results and recommendations
    - Performance metrics and confidence scores
    - Processing status and timing
    """

    __tablename__ = 'agent_tasks'

    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)

    # Agent Configuration
    agent_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: cfa, cfp, cio, accountant, quant_risk, quant_strategy, financial_coach, billing_admin
    task_type = db.Column(db.String(100), nullable=False)
    # Types: portfolio_review, risk_analysis, tax_planning, retirement_planning, etc.

    # Input/Output Data
    input_data = db.Column(db.JSON)
    output_data = db.Column(db.JSON)
    recommendations = db.Column(db.JSON)

    # Analysis Results
    confidence_score = db.Column(db.Numeric(5, 4))  # 0.0000 to 1.0000
    reasoning = db.Column(db.Text)
    data_sources = db.Column(db.JSON)  # List of data sources used

    # Processing Status
    status = db.Column(db.String(20), default='pending', index=True)
    # Status: pending, processing, completed, failed, cancelled
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)

    # Priority and Scheduling
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    scheduled_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)

    # Timing
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    processing_time_ms = db.Column(db.Integer)

    # Parent Task (for sub-analyses)
    parent_task_id = db.Column(UUID(as_uuid=True), db.ForeignKey('agent_tasks.id'))

    # Celery Task ID
    celery_task_id = db.Column(db.String(255))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subtasks = db.relationship('AgentTask', backref=db.backref('parent_task', remote_side=[id]))

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == 'completed'

    @property
    def is_failed(self) -> bool:
        """Check if task failed."""
        return self.status == 'failed'

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.is_failed and self.retry_count < self.max_retries

    @property
    def duration_seconds(self) -> float:
        """Get task duration in seconds."""
        if self.processing_time_ms:
            return self.processing_time_ms / 1000.0
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return 0.0

    def start(self):
        """Mark task as started."""
        self.status = 'processing'
        self.started_at = datetime.utcnow()

    def complete(self, output_data: dict = None, recommendations: list = None,
                 confidence_score: float = None, reasoning: str = None):
        """Mark task as completed with results."""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()

        if output_data:
            self.output_data = output_data
        if recommendations:
            self.recommendations = recommendations
        if confidence_score is not None:
            self.confidence_score = Decimal(str(confidence_score))
        if reasoning:
            self.reasoning = reasoning

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.processing_time_ms = int(delta.total_seconds() * 1000)

    def fail(self, error_message: str):
        """Mark task as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.processing_time_ms = int(delta.total_seconds() * 1000)

    def retry(self):
        """Reset task for retry."""
        if not self.can_retry:
            return False

        self.status = 'pending'
        self.retry_count += 1
        self.error_message = None
        self.started_at = None
        self.completed_at = None
        self.processing_time_ms = None
        return True

    def cancel(self):
        """Cancel the task."""
        if self.status not in ['completed', 'failed']:
            self.status = 'cancelled'
            self.completed_at = datetime.utcnow()

    @classmethod
    def create_task(cls, user_id, agent_type: str, task_type: str,
                    input_data: dict = None, priority: str = 'normal', **kwargs):
        """Factory method for creating a new agent task."""
        # Convert string user_id to UUID if needed
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        return cls(
            user_id=user_id,
            agent_type=agent_type,
            task_type=task_type,
            input_data=input_data or {},
            priority=priority,
            **kwargs
        )

    def to_dict(self, include_full_output: bool = False) -> dict:
        """Convert to dictionary."""
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'agent_type': self.agent_type,
            'task_type': self.task_type,
            'status': self.status,
            'priority': self.priority,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

        if include_full_output:
            data['input_data'] = self.input_data
            data['output_data'] = self.output_data
            data['recommendations'] = self.recommendations
            data['reasoning'] = self.reasoning
            data['data_sources'] = self.data_sources

        return data

    def __repr__(self):
        return f'<AgentTask {self.agent_type}/{self.task_type} ({self.status})>'


# Create indexes
db.Index('idx_agent_tasks_user_status', AgentTask.user_id, AgentTask.status)
db.Index('idx_agent_tasks_agent_type', AgentTask.agent_type, AgentTask.status)
db.Index('idx_agent_tasks_created', AgentTask.created_at)
