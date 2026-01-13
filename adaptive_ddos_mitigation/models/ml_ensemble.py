"""
ML Ensemble Detector

Combines multiple ML models for robust anomaly detection:
- Isolation Forest (unsupervised anomaly detection)
- Autoencoder (reconstruction-based anomaly detection)
- Time-series smoothing (EWMA-based trend detection)

Uses confidence-weighted voting for final decision.
"""

import logging
import numpy as np
import joblib
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import deque

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

try:
    from tensorflow import keras
    from tensorflow.keras import layers, Model
    import tensorflow as tf
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    logging.warning("TensorFlow/Keras not available. Autoencoder disabled.")

import sys
sys.path.append(str(Path(__file__).parent.parent))
from core.feature_engineering import FeatureVector
from core.hybrid_detector import DetectionResult


class IsolationForestDetector:
    """Isolation Forest based anomaly detector"""
    
    def __init__(self,
                 n_estimators: int = 100,
                 contamination: float = 0.05,
                 max_samples: int = 256):
        """
        Initialize Isolation Forest detector
        
        Args:
            n_estimators: Number of trees
            contamination: Expected proportion of anomalies
            max_samples: Samples per tree
        """
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            max_samples=max_samples,
            random_state=42,
            n_jobs=-1
        )
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
        
    def train(self, feature_vectors: List[FeatureVector]):
        """
        Train on normal traffic
        
        Args:
            feature_vectors: List of feature vectors (should be mostly normal)
        """
        if not feature_vectors:
            self.logger.warning("No training data provided")
            return
        
        X = np.array([fv.features for fv in feature_vectors])
        self.model.fit(X)
        self.is_trained = True
        self.logger.info(f"Isolation Forest trained on {len(feature_vectors)} samples")
    
    def predict(self, feature_vector: FeatureVector) -> Tuple[bool, float]:
        """
        Predict if feature vector is anomaly
        
        Args:
            feature_vector: Feature vector to classify
            
        Returns:
            (is_anomaly, anomaly_score)
        """
        if not self.is_trained:
            self.logger.warning("Model not trained")
            return False, 0.0
        
        X = feature_vector.features.reshape(1, -1)
        
        # Predict (-1 for anomaly, 1 for normal)
        prediction = self.model.predict(X)[0]
        
        # Get anomaly score (lower is more anomalous)
        score = self.model.score_samples(X)[0]
        
        # Normalize score to 0-1 range (higher = more anomalous)
        anomaly_score = 1.0 / (1.0 + np.exp(score))  # Sigmoid transformation
        
        is_anomaly = prediction == -1
        
        return is_anomaly, anomaly_score
    
    def save(self, path: str):
        """Save model to disk"""
        joblib.dump(self.model, path)
        self.logger.info(f"Isolation Forest saved to {path}")
    
    def load(self, path: str):
        """Load model from disk"""
        self.model = joblib.load(path)
        self.is_trained = True
        self.logger.info(f"Isolation Forest loaded from {path}")


class AutoencoderDetector:
    """Autoencoder-based anomaly detector"""
    
    def __init__(self,
                 input_dim: int,
                 encoding_dim: int = 16,
                 reconstruction_threshold: float = 0.1):
        """
        Initialize Autoencoder detector
        
        Args:
            input_dim: Number of input features
            encoding_dim: Size of encoded representation
            reconstruction_threshold: Threshold for anomaly detection
        """
        if not KERAS_AVAILABLE:
            raise ImportError("TensorFlow/Keras required for Autoencoder")
        
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.reconstruction_threshold = reconstruction_threshold
        self.model = None
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
        
        self._build_model()
    
    def _build_model(self):
        """Build autoencoder architecture"""
        # Encoder
        input_layer = layers.Input(shape=(self.input_dim,))
        encoded = layers.Dense(64, activation='relu')(input_layer)
        encoded = layers.Dense(32, activation='relu')(encoded)
        encoded = layers.Dense(self.encoding_dim, activation='relu')(encoded)
        
        # Decoder
        decoded = layers.Dense(32, activation='relu')(encoded)
        decoded = layers.Dense(64, activation='relu')(decoded)
        decoded = layers.Dense(self.input_dim, activation='sigmoid')(decoded)
        
        # Autoencoder model
        self.model = Model(input_layer, decoded)
        self.model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        self.logger.info(f"Autoencoder built: {self.input_dim} -> {self.encoding_dim} -> {self.input_dim}")
    
    def train(self, 
              feature_vectors: List[FeatureVector],
              epochs: int = 50,
              batch_size: int = 32,
              validation_split: float = 0.2):
        """
        Train autoencoder on normal traffic
        
        Args:
            feature_vectors: List of feature vectors (normal traffic)
            epochs: Training epochs
            batch_size: Batch size
            validation_split: Validation split ratio
        """
        if not feature_vectors:
            self.logger.warning("No training data provided")
            return
        
        X = np.array([fv.features for fv in feature_vectors])
        
        # Train to reconstruct normal traffic
        history = self.model.fit(
            X, X,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=0,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=5,
                    restore_best_weights=True
                )
            ]
        )
        
        self.is_trained = True
        final_loss = history.history['loss'][-1]
        self.logger.info(f"Autoencoder trained on {len(feature_vectors)} samples, final loss: {final_loss:.4f}")
    
    def predict(self, feature_vector: FeatureVector) -> Tuple[bool, float]:
        """
        Predict if feature vector is anomaly based on reconstruction error
        
        Args:
            feature_vector: Feature vector to classify
            
        Returns:
            (is_anomaly, anomaly_score)
        """
        if not self.is_trained:
            self.logger.warning("Model not trained")
            return False, 0.0
        
        X = feature_vector.features.reshape(1, -1)
        
        # Reconstruct
        reconstruction = self.model.predict(X, verbose=0)
        
        # Calculate reconstruction error
        mse = np.mean((X - reconstruction) ** 2)
        
        # Normalize to 0-1
        anomaly_score = min(mse / (self.reconstruction_threshold * 2), 1.0)
        
        is_anomaly = mse > self.reconstruction_threshold
        
        return is_anomaly, anomaly_score
    
    def save(self, path: str):
        """Save model to disk"""
        self.model.save(path)
        self.logger.info(f"Autoencoder saved to {path}")
    
    def load(self, path: str):
        """Load model from disk"""
        self.model = keras.models.load_model(path)
        self.is_trained = True
        self.logger.info(f"Autoencoder loaded from {path}")


class TimeSeriesDetector:
    """Time-series based anomaly detector using EWMA"""
    
    def __init__(self,
                 alpha: float = 0.3,
                 threshold_multiplier: float = 2.5):
        """
        Initialize time-series detector
        
        Args:
            alpha: EWMA smoothing factor (0-1)
            threshold_multiplier: Standard deviations for anomaly threshold
        """
        self.alpha = alpha
        self.threshold_multiplier = threshold_multiplier
        
        self.ewma_values = {}
        self.ewma_variance = {}
        self.history = deque(maxlen=100)
        
        self.logger = logging.getLogger(__name__)
    
    def update(self, feature_vector: FeatureVector):
        """
        Update EWMA with new observation
        
        Args:
            feature_vector: New feature vector
        """
        self.history.append(feature_vector)
        
        feature_dict = feature_vector.to_dict()
        
        for feature_name, value in feature_dict.items():
            if feature_name not in self.ewma_values:
                self.ewma_values[feature_name] = value
                self.ewma_variance[feature_name] = 0
            else:
                # Update EWMA
                old_ewma = self.ewma_values[feature_name]
                self.ewma_values[feature_name] = self.alpha * value + (1 - self.alpha) * old_ewma
                
                # Update variance estimate
                deviation = value - old_ewma
                self.ewma_variance[feature_name] = (1 - self.alpha) * \
                    (self.ewma_variance[feature_name] + self.alpha * deviation ** 2)
    
    def predict(self, feature_vector: FeatureVector) -> Tuple[bool, float]:
        """
        Predict if feature vector deviates from expected trend
        
        Args:
            feature_vector: Feature vector to classify
            
        Returns:
            (is_anomaly, anomaly_score)
        """
        if len(self.history) < 10:
            # Not enough history
            return False, 0.0
        
        feature_dict = feature_vector.to_dict()
        deviations = []
        
        for feature_name, value in feature_dict.items():
            if feature_name in self.ewma_values:
                expected = self.ewma_values[feature_name]
                variance = self.ewma_variance[feature_name]
                std = np.sqrt(variance) if variance > 0 else 1e-6
                
                # Calculate z-score
                z_score = abs(value - expected) / std
                deviations.append(z_score)
        
        if not deviations:
            return False, 0.0
        
        # Use mean deviation as anomaly score
        mean_deviation = np.mean(deviations)
        max_deviation = np.max(deviations)
        
        anomaly_score = min(mean_deviation / self.threshold_multiplier, 1.0)
        is_anomaly = max_deviation > self.threshold_multiplier
        
        return is_anomaly, anomaly_score


class MLEnsembleDetector:
    """
    Ensemble ML detector combining multiple models.
    
    Uses weighted voting for robust anomaly detection.
    """
    
    def __init__(self,
                 input_dim: int,
                 config: Dict):
        """
        Initialize ML ensemble
        
        Args:
            input_dim: Number of features
            config: Configuration dictionary
        """
        self.input_dim = input_dim
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self.models = {}
        
        if config.get('models', {}).get('isolation_forest', {}).get('enabled', True):
            self.models['isolation_forest'] = IsolationForestDetector(
                n_estimators=config['models']['isolation_forest'].get('n_estimators', 100),
                contamination=config['models']['isolation_forest'].get('contamination', 0.05),
                max_samples=config['models']['isolation_forest'].get('max_samples', 256)
            )
        
        if KERAS_AVAILABLE and config.get('models', {}).get('autoencoder', {}).get('enabled', True):
            self.models['autoencoder'] = AutoencoderDetector(
                input_dim=input_dim,
                encoding_dim=config['models']['autoencoder'].get('encoding_dim', 16),
                reconstruction_threshold=config['models']['autoencoder'].get('reconstruction_threshold', 0.1)
            )
        
        if config.get('models', {}).get('time_series', {}).get('enabled', True):
            self.models['time_series'] = TimeSeriesDetector(
                alpha=config['models']['time_series'].get('alpha', 0.3)
            )
        
        # Voting configuration
        self.voting_method = config.get('voting', {}).get('method', 'weighted')
        self.weights = config.get('voting', {}).get('weights', {
            'isolation_forest': 0.4,
            'autoencoder': 0.4,
            'time_series': 0.2
        })
        self.confidence_threshold = config.get('voting', {}).get('confidence_threshold', 0.65)
        
        self.logger.info(f"ML Ensemble initialized with {len(self.models)} models")
    
    def train(self, feature_vectors: List[FeatureVector]):
        """
        Train all models in ensemble
        
        Args:
            feature_vectors: Training data (normal traffic)
        """
        self.logger.info(f"Training ensemble on {len(feature_vectors)} samples")
        
        for name, model in self.models.items():
            if name == 'time_series':
                # Time series doesn't need explicit training
                for fv in feature_vectors:
                    model.update(fv)
            else:
                model.train(feature_vectors)
        
        self.logger.info("Ensemble training complete")
    
    def detect(self, feature_vector: FeatureVector) -> DetectionResult:
        """
        Detect anomalies using ensemble voting
        
        Args:
            feature_vector: Feature vector to classify
            
        Returns:
            DetectionResult with ensemble decision
        """
        predictions = {}
        scores = {}
        
        # Get predictions from all models
        for name, model in self.models.items():
            is_anomaly, score = model.predict(feature_vector)
            predictions[name] = is_anomaly
            scores[name] = score
            
            # Update time series
            if name == 'time_series':
                model.update(feature_vector)
        
        # Perform voting
        if self.voting_method == 'weighted':
            weighted_score = sum(
                scores.get(name, 0) * self.weights.get(name, 0)
                for name in self.models.keys()
            )
            is_anomaly = weighted_score > self.confidence_threshold
            confidence = weighted_score
        elif self.voting_method == 'majority':
            votes = sum(predictions.values())
            is_anomaly = votes > len(predictions) / 2
            confidence = votes / len(predictions)
            weighted_score = sum(scores.values()) / len(scores)
        else:  # unanimous
            is_anomaly = all(predictions.values())
            confidence = 1.0 if is_anomaly else 0.0
            weighted_score = sum(scores.values()) / len(scores)
        
        triggered_rules = [f"ml_{name}" for name, pred in predictions.items() if pred]
        
        return DetectionResult(
            is_anomaly=is_anomaly,
            anomaly_score=weighted_score,
            confidence=confidence,
            stage="ml_ensemble",
            triggered_rules=triggered_rules,
            feature_contributions=scores,
            timestamp=feature_vector.timestamp
        )
    
    def save_models(self, directory: str):
        """Save all models to directory"""
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        
        for name, model in self.models.items():
            if name == 'time_series':
                continue  # Time series doesn't need persistence
            
            model_path = path / f"{name}_model"
            model.save(str(model_path))
        
        self.logger.info(f"Models saved to {directory}")
    
    def load_models(self, directory: str):
        """Load all models from directory"""
        path = Path(directory)
        
        for name, model in self.models.items():
            if name == 'time_series':
                continue
            
            model_path = path / f"{name}_model"
            if model_path.exists():
                model.load(str(model_path))
        
        self.logger.info(f"Models loaded from {directory}")
