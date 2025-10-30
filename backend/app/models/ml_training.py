from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey, Float, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class FeedbackRecord(Base):
    """Model for storing user feedback on ML predictions and impact card accuracy."""
    __tablename__ = "ml_feedback_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    impact_card_id = Column(Integer, ForeignKey("impact_cards.id"), nullable=False, index=True)
    
    # Feedback details
    feedback_type = Column(String(50), nullable=False, index=True)  # accuracy, relevance, severity, category
    original_value = Column(Float, nullable=True)  # Original ML prediction value
    corrected_value = Column(Float, nullable=True)  # User-corrected value
    confidence = Column(Float, nullable=False, default=1.0)  # User confidence in feedback (0.0-1.0)
    
    # Additional context
    feedback_context = Column(JSON, default=dict)  # Additional feedback metadata
    user_expertise_level = Column(String(20), default="unknown")  # novice, intermediate, expert, unknown
    
    # Processing status
    feedback_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed = Column(Boolean, default=False, nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    impact_card = relationship("ImpactCard", backref="feedback_records")
    
    def __repr__(self):
        return f"<FeedbackRecord(id={self.id}, type='{self.feedback_type}', processed={self.processed})>"

class ModelPerformanceMetric(Base):
    """Model for tracking ML model performance metrics over time."""
    __tablename__ = "ml_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(100), nullable=False, index=True)
    model_type = Column(String(50), nullable=False, index=True)  # impact_classifier, risk_scorer, etc.
    
    # Performance metrics
    metric_name = Column(String(50), nullable=False, index=True)  # f1_score, precision, recall, accuracy
    metric_value = Column(Float, nullable=False)
    
    # Evaluation context
    evaluation_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    dataset_size = Column(Integer, nullable=True)
    evaluation_type = Column(String(30), default="validation")  # validation, test, production
    
    # Additional metadata
    metric_metadata = Column(JSON, default=dict)  # Additional metric context and parameters
    
    def __repr__(self):
        return f"<ModelPerformanceMetric(model='{self.model_version}', metric='{self.metric_name}', value={self.metric_value})>"

class TrainingJob(Base):
    """Model for tracking ML model training jobs and their status."""
    __tablename__ = "ml_training_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Job configuration
    model_type = Column(String(50), nullable=False, index=True)  # impact_classifier, risk_scorer, etc.
    trigger_type = Column(String(50), nullable=False, index=True)  # scheduled, performance_drop, feedback_threshold
    
    # Job status
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, running, completed, failed
    
    # Model versioning
    previous_model_version = Column(String(100), nullable=True)
    new_model_version = Column(String(100), nullable=True)
    
    # Training data
    training_data_size = Column(Integer, nullable=True)
    validation_data_size = Column(Integer, nullable=True)
    
    # Performance tracking
    performance_improvement = Column(Float, nullable=True)  # Improvement over previous model
    baseline_metric_value = Column(Float, nullable=True)
    new_metric_value = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Training configuration
    training_config = Column(JSON, default=dict)  # Hyperparameters and training settings
    
    def __repr__(self):
        return f"<TrainingJob(job_id='{self.job_id}', status='{self.status}', model_type='{self.model_type}')>"

# Database indexes for efficient querying
Index('idx_feedback_user_timestamp', FeedbackRecord.user_id, FeedbackRecord.feedback_timestamp)
Index('idx_feedback_processed_timestamp', FeedbackRecord.processed, FeedbackRecord.feedback_timestamp)
Index('idx_performance_model_timestamp', ModelPerformanceMetric.model_version, ModelPerformanceMetric.evaluation_timestamp)
Index('idx_training_status_created', TrainingJob.status, TrainingJob.created_at)
Index('idx_training_model_trigger', TrainingJob.model_type, TrainingJob.trigger_type)