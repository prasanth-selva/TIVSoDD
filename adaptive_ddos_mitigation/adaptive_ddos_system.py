"""
Adaptive DDoS Mitigation System - Main Orchestrator

Integrates all components into a cohesive system.
"""

import logging
import time
import yaml
from typing import Dict, List, Optional
from pathlib import Path
from collections import deque

from core.traffic_aggregator import TrafficAggregator, TrafficWindow
from core.feature_engineering import FeatureEngineer, FeatureVector
from core.hybrid_detector import HybridDetector, StatisticalAnomalyDetector
from core.signature_generator import SignatureGenerator
from core.mitigation_controller import AdaptiveMitigationController
from core.explainability import ExplainabilityEngine
from models.ml_ensemble import MLEnsembleDetector


class AdaptiveDDoSMitigationSystem:
    """
    Main orchestrator for the adaptive DDoS mitigation system.
    
    Coordinates traffic ingestion, feature extraction, anomaly detection,
    signature generation, mitigation, and explainability.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the system
        
        Args:
            config_path: Path to configuration YAML file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Adaptive DDoS Mitigation System")
        
        # Initialize components
        self._init_components()
        
        # System state
        self.is_trained = False
        self.anomaly_score_history = deque(maxlen=100)
        self.training_feature_vectors = []
        
        self.logger.info("System initialization complete")
    
    def _setup_logging(self):
        """Configure logging"""
        log_config = self.config.get('logging', {})
        log_level = log_config.get('level', 'INFO')
        log_dir = Path(log_config.get('log_dir', 'logs'))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'ddos_mitigation.log'),
                logging.StreamHandler()
            ]
        )
    
    def _init_components(self):
        """Initialize all system components"""
        # Traffic aggregator
        traffic_config = self.config.get('traffic_capture', {})
        self.aggregator = TrafficAggregator(
            window_size=traffic_config.get('window_size_sec', 5.0),
            overlap=traffic_config.get('window_overlap', 0.5),
            max_packets_per_window=traffic_config.get('max_packets_per_window', 100000)
        )
        
        # Feature engineer
        feature_config = self.config.get('feature_engineering', {})
        self.feature_engineer = FeatureEngineer(
            normalization=feature_config.get('normalization', 'minmax'),
            enable_temporal=feature_config.get('enable_temporal', True),
            enable_statistical=feature_config.get('enable_statistical', True),
            enable_protocol=feature_config.get('enable_protocol', True),
            enable_flow=feature_config.get('enable_flow', True)
        )
        
        # Statistical detector
        stat_config = self.config.get('statistical_detector', {})
        self.statistical_detector = StatisticalAnomalyDetector(
            packet_rate_threshold=stat_config.get('packet_rate_threshold', 10000),
            burst_threshold=stat_config.get('burst_threshold', 3.0),
            entropy_min_threshold=stat_config.get('entropy_min_threshold', 1.5),
            variance_threshold=stat_config.get('variance_threshold', 2.5)
        )
        
        # ML ensemble detector (will be initialized after feature dimension is known)
        self.ml_detector = None
        
        # Hybrid detector
        self.hybrid_detector = HybridDetector(
            statistical_detector=self.statistical_detector,
            ml_detector=None,  # Will be set after training
            require_ml_confirmation=True
        )
        
        # Signature generator
        sig_config = self.config.get('signature_generation', {})
        self.signature_generator = SignatureGenerator(
            min_attack_duration=sig_config.get('min_attack_duration', 10.0),
            signature_ttl=sig_config.get('signature_ttl', 300.0),
            max_signatures=sig_config.get('max_signatures', 100)
        )
        
        # Mitigation controller
        mitigation_config = self.config.get('mitigation', {})
        self.mitigation_controller = AdaptiveMitigationController(mitigation_config)
        
        # Explainability engine
        explainability_config = self.config.get('explainability', {})
        self.explainability_engine = ExplainabilityEngine(
            top_n_features=explainability_config.get('top_features', 5),
            generate_text=explainability_config.get('generate_text_explanation', True),
            log_explanations=explainability_config.get('log_decisions', True)
        )
        
        self.logger.info("All components initialized")
    
    def train(self, training_pcap: Optional[str] = None, num_windows: int = 100):
        """
        Train the ML models on normal traffic
        
        Args:
            training_pcap: Path to PCAP with normal traffic (optional)
            num_windows: Number of windows to generate if simulating
        """
        self.logger.info("Starting training phase")
        
        training_vectors = []
        
        if training_pcap:
            # Train from PCAP
            self.logger.info(f"Training from PCAP: {training_pcap}")
            for window in self.aggregator.aggregate_pcap(training_pcap):
                features = self.feature_engineer.extract_features(window)
                training_vectors.append(features)
                
                # Update statistical baseline
                self.statistical_detector.update_baseline(features)
        else:
            # Generate simulated normal traffic
            self.logger.info(f"Training on simulated normal traffic ({num_windows} windows)")
            stream = self.aggregator.simulate_realtime_stream(
                base_rate=1000,
                duration=num_windows * 5,  # 5 second windows
                attack_start=999999,  # No attack
                attack_duration=0
            )
            
            count = 0
            for window in stream:
                if count >= num_windows:
                    break
                
                features = self.feature_engineer.extract_features(window)
                training_vectors.append(features)
                self.statistical_detector.update_baseline(features)
                count += 1
        
        if not training_vectors:
            self.logger.error("No training data collected")
            return
        
        self.logger.info(f"Collected {len(training_vectors)} training samples")
        
        # Fit feature normalizer
        self.feature_engineer.fit_scaler(training_vectors)
        
        # Normalize training vectors
        normalized_vectors = [
            self.feature_engineer.normalize(fv) for fv in training_vectors
        ]
        
        # Initialize and train ML ensemble
        input_dim = len(training_vectors[0].features)
        ml_config = self.config.get('ml_ensemble', {})
        
        self.ml_detector = MLEnsembleDetector(
            input_dim=input_dim,
            config=ml_config
        )
        
        self.ml_detector.train(normalized_vectors)
        
        # Update hybrid detector with trained ML detector
        self.hybrid_detector.ml_detector = self.ml_detector
        
        self.is_trained = True
        self.logger.info("Training complete")
    
    def process_window(self, window: TrafficWindow) -> Dict:
        """
        Process a single traffic window through the entire pipeline
        
        Args:
            window: Traffic window to process
            
        Returns:
            Processing results dictionary
        """
        start_time = time.time()
        
        # Extract features
        feature_vector = self.feature_engineer.extract_and_normalize(window)
        
        # Check for signature match
        matched_signature = self.signature_generator.match_signature(window, feature_vector)
        
        # Perform detection
        detection_result = self.hybrid_detector.detect(feature_vector)
        
        # Track anomaly scores for rollback evaluation
        self.anomaly_score_history.append(detection_result.anomaly_score)
        
        # Make mitigation decision
        mitigation_decision = self.mitigation_controller.decide_mitigation(
            detection_result,
            matched_signature
        )
        
        # Simulate enforcement
        mitigation_stats = self.mitigation_controller.simulate_enforcement(
            window.packet_count,
            mitigation_decision
        )
        
        # Generate explanation
        explanation = self.explainability_engine.explain_decision(
            feature_vector,
            detection_result,
            mitigation_decision
        )
        
        # Handle attack observation for signature generation
        if detection_result.is_anomaly:
            self.signature_generator.observe_attack(window, feature_vector)
        else:
            # Reset attack observation if traffic normalizes
            if self.signature_generator.attack_start_time is not None:
                self.signature_generator.reset_attack_observation()
            
            # Update baseline with normal traffic
            self.hybrid_detector.update_baseline(feature_vector)
        
        # Evaluate rollback conditions
        if len(self.anomaly_score_history) >= 10:
            recent_scores = list(self.anomaly_score_history)[-10:]
            if self.mitigation_controller.evaluate_rollback(recent_scores):
                self.mitigation_controller.perform_rollback()
        
        processing_time = time.time() - start_time
        
        return {
            'timestamp': window.start_time,
            'window_id': feature_vector.window_id,
            'is_anomaly': detection_result.is_anomaly,
            'anomaly_score': detection_result.anomaly_score,
            'confidence': detection_result.confidence,
            'detection_stage': detection_result.stage,
            'matched_signature': matched_signature.signature_id if matched_signature else None,
            'mitigation_action': mitigation_decision.action.value,
            'mitigation_stats': mitigation_stats,
            'explanation': explanation.to_dict(),
            'processing_time_ms': processing_time * 1000
        }
    
    def run_simulation(self,
                      duration: float = 60.0,
                      attack_start: float = 20.0,
                      attack_duration: float = 15.0,
                      base_rate: int = 1000,
                      attack_multiplier: float = 10.0) -> List[Dict]:
        """
        Run a simulation with injected attack
        
        Args:
            duration: Simulation duration (seconds)
            attack_start: When attack starts
            attack_duration: Attack duration
            base_rate: Normal traffic rate (pps)
            attack_multiplier: Attack traffic multiplier
            
        Returns:
            List of processing results
        """
        if not self.is_trained:
            self.logger.warning("System not trained, training on normal traffic first")
            self.train()
        
        self.logger.info(f"Starting simulation: {duration}s total, attack at {attack_start}s for {attack_duration}s")
        
        results = []
        
        stream = self.aggregator.simulate_realtime_stream(
            base_rate=base_rate,
            duration=duration,
            attack_start=attack_start,
            attack_duration=attack_duration,
            attack_multiplier=attack_multiplier
        )
        
        for window in stream:
            result = self.process_window(window)
            results.append(result)
            
            # Log significant events
            if result['is_anomaly']:
                self.logger.warning(
                    f"ANOMALY DETECTED - Score: {result['anomaly_score']:.2f}, "
                    f"Action: {result['mitigation_action']}"
                )
        
        self.logger.info(f"Simulation complete. Processed {len(results)} windows")
        
        return results
    
    def run_pcap(self, pcap_path: str) -> List[Dict]:
        """
        Process a PCAP file
        
        Args:
            pcap_path: Path to PCAP file
            
        Returns:
            List of processing results
        """
        if not self.is_trained:
            self.logger.warning("System not trained, results may be unreliable")
        
        self.logger.info(f"Processing PCAP: {pcap_path}")
        
        results = []
        
        for window in self.aggregator.aggregate_pcap(pcap_path):
            result = self.process_window(window)
            results.append(result)
        
        self.logger.info(f"PCAP processing complete. Processed {len(results)} windows")
        
        return results
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            'is_trained': self.is_trained,
            'active_signatures': len(self.signature_generator.get_active_signatures()),
            'active_mitigation_rules': len(self.mitigation_controller.active_rules),
            'detection_statistics': self.hybrid_detector.get_statistics(),
            'mitigation_statistics': self.mitigation_controller.get_statistics(),
            'recent_avg_anomaly_score': sum(self.anomaly_score_history) / len(self.anomaly_score_history)
                                       if self.anomaly_score_history else 0
        }
    
    def save_models(self, directory: str):
        """Save trained models"""
        if not self.is_trained:
            self.logger.warning("System not trained, nothing to save")
            return
        
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        
        self.ml_detector.save_models(str(path))
        self.logger.info(f"Models saved to {directory}")
    
    def load_models(self, directory: str):
        """Load trained models"""
        if self.ml_detector is None:
            # Need to initialize ML detector first
            self.logger.error("Cannot load models before initialization. Train first.")
            return
        
        self.ml_detector.load_models(directory)
        self.hybrid_detector.ml_detector = self.ml_detector
        self.is_trained = True
        self.logger.info(f"Models loaded from {directory}")
