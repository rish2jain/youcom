"""
Database models for ML Model Registry and Feature Store

This module contains SQLAlchemy models for the ML model registry,
A/B testing, and feature storage.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float, Boolean
from sqlalchemy.sql import func
from app.database import Base

class ModelRegistryRecord(Base):
    """Database model for the model registry."""
    __tablename__ = "ml_model_registry"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(100), unique=True, nullable=False, index=True)
    model_type = Column(String(50), nullable=False, index=True)
    version = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="inactive", index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Model information
    performance_metrics = Column(JSON, default=dict)
    training_config = Column(JSON, default=dict)
    file_paths = Column(JSON, default=dict)
    checksum = Column(String(64), nullable=False)
    
    # Metadata
    tags = Column(JSON, default=list)
    description = Column(Text, default="")
    deployment_strategy = Column(String(20), default="immediate")
    
    # Parent-child relationships for versioning
    parent_model_id = Column(String(100), nullable=True, index=True)
    
    def to_metadata(self):
        """Convert database record to metadata object."""
        from app.services.ml_model_registry import ModelMetadata, ModelStatus
        from app.services.ml_training_service import ModelType
        
        return ModelMetadata(
            model_id=self.model_id,
            model_type=ModelType(self.model_type),
            version=self.version,
            status=ModelStatus(self.status),
            created_at=self.created_at,
            deployed_at=self.deployed_at,
            performance_metrics=self.performance_metrics or {},
            training_config=self.training_config or {},
            file_paths=self.file_paths or {},
            checksum=self.checksum,
            tags=self.tags or [],
            description=self.description or ""
        )

class ABTestRecord(Base):
    """Database model for A/B test configurations."""
    __tablename__ = "ml_ab_tests"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(String(100), unique=True, nullable=False, index=True)
    model_type = Column(String(50), nullable=False, index=True)
    
    # Test configuration
    model_a_version = Column(String(100), nullable=False)
    model_b_version = Column(String(100), nullable=False)
    traffic_split = Column(Float, nullable=False, default=0.5)
    
    # Test timeline
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Test parameters
    success_metrics = Column(JSON, default=list)
    minimum_samples = Column(Integer, default=100)
    
    # Test status
    status = Column(String(20), default="active", index=True)  # active, completed, cancelled
    winner_version = Column(String(100), nullable=True)
    
    # Results
    results = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FeatureStoreRecord(Base):
    """Database model for persistent feature storage."""
    __tablename__ = "ml_feature_store"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    feature_hash = Column(String(32), nullable=False, index=True)
    features_json = Column(JSON, nullable=False)
    extraction_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Feature metadata
    feature_count = Column(Integer, nullable=False)
    avg_confidence = Column(Float, nullable=False)
    feature_types = Column(JSON, nullable=False)  # List of feature types present