"""Machine Learning-based prediction service for competitor behavior forecasting."""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error
import joblib
import os

from app.models.predictive_intelligence import CompetitorPattern, PredictedEvent, PatternEvent
from app.models.impact_card import ImpactCard

logger = logging.getLogger(__name__)


class MLPredictionService:
    """Machine Learning service for advanced competitor behavior prediction."""
    
    def __init__(self, db: Session):
        self.db = db
        self.models_dir = "data/ml_models"
        self.scalers_dir = "data/ml_scalers"
        
        # Ensure directories exist
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.scalers_dir, exist_ok=True)
        
        # Model configurations
        self.timeline_model = None
        self.probability_model = None
        self.confidence_model = None
        self.feature_scaler = None
        self.label_encoder = None
        
        # Model parameters
        self.min_training_samples = 20
        self.feature_window_days = 30
        self.prediction_confidence_threshold = 0.6
    
    def train_prediction_models(self) -> Dict[str, Any]:
        """Train ML models for prediction enhancement."""
        logger.info("Training ML prediction models...")
        
        # Prepare training data
        training_data = self._prepare_training_data()
        
        if len(training_data) < self.min_training_samples:
            logger.warning(f"Insufficient training data: {len(training_data)} samples")
            return {"status": "insufficient_data", "samples": len(training_data)}
        
        # Split features and targets
        features_df = pd.DataFrame(training_data)
        
        # Prepare features
        feature_columns = [
            'days_since_last', 'pattern_frequency', 'pattern_confidence',
            'avg_risk_score', 'risk_trend', 'time_consistency',
            'impact_diversity', 'seasonal_factor'
        ]
        
        X = features_df[feature_columns].fillna(0)
        
        # Prepare targets
        y_timeline = features_df['actual_timeline'].fillna(30)  # Default to 30 days
        y_probability = features_df['success_probability'].fillna(0.5)
        y_confidence = features_df['prediction_confidence'].fillna(0.5)
        
        # Scale features
        self.feature_scaler = StandardScaler()
        X_scaled = self.feature_scaler.fit_transform(X)
        
        # Train timeline prediction model (regression)
        self.timeline_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.timeline_model.fit(X_scaled, y_timeline)
        
        # Train probability prediction model (classification)
        y_prob_binary = (y_probability > 0.5).astype(int)
        self.probability_model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42
        )
        self.probability_model.fit(X_scaled, y_prob_binary)
        
        # Train confidence prediction model (regression)
        self.confidence_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            random_state=42
        )
        self.confidence_model.fit(X_scaled, y_confidence)
        
        # Save models
        self._save_models()
        
        # Calculate training metrics
        timeline_mae = mean_absolute_error(y_timeline, self.timeline_model.predict(X_scaled))
        prob_accuracy = accuracy_score(y_prob_binary, self.probability_model.predict(X_scaled))
        conf_mae = mean_absolute_error(y_confidence, self.confidence_model.predict(X_scaled))
        
        metrics = {
            "status": "success",
            "training_samples": len(training_data),
            "timeline_mae": timeline_mae,
            "probability_accuracy": prob_accuracy,
            "confidence_mae": conf_mae,
            "feature_importance": self._get_feature_importance()
        }
        
        logger.info(f"Model training completed: {metrics}")
        return metrics
    
    def _prepare_training_data(self) -> List[Dict[str, Any]]:
        """Prepare training data from historical patterns and outcomes."""
        training_data = []
        
        # Get all validated predictions for training
        validated_predictions = self.db.query(PredictedEvent).filter(
            PredictedEvent.status.in_(["validated", "invalidated"]),
            PredictedEvent.accuracy_score.isnot(None)
        ).all()
        
        for prediction in validated_predictions:
            # Get the pattern associated with this prediction
            pattern = self.db.query(CompetitorPattern).filter(
                CompetitorPattern.id == prediction.pattern_id
            ).first()
            
            if not pattern:
                continue
            
            # Calculate features
            features = self._extract_prediction_features(pattern, prediction)
            
            # Calculate actual outcomes
            actual_timeline = None
            if prediction.validation_date and prediction.predicted_date:
                actual_timeline = (prediction.validation_date - prediction.predicted_date).days
            
            success_probability = prediction.accuracy_score
            prediction_confidence = prediction.confidence
            
            training_sample = {
                **features,
                'actual_timeline': actual_timeline,
                'success_probability': success_probability,
                'prediction_confidence': prediction_confidence
            }
            
            training_data.append(training_sample)
        
        return training_data
    
    def _extract_prediction_features(self, pattern: CompetitorPattern, prediction: PredictedEvent) -> Dict[str, float]:
        """Extract features for ML model training and prediction."""
        features = {}
        
        # Time-based features
        if pattern.last_observed:
            days_since_last = (prediction.created_at - pattern.last_observed).days
            features['days_since_last'] = days_since_last
        else:
            features['days_since_last'] = 0
        
        # Pattern characteristics
        features['pattern_frequency'] = pattern.frequency or 0
        features['pattern_confidence'] = pattern.confidence or 0
        features['avg_risk_score'] = self._calculate_avg_risk_score(pattern)
        features['risk_trend'] = self._calculate_risk_trend(pattern)
        features['time_consistency'] = self._calculate_time_consistency(pattern)
        features['impact_diversity'] = self._calculate_impact_diversity(pattern)
        
        # Seasonal factors
        features['seasonal_factor'] = self._calculate_seasonal_factor(prediction.created_at)
        
        return features
    
    def _calculate_avg_risk_score(self, pattern: CompetitorPattern) -> float:
        """Calculate average risk score from pattern sequence."""
        if not pattern.sequence:
            return 0.0
        
        risk_scores = [event.get('risk_score', 0) for event in pattern.sequence if event.get('risk_score')]
        return np.mean(risk_scores) if risk_scores else 0.0
    
    def _calculate_risk_trend(self, pattern: CompetitorPattern) -> float:
        """Calculate risk score trend from pattern sequence."""
        if not pattern.sequence or len(pattern.sequence) < 2:
            return 0.0
        
        risk_scores = [event.get('risk_score', 0) for event in pattern.sequence if event.get('risk_score')]
        if len(risk_scores) < 2:
            return 0.0
        
        # Calculate linear trend
        x = np.arange(len(risk_scores))
        trend = np.polyfit(x, risk_scores, 1)[0]
        return trend
    
    def _calculate_time_consistency(self, pattern: CompetitorPattern) -> float:
        """Calculate consistency of timing intervals in pattern."""
        if not pattern.typical_intervals or len(pattern.typical_intervals) < 2:
            return 0.0
        
        intervals = pattern.typical_intervals
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        # Consistency is inverse of coefficient of variation
        if mean_interval > 0:
            cv = std_interval / mean_interval
            consistency = max(0.0, 1.0 - cv)
        else:
            consistency = 0.0
        
        return consistency
    
    def _calculate_impact_diversity(self, pattern: CompetitorPattern) -> float:
        """Calculate diversity of impact areas in pattern."""
        if not pattern.sequence:
            return 0.0
        
        all_impacts = []
        for event in pattern.sequence:
            if event.get('impact_areas'):
                all_impacts.extend(event['impact_areas'])
        
        if not all_impacts:
            return 0.0
        
        # Calculate diversity as ratio of unique impacts to total impacts
        unique_impacts = len(set(all_impacts))
        total_impacts = len(all_impacts)
        
        return unique_impacts / total_impacts if total_impacts > 0 else 0.0
    
    def _calculate_seasonal_factor(self, date: datetime) -> float:
        """Calculate seasonal factor based on date."""
        # Simple seasonal factor based on month
        month = date.month
        
        # Business activity patterns (higher in Q1, Q4)
        seasonal_weights = {
            1: 0.9, 2: 0.8, 3: 0.9,  # Q1
            4: 0.7, 5: 0.7, 6: 0.6,  # Q2
            7: 0.5, 8: 0.5, 9: 0.7,  # Q3
            10: 0.8, 11: 0.9, 12: 0.9  # Q4
        }
        
        return seasonal_weights.get(month, 0.7)
    
    def enhance_prediction(self, pattern: CompetitorPattern, base_prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance a base prediction using ML models."""
        if not self._models_loaded():
            logger.warning("ML models not loaded, using base prediction")
            return base_prediction
        
        try:
            # Extract features for this pattern
            features = self._extract_prediction_features(pattern, type('obj', (object,), {
                'created_at': datetime.utcnow(),
                'pattern_id': pattern.id
            })())
            
            # Prepare feature vector
            feature_vector = np.array([[
                features['days_since_last'],
                features['pattern_frequency'],
                features['pattern_confidence'],
                features['avg_risk_score'],
                features['risk_trend'],
                features['time_consistency'],
                features['impact_diversity'],
                features['seasonal_factor']
            ]])
            
            # Scale features
            feature_vector_scaled = self.feature_scaler.transform(feature_vector)
            
            # Make predictions
            predicted_timeline = self.timeline_model.predict(feature_vector_scaled)[0]
            predicted_probability = self.probability_model.predict_proba(feature_vector_scaled)[0][1]
            predicted_confidence = self.confidence_model.predict(feature_vector_scaled)[0]
            
            # Enhance the base prediction
            enhanced_prediction = base_prediction.copy()
            
            # Update timeline
            enhanced_prediction['predicted_timeline_days'] = max(1, int(predicted_timeline))
            enhanced_prediction['predicted_date'] = datetime.utcnow() + timedelta(days=int(predicted_timeline))
            
            # Update probability and confidence
            enhanced_prediction['ml_probability'] = min(1.0, max(0.0, predicted_probability))
            enhanced_prediction['ml_confidence'] = min(1.0, max(0.0, predicted_confidence))
            
            # Combine with base prediction using weighted average
            base_weight = 0.4
            ml_weight = 0.6
            
            if 'probability' in base_prediction:
                enhanced_prediction['probability'] = (
                    base_weight * base_prediction['probability'] + 
                    ml_weight * enhanced_prediction['ml_probability']
                )
            
            if 'confidence' in base_prediction:
                enhanced_prediction['confidence'] = (
                    base_weight * base_prediction['confidence'] + 
                    ml_weight * enhanced_prediction['ml_confidence']
                )
            
            # Add ML-specific reasoning
            enhanced_prediction['ml_reasoning'] = [
                f"ML model predicts timeline of {int(predicted_timeline)} days",
                f"ML probability score: {predicted_probability:.2f}",
                f"ML confidence score: {predicted_confidence:.2f}",
                f"Key factors: pattern consistency, risk trend, seasonal timing"
            ]
            
            logger.info(f"Enhanced prediction with ML: timeline={predicted_timeline:.1f}d, prob={predicted_probability:.2f}")
            return enhanced_prediction
            
        except Exception as e:
            logger.error(f"Error enhancing prediction with ML: {e}")
            return base_prediction
    
    def calculate_confidence_intervals(self, prediction: Dict[str, Any], pattern: CompetitorPattern) -> Dict[str, Any]:
        """Calculate confidence intervals for predictions."""
        if not self._models_loaded():
            return prediction
        
        try:
            # Extract features
            features = self._extract_prediction_features(pattern, type('obj', (object,), {
                'created_at': datetime.utcnow(),
                'pattern_id': pattern.id
            })())
            
            feature_vector = np.array([[
                features['days_since_last'],
                features['pattern_frequency'],
                features['pattern_confidence'],
                features['avg_risk_score'],
                features['risk_trend'],
                features['time_consistency'],
                features['impact_diversity'],
                features['seasonal_factor']
            ]])
            
            feature_vector_scaled = self.feature_scaler.transform(feature_vector)
            
            # Calculate prediction intervals using bootstrap of residuals approach
            timeline_predictions = []
            
            # Get recent data for residual calculation
            recent_data = self._get_recent_training_data()
            if len(recent_data) >= 10:
                X_recent = pd.DataFrame(recent_data)[
                    ['days_since_last', 'pattern_frequency', 'pattern_confidence',
                     'avg_risk_score', 'risk_trend', 'time_consistency',
                     'impact_diversity', 'seasonal_factor']
                ].fillna(0)
                y_recent = pd.DataFrame(recent_data)['actual_timeline'].fillna(30)
                
                X_recent_scaled = self.feature_scaler.transform(X_recent)
                
                # Get predictions from already-trained model
                recent_preds = self.timeline_model.predict(X_recent_scaled)
                residuals = np.array(y_recent - recent_preds)
                
                # Get base prediction for current feature vector (computed once)
                base_pred = self.timeline_model.predict(feature_vector_scaled)[0]
                
                # Validate residuals before bootstrapping
                if (len(residuals) > 0 and 
                    not np.any(np.isnan(residuals)) and 
                    np.std(residuals) > 1e-6):
                    
                    # Bootstrap residuals to create prediction intervals
                    n_bootstrap = 1000  # Statistically reasonable sample count
                    for _ in range(n_bootstrap):
                        sampled_residual = np.random.choice(residuals)
                        timeline_predictions.append(base_pred + sampled_residual)
                else:
                    # Fall back to minimal variance sampling if residuals are invalid
                    logger.warning("Invalid residuals detected, falling back to minimal variance sampling")
                    for i in range(5):
                        timeline_predictions.append(base_pred + np.random.normal(0, base_pred * 0.1))
            else:
                # Fallback: use base prediction with minimal variance
                base_pred = self.timeline_model.predict(feature_vector_scaled)[0]
                for i in range(5):
                    timeline_predictions.append(base_pred + np.random.normal(0, base_pred * 0.1))
            
            if timeline_predictions:
                # Calculate confidence intervals
                timeline_mean = np.mean(timeline_predictions)
                timeline_std = np.std(timeline_predictions)
                
                # 95% confidence interval
                lower_bound = max(1, timeline_mean - 1.96 * timeline_std)
                upper_bound = timeline_mean + 1.96 * timeline_std
                
                prediction['confidence_intervals'] = {
                    'timeline_days': {
                        'mean': timeline_mean,
                        'lower_95': lower_bound,
                        'upper_95': upper_bound,
                        'std': timeline_std
                    }
                }
                
                # Update timeframe based on confidence intervals
                if upper_bound <= 7:
                    prediction['timeframe'] = "within 1 week"
                elif upper_bound <= 30:
                    prediction['timeframe'] = "within 1 month"
                elif upper_bound <= 90:
                    prediction['timeframe'] = "within 3 months"
                else:
                    prediction['timeframe'] = "beyond 3 months"
                
                prediction['earliest_date'] = datetime.utcnow() + timedelta(days=int(lower_bound))
                prediction['latest_date'] = datetime.utcnow() + timedelta(days=int(upper_bound))
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error calculating confidence intervals: {e}")
            return prediction
    
    def _get_recent_training_data(self) -> List[Dict[str, Any]]:
        """Get recent training data for confidence interval calculation."""
        # Get recent validated predictions (last 30 days)
        recent_date = datetime.utcnow() - timedelta(days=30)
        
        recent_predictions = self.db.query(PredictedEvent).filter(
            PredictedEvent.status.in_(["validated", "invalidated"]),
            PredictedEvent.created_at >= recent_date,
            PredictedEvent.accuracy_score.isnot(None)
        ).limit(50).all()
        
        training_data = []
        for prediction in recent_predictions:
            pattern = self.db.query(CompetitorPattern).filter(
                CompetitorPattern.id == prediction.pattern_id
            ).first()
            
            if pattern:
                features = self._extract_prediction_features(pattern, prediction)
                actual_timeline = None
                if prediction.validation_date and prediction.predicted_date:
                    actual_timeline = (prediction.validation_date - prediction.predicted_date).days
                
                training_data.append({
                    **features,
                    'actual_timeline': actual_timeline or 30
                })
        
        return training_data
    
    def _save_models(self):
        """Save trained models to disk."""
        try:
            if self.timeline_model:
                joblib.dump(self.timeline_model, os.path.join(self.models_dir, 'timeline_model.pkl'))
            
            if self.probability_model:
                joblib.dump(self.probability_model, os.path.join(self.models_dir, 'probability_model.pkl'))
            
            if self.confidence_model:
                joblib.dump(self.confidence_model, os.path.join(self.models_dir, 'confidence_model.pkl'))
            
            if self.feature_scaler:
                joblib.dump(self.feature_scaler, os.path.join(self.scalers_dir, 'feature_scaler.pkl'))
            
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def _load_models(self) -> bool:
        """Load trained models from disk."""
        try:
            timeline_path = os.path.join(self.models_dir, 'timeline_model.pkl')
            probability_path = os.path.join(self.models_dir, 'probability_model.pkl')
            confidence_path = os.path.join(self.models_dir, 'confidence_model.pkl')
            scaler_path = os.path.join(self.scalers_dir, 'feature_scaler.pkl')
            
            if all(os.path.exists(path) for path in [timeline_path, probability_path, confidence_path, scaler_path]):
                self.timeline_model = joblib.load(timeline_path)
                self.probability_model = joblib.load(probability_path)
                self.confidence_model = joblib.load(confidence_path)
                self.feature_scaler = joblib.load(scaler_path)
                
                logger.info("Models loaded successfully")
                return True
            else:
                logger.warning("Some model files not found")
                return False
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def _models_loaded(self) -> bool:
        """Check if all models are loaded."""
        return all([
            self.timeline_model is not None,
            self.probability_model is not None,
            self.confidence_model is not None,
            self.feature_scaler is not None
        ])
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained models."""
        if not self.timeline_model:
            return {}
        
        feature_names = [
            'days_since_last', 'pattern_frequency', 'pattern_confidence',
            'avg_risk_score', 'risk_trend', 'time_consistency',
            'impact_diversity', 'seasonal_factor'
        ]
        
        importance = self.timeline_model.feature_importances_
        return dict(zip(feature_names, importance))
    
    def get_model_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the ML models."""
        if not self._models_loaded():
            return {"status": "models_not_loaded"}
        
        # Get recent validation data
        recent_predictions = self.db.query(PredictedEvent).filter(
            PredictedEvent.status.in_(["validated", "invalidated"]),
            PredictedEvent.accuracy_score.isnot(None)
        ).limit(100).all()
        
        if not recent_predictions:
            return {"status": "no_validation_data"}
        
        # Calculate performance metrics
        total_predictions = len(recent_predictions)
        accurate_predictions = sum(1 for p in recent_predictions if p.accuracy_score > 0.5)
        
        return {
            "status": "success",
            "total_predictions": total_predictions,
            "accurate_predictions": accurate_predictions,
            "accuracy_rate": accurate_predictions / total_predictions,
            "feature_importance": self._get_feature_importance(),
            "model_types": {
                "timeline": "RandomForestRegressor",
                "probability": "GradientBoostingClassifier", 
                "confidence": "RandomForestRegressor"
            }
        }
    
    def initialize_models(self):
        """Initialize models by loading from disk or training if needed."""
        if not self._load_models():
            logger.info("Models not found, will train when sufficient data is available")
            return False
        return True