"""
Hybrid Detection Layer

Two-stage detection pipeline:
1. Fast statistical anomaly gate for early filtering
2. ML-based anomaly detection for confirmation

Reduces ML computational load and minimizes latency.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque

from .feature_engineering import FeatureVector


@dataclass
class DetectionResult:
    """Result from anomaly detection"""
    is_anomaly: bool
    anomaly_score: float
    confidence: float
    stage: str  # "statistical" or "ml"
    triggered_rules: List[str]
    feature_contributions: Dict[str, float]
    timestamp: float
    
    
class StatisticalAnomalyDetector:
    """
    Fast statistical anomaly detector using simple thresholds.
    
    Acts as a gating mechanism to reduce ML inference load.
    Based on rate limiting, variance analysis, and entropy checks.
    """
    
    def __init__(self,
                 packet_rate_threshold: float = 10000,
                 burst_threshold: float = 3.0,
                 entropy_min_threshold: float = 1.5,
                 variance_threshold: float = 2.5,
                 baseline_window_size: int = 10):
        """
        Initialize statistical detector
        
        Args:
            packet_rate_threshold: Maximum packets/sec before flagging
            burst_threshold: Standard deviations for burst detection
            entropy_min_threshold: Minimum entropy (bits) for legitimate traffic
            variance_threshold: Standard deviations for variance anomaly
            baseline_window_size: Number of windows for baseline calculation
        """
        self.packet_rate_threshold = packet_rate_threshold
        self.burst_threshold = burst_threshold
        self.entropy_min_threshold = entropy_min_threshold
        self.variance_threshold = variance_threshold
        
        self.logger = logging.getLogger(__name__)
        
        # Baseline tracking
        self.baseline_window = deque(maxlen=baseline_window_size)
        self.baseline_stats = {
            'packet_rate_mean': 0,
            'packet_rate_std': 1,
            'entropy_mean': 0,
            'entropy_std': 1
        }
    
    def update_baseline(self, feature_vector: FeatureVector):
        """
        Update baseline statistics from normal traffic
        
        Args:
            feature_vector: Features from a normal traffic window
        """
        self.baseline_window.append(feature_vector)
        
        if len(self.baseline_window) >= 3:
            # Calculate baseline statistics
            packet_rates = [fv.raw_stats.get('packet_rate', 0) for fv in self.baseline_window]
            entropies = [fv.raw_stats.get('src_ip_entropy', 0) for fv in self.baseline_window]
            
            self.baseline_stats['packet_rate_mean'] = np.mean(packet_rates)
            self.baseline_stats['packet_rate_std'] = max(np.std(packet_rates), 1.0)
            self.baseline_stats['entropy_mean'] = np.mean(entropies)
            self.baseline_stats['entropy_std'] = max(np.std(entropies), 0.1)
    
    def detect(self, feature_vector: FeatureVector) -> DetectionResult:
        """
        Perform fast statistical anomaly detection
        
        Args:
            feature_vector: Extracted features
            
        Returns:
            DetectionResult
        """
        triggered_rules = []
        scores = []
        
        # Extract relevant statistics
        packet_rate = feature_vector.raw_stats.get('packet_rate', 0)
        src_ip_entropy = feature_vector.raw_stats.get('src_ip_entropy', 0)
        syn_ratio = feature_vector.raw_stats.get('syn_ratio', 0)
        burstiness = feature_vector.raw_stats.get('burstiness', 0)
        
        # Rule 1: Absolute packet rate threshold
        if packet_rate > self.packet_rate_threshold:
            triggered_rules.append("high_packet_rate")
            scores.append(min((packet_rate / self.packet_rate_threshold) - 1, 1.0))
        
        # Rule 2: Packet rate deviation from baseline
        rate_z_score = abs(packet_rate - self.baseline_stats['packet_rate_mean']) / \
                       self.baseline_stats['packet_rate_std']
        if rate_z_score > self.variance_threshold:
            triggered_rules.append("rate_deviation")
            scores.append(min(rate_z_score / self.variance_threshold - 1, 1.0))
        
        # Rule 3: Low entropy (potential DDoS from limited sources)
        if src_ip_entropy < self.entropy_min_threshold:
            triggered_rules.append("low_entropy")
            scores.append(1.0 - (src_ip_entropy / self.entropy_min_threshold))
        
        # Rule 4: High burstiness
        if burstiness > self.burst_threshold:
            triggered_rules.append("high_burstiness")
            scores.append(min(burstiness / self.burst_threshold - 1, 1.0))
        
        # Rule 5: SYN flood detection
        if syn_ratio > 0.6:  # More than 60% SYN packets
            triggered_rules.append("syn_flood")
            scores.append(syn_ratio)
        
        # Calculate overall anomaly score
        anomaly_score = max(scores) if scores else 0.0
        is_anomaly = len(triggered_rules) >= 2 or anomaly_score > 0.7
        
        # Confidence based on number of triggered rules
        confidence = min(len(triggered_rules) / 3.0, 1.0)
        
        return DetectionResult(
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            confidence=confidence,
            stage="statistical",
            triggered_rules=triggered_rules,
            feature_contributions={
                'packet_rate': packet_rate,
                'src_ip_entropy': src_ip_entropy,
                'burstiness': burstiness,
                'syn_ratio': syn_ratio
            },
            timestamp=feature_vector.timestamp
        )


class HybridDetector:
    """
    Two-stage hybrid detection pipeline.
    
    Combines fast statistical filtering with ML-based confirmation
    to achieve both low latency and high accuracy.
    """
    
    def __init__(self,
                 statistical_detector: StatisticalAnomalyDetector,
                 ml_detector: Optional['MLEnsembleDetector'] = None,
                 require_ml_confirmation: bool = True):
        """
        Initialize hybrid detector
        
        Args:
            statistical_detector: Fast statistical detector
            ml_detector: ML-based detector (optional)
            require_ml_confirmation: Require ML confirmation for high-confidence detection
        """
        self.statistical_detector = statistical_detector
        self.ml_detector = ml_detector
        self.require_ml_confirmation = require_ml_confirmation
        
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.stats = {
            'total_processed': 0,
            'statistical_detections': 0,
            'ml_confirmations': 0,
            'false_positives_avoided': 0
        }
    
    def detect(self, feature_vector: FeatureVector) -> DetectionResult:
        """
        Perform two-stage anomaly detection
        
        Args:
            feature_vector: Extracted features
            
        Returns:
            Final DetectionResult
        """
        self.stats['total_processed'] += 1
        
        # Stage 1: Statistical detection
        stat_result = self.statistical_detector.detect(feature_vector)
        
        # If statistical detector doesn't flag as anomaly, return early
        if not stat_result.is_anomaly:
            return stat_result
        
        self.stats['statistical_detections'] += 1
        
        # Stage 2: ML confirmation (if available and required)
        if self.ml_detector and self.require_ml_confirmation:
            ml_result = self.ml_detector.detect(feature_vector)
            
            # Combine results
            if ml_result.is_anomaly:
                self.stats['ml_confirmations'] += 1
                # ML confirms - use ML result with higher confidence
                return DetectionResult(
                    is_anomaly=True,
                    anomaly_score=(stat_result.anomaly_score + ml_result.anomaly_score) / 2,
                    confidence=max(stat_result.confidence, ml_result.confidence),
                    stage="hybrid",
                    triggered_rules=stat_result.triggered_rules + ml_result.triggered_rules,
                    feature_contributions=ml_result.feature_contributions,
                    timestamp=feature_vector.timestamp
                )
            else:
                # ML doesn't confirm - likely false positive
                self.stats['false_positives_avoided'] += 1
                self.logger.debug("Statistical detection not confirmed by ML")
                return DetectionResult(
                    is_anomaly=False,
                    anomaly_score=stat_result.anomaly_score * 0.5,
                    confidence=0.3,
                    stage="hybrid",
                    triggered_rules=stat_result.triggered_rules,
                    feature_contributions=stat_result.feature_contributions,
                    timestamp=feature_vector.timestamp
                )
        
        # No ML detector or confirmation not required
        return stat_result
    
    def update_baseline(self, feature_vector: FeatureVector):
        """Update baseline for statistical detector"""
        self.statistical_detector.update_baseline(feature_vector)
    
    def get_statistics(self) -> Dict:
        """Get detection statistics"""
        stats = self.stats.copy()
        if stats['total_processed'] > 0:
            stats['detection_rate'] = stats['statistical_detections'] / stats['total_processed']
            if stats['statistical_detections'] > 0:
                stats['ml_confirmation_rate'] = stats['ml_confirmations'] / stats['statistical_detections']
        return stats
