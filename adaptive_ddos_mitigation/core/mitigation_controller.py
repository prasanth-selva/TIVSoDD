"""
Adaptive Mitigation Controller

Implements graduated mitigation strategies:
- Allow → Rate Limit → Traffic Shaping → Block

Features adaptive thresholds, rollback logic, and enforcement simulation.
"""

import time
import logging
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque, defaultdict

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.hybrid_detector import DetectionResult
from core.signature_generator import AttackSignature


class MitigationAction(Enum):
    """Mitigation action levels"""
    ALLOW = "allow"
    MONITOR = "monitor"
    RATE_LIMIT = "rate_limit"
    SHAPE = "traffic_shaping"
    BLOCK = "drop"


@dataclass
class MitigationRule:
    """Active mitigation rule"""
    rule_id: str
    action: MitigationAction
    creation_time: float
    confidence: float
    
    # Rule parameters
    target_signature: Optional[AttackSignature] = None
    rate_limit_pps: Optional[int] = None
    shaping_rate: Optional[int] = None
    
    # Tracking
    packets_processed: int = 0
    packets_dropped: int = 0
    packets_shaped: int = 0
    last_evaluation_time: float = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'rule_id': self.rule_id,
            'action': self.action.value,
            'confidence': self.confidence,
            'age_seconds': time.time() - self.creation_time,
            'packets_processed': self.packets_processed,
            'packets_dropped': self.packets_dropped,
            'packets_shaped': self.packets_shaped,
            'drop_rate': self.packets_dropped / self.packets_processed
                        if self.packets_processed > 0 else 0
        }


@dataclass
class MitigationDecision:
    """Decision made by mitigation controller"""
    action: MitigationAction
    reason: str
    confidence: float
    rule_id: Optional[str]
    timestamp: float
    
    # Enforcement details
    should_drop: bool = False
    should_rate_limit: bool = False
    should_shape: bool = False
    rate_limit_value: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'action': self.action.value,
            'reason': self.reason,
            'confidence': self.confidence,
            'rule_id': self.rule_id,
            'should_drop': self.should_drop,
            'should_rate_limit': self.should_rate_limit,
            'should_shape': self.should_shape,
            'rate_limit_value': self.rate_limit_value
        }


class AdaptiveMitigationController:
    """
    Graduated mitigation controller with adaptive thresholds.
    
    Implements multi-level response strategy with automatic rollback
    when traffic normalizes.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize mitigation controller
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Mitigation strategy
        self.strategy = config.get('strategy', 'graduated')
        self.levels = config.get('levels', [])
        
        # Rollback configuration
        self.rollback_enabled = config.get('rollback', {}).get('enabled', True)
        self.evaluation_interval = config.get('rollback', {}).get('evaluation_interval', 30)
        self.normalize_threshold = config.get('rollback', {}).get('normalize_threshold', 0.2)
        self.grace_period = config.get('rollback', {}).get('grace_period', 60)
        
        # Active rules
        self.active_rules: Dict[str, MitigationRule] = {}
        
        # Decision history
        self.decision_history = deque(maxlen=1000)
        
        # Traffic statistics for rollback evaluation
        self.traffic_stats = deque(maxlen=100)
        
        # Rule ID counter
        self.rule_counter = 0
        
        self.logger.info(f"Mitigation controller initialized with {self.strategy} strategy")
    
    def decide_mitigation(self, 
                         detection_result: DetectionResult,
                         matched_signature: Optional[AttackSignature] = None) -> MitigationDecision:
        """
        Decide mitigation action based on detection result
        
        Args:
            detection_result: Result from anomaly detection
            matched_signature: Matched attack signature (if any)
            
        Returns:
            MitigationDecision
        """
        current_time = time.time()
        
        # If not an anomaly, allow traffic
        if not detection_result.is_anomaly:
            return MitigationDecision(
                action=MitigationAction.ALLOW,
                reason="Normal traffic",
                confidence=1.0 - detection_result.anomaly_score,
                rule_id=None,
                timestamp=current_time
            )
        
        # Determine mitigation level based on anomaly score
        action = self._determine_action(detection_result.anomaly_score)
        
        # Check if we already have a rule for this signature
        existing_rule = self._find_existing_rule(matched_signature)
        
        if existing_rule:
            # Update existing rule
            rule_id = existing_rule.rule_id
            self._update_rule(existing_rule, detection_result)
        else:
            # Create new rule
            rule_id = self._create_rule(action, detection_result, matched_signature)
        
        # Create decision
        decision = MitigationDecision(
            action=action,
            reason=self._generate_reason(detection_result, matched_signature),
            confidence=detection_result.confidence,
            rule_id=rule_id,
            timestamp=current_time
        )
        
        # Set enforcement flags
        if action == MitigationAction.BLOCK:
            decision.should_drop = True
        elif action == MitigationAction.RATE_LIMIT:
            decision.should_rate_limit = True
            decision.rate_limit_value = self._get_rate_limit(action)
        elif action == MitigationAction.SHAPE:
            decision.should_shape = True
            decision.rate_limit_value = self._get_shaping_rate(action)
        
        # Record decision
        self.decision_history.append(decision)
        
        return decision
    
    def _determine_action(self, anomaly_score: float) -> MitigationAction:
        """Determine mitigation action based on score"""
        if self.strategy == 'immediate':
            # Immediate blocking
            return MitigationAction.BLOCK if anomaly_score > 0.5 else MitigationAction.ALLOW
        
        elif self.strategy == 'graduated':
            # Graduated response
            for level in self.levels:
                threshold = level.get('threshold', 0)
                if anomaly_score >= threshold:
                    action_str = level.get('action', 'monitor')
                    return MitigationAction(action_str)
            
            return MitigationAction.ALLOW
        
        else:  # delayed
            # Only take action if anomaly persists
            recent_anomalies = sum(
                1 for d in list(self.decision_history)[-10:]
                if d.action != MitigationAction.ALLOW
            )
            
            if recent_anomalies >= 5:
                return MitigationAction.BLOCK if anomaly_score > 0.7 else MitigationAction.RATE_LIMIT
            else:
                return MitigationAction.MONITOR
    
    def _find_existing_rule(self, signature: Optional[AttackSignature]) -> Optional[MitigationRule]:
        """Find existing rule for signature"""
        if not signature:
            return None
        
        for rule in self.active_rules.values():
            if rule.target_signature and rule.target_signature.signature_id == signature.signature_id:
                return rule
        
        return None
    
    def _create_rule(self,
                     action: MitigationAction,
                     detection_result: DetectionResult,
                     signature: Optional[AttackSignature]) -> str:
        """Create new mitigation rule"""
        self.rule_counter += 1
        rule_id = f"rule_{self.rule_counter}_{int(time.time())}"
        
        rule = MitigationRule(
            rule_id=rule_id,
            action=action,
            creation_time=time.time(),
            confidence=detection_result.confidence,
            target_signature=signature,
            rate_limit_pps=self._get_rate_limit(action),
            shaping_rate=self._get_shaping_rate(action),
            last_evaluation_time=time.time()
        )
        
        self.active_rules[rule_id] = rule
        self.logger.info(f"Created mitigation rule {rule_id}: {action.value}")
        
        return rule_id
    
    def _update_rule(self, rule: MitigationRule, detection_result: DetectionResult):
        """Update existing rule"""
        # Update confidence (exponential moving average)
        rule.confidence = 0.7 * rule.confidence + 0.3 * detection_result.confidence
        
        # Potentially escalate action
        new_action = self._determine_action(detection_result.anomaly_score)
        if new_action.value > rule.action.value:
            self.logger.info(f"Escalating rule {rule.rule_id} from {rule.action.value} to {new_action.value}")
            rule.action = new_action
            rule.rate_limit_pps = self._get_rate_limit(new_action)
            rule.shaping_rate = self._get_shaping_rate(new_action)
    
    def _get_rate_limit(self, action: MitigationAction) -> Optional[int]:
        """Get rate limit for action"""
        for level in self.levels:
            if level.get('action') == action.value:
                return level.get('rate_limit_pps')
        return None
    
    def _get_shaping_rate(self, action: MitigationAction) -> Optional[int]:
        """Get shaping rate for action"""
        for level in self.levels:
            if level.get('action') == action.value:
                return level.get('shaping_rate')
        return None
    
    def _generate_reason(self, 
                        detection_result: DetectionResult,
                        signature: Optional[AttackSignature]) -> str:
        """Generate human-readable mitigation reason"""
        reasons = []
        
        if signature:
            reasons.append(f"Matched attack signature {signature.signature_id}")
        
        if detection_result.triggered_rules:
            top_rules = detection_result.triggered_rules[:3]
            reasons.append(f"Triggered rules: {', '.join(top_rules)}")
        
        reasons.append(f"Anomaly score: {detection_result.anomaly_score:.2f}")
        reasons.append(f"Confidence: {detection_result.confidence:.2f}")
        
        return "; ".join(reasons)
    
    def evaluate_rollback(self, recent_scores: List[float]) -> bool:
        """
        Evaluate if rollback should occur
        
        Args:
            recent_scores: Recent anomaly scores
            
        Returns:
            True if rollback should occur
        """
        if not self.rollback_enabled:
            return False
        
        if len(recent_scores) < 5:
            return False
        
        # Check if traffic has normalized
        avg_score = sum(recent_scores) / len(recent_scores)
        
        if avg_score < self.normalize_threshold:
            self.logger.info(f"Traffic normalized (avg score: {avg_score:.2f}), triggering rollback")
            return True
        
        return False
    
    def perform_rollback(self):
        """Remove or downgrade mitigation rules"""
        current_time = time.time()
        rules_to_remove = []
        
        for rule_id, rule in self.active_rules.items():
            # Check if rule is old enough for grace period
            rule_age = current_time - rule.creation_time
            
            if rule_age < self.grace_period:
                continue
            
            # Downgrade or remove rule
            if rule.action == MitigationAction.BLOCK:
                rule.action = MitigationAction.SHAPE
                rule.shaping_rate = self._get_shaping_rate(MitigationAction.SHAPE)
                self.logger.info(f"Downgraded rule {rule_id} to {rule.action.value}")
            elif rule.action == MitigationAction.SHAPE:
                rule.action = MitigationAction.RATE_LIMIT
                rule.rate_limit_pps = self._get_rate_limit(MitigationAction.RATE_LIMIT)
                self.logger.info(f"Downgraded rule {rule_id} to {rule.action.value}")
            else:
                # Remove rule
                rules_to_remove.append(rule_id)
                self.logger.info(f"Removed rule {rule_id}")
        
        # Remove rules
        for rule_id in rules_to_remove:
            del self.active_rules[rule_id]
    
    def simulate_enforcement(self, 
                           packet_count: int,
                           decision: MitigationDecision) -> Dict:
        """
        Simulate enforcement of mitigation decision
        
        Args:
            packet_count: Number of packets in window
            decision: Mitigation decision
            
        Returns:
            Enforcement statistics
        """
        stats = {
            'total_packets': packet_count,
            'packets_allowed': 0,
            'packets_dropped': 0,
            'packets_shaped': 0,
            'packets_rate_limited': 0
        }
        
        if decision.action == MitigationAction.ALLOW or decision.action == MitigationAction.MONITOR:
            stats['packets_allowed'] = packet_count
        
        elif decision.action == MitigationAction.BLOCK:
            stats['packets_dropped'] = packet_count
        
        elif decision.action == MitigationAction.RATE_LIMIT:
            # Simulate rate limiting
            if decision.rate_limit_value:
                allowed = min(packet_count, decision.rate_limit_value)
                stats['packets_allowed'] = allowed
                stats['packets_rate_limited'] = packet_count - allowed
                stats['packets_dropped'] = packet_count - allowed
        
        elif decision.action == MitigationAction.SHAPE:
            # Simulate traffic shaping (delay rather than drop)
            if decision.rate_limit_value:
                shaped = max(0, packet_count - decision.rate_limit_value)
                stats['packets_allowed'] = decision.rate_limit_value
                stats['packets_shaped'] = shaped
        
        # Update rule statistics
        if decision.rule_id and decision.rule_id in self.active_rules:
            rule = self.active_rules[decision.rule_id]
            rule.packets_processed += packet_count
            rule.packets_dropped += stats['packets_dropped']
            rule.packets_shaped += stats['packets_shaped']
        
        return stats
    
    def get_active_rules_summary(self) -> Dict:
        """Get summary of active mitigation rules"""
        return {
            'total_rules': len(self.active_rules),
            'rules_by_action': self._count_by_action(),
            'rules': [rule.to_dict() for rule in self.active_rules.values()]
        }
    
    def _count_by_action(self) -> Dict[str, int]:
        """Count rules by action type"""
        counts = defaultdict(int)
        for rule in self.active_rules.values():
            counts[rule.action.value] += 1
        return dict(counts)
    
    def get_statistics(self) -> Dict:
        """Get mitigation statistics"""
        return {
            'total_decisions': len(self.decision_history),
            'active_rules': len(self.active_rules),
            'decisions_by_action': self._count_decisions_by_action(),
            'avg_confidence': self._calculate_avg_confidence()
        }
    
    def _count_decisions_by_action(self) -> Dict[str, int]:
        """Count decisions by action"""
        counts = defaultdict(int)
        for decision in self.decision_history:
            counts[decision.action.value] += 1
        return dict(counts)
    
    def _calculate_avg_confidence(self) -> float:
        """Calculate average decision confidence"""
        if not self.decision_history:
            return 0.0
        
        confidences = [d.confidence for d in self.decision_history]
        return sum(confidences) / len(confidences)
