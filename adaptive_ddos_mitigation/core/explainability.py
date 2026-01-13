"""
Explainable AI Module

Provides human-readable explanations for mitigation decisions.
Includes feature importance analysis and SOC-friendly output.
"""

import logging
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.feature_engineering import FeatureVector
from core.hybrid_detector import DetectionResult
from core.mitigation_controller import MitigationDecision


@dataclass
class Explanation:
    """Structured explanation for a decision"""
    decision_id: str
    timestamp: float
    is_anomaly: bool
    anomaly_score: float
    action: str
    
    # Feature importance
    top_features: List[Tuple[str, float]]  # (feature_name, importance)
    
    # Human-readable text
    summary: str
    detailed_explanation: str
    technical_details: Dict
    
    # Recommendations
    recommended_actions: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'decision_id': self.decision_id,
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'is_anomaly': self.is_anomaly,
            'anomaly_score': self.anomaly_score,
            'action': self.action,
            'top_features': [
                {'name': name, 'importance': importance}
                for name, importance in self.top_features
            ],
            'summary': self.summary,
            'detailed_explanation': self.detailed_explanation,
            'technical_details': self.technical_details,
            'recommended_actions': self.recommended_actions
        }
    
    def to_soc_report(self) -> str:
        """Generate SOC-friendly report"""
        report = []
        report.append("="* 70)
        report.append("DDOS MITIGATION DECISION REPORT")
        report.append("=" * 70)
        report.append(f"Timestamp: {datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Decision ID: {self.decision_id}")
        report.append(f"Status: {'ATTACK DETECTED' if self.is_anomaly else 'NORMAL TRAFFIC'}")
        report.append(f"Anomaly Score: {self.anomaly_score:.2f}")
        report.append(f"Action Taken: {self.action}")
        report.append("")
        
        report.append("SUMMARY:")
        report.append(f"  {self.summary}")
        report.append("")
        
        report.append("TOP CONTRIBUTING FACTORS:")
        for i, (feature, importance) in enumerate(self.top_features, 1):
            report.append(f"  {i}. {feature}: {importance:.2%} contribution")
        report.append("")
        
        report.append("DETAILED ANALYSIS:")
        for line in self.detailed_explanation.split('\n'):
            report.append(f"  {line}")
        report.append("")
        
        if self.recommended_actions:
            report.append("RECOMMENDED ACTIONS:")
            for i, action in enumerate(self.recommended_actions, 1):
                report.append(f"  {i}. {action}")
        
        report.append("=" * 70)
        
        return "\n".join(report)


class ExplainabilityEngine:
    """
    Explainable AI engine for DDoS mitigation decisions.
    
    Provides feature importance, human-readable explanations,
    and actionable recommendations.
    """
    
    def __init__(self, 
                 top_n_features: int = 5,
                 generate_text: bool = True,
                 log_explanations: bool = True):
        """
        Initialize explainability engine
        
        Args:
            top_n_features: Number of top features to highlight
            generate_text: Generate text explanations
            log_explanations: Log explanations
        """
        self.top_n_features = top_n_features
        self.generate_text = generate_text
        self.log_explanations = log_explanations
        
        self.logger = logging.getLogger(__name__)
        
        # Feature importance templates
        self.feature_descriptions = self._build_feature_descriptions()
        
        # Explanation counter
        self.explanation_counter = 0
    
    def _build_feature_descriptions(self) -> Dict[str, str]:
        """Build human-readable descriptions for features"""
        return {
            # Rate-based
            'packet_rate': 'Packet arrival rate (packets/second)',
            'byte_rate': 'Data transfer rate (bytes/second)',
            'packet_count': 'Total packets in window',
            
            # Temporal
            'inter_arrival_mean': 'Average time between packets',
            'inter_arrival_std': 'Variation in packet timing',
            'burstiness_index': 'Traffic burstiness (high = bursty)',
            'coefficient_of_variation': 'Timing consistency',
            
            # Statistical
            'src_ip_entropy': 'Source IP diversity (low = concentrated)',
            'dst_ip_entropy': 'Destination IP diversity',
            'src_port_entropy': 'Source port randomness',
            'dst_port_entropy': 'Destination port distribution',
            'packet_size_entropy': 'Packet size variability',
            'unique_src_ips': 'Number of unique source IPs',
            'unique_dst_ips': 'Number of unique destination IPs',
            'src_dst_ratio': 'Source to destination IP ratio',
            
            # Protocol
            'tcp_ratio': 'TCP traffic percentage',
            'udp_ratio': 'UDP traffic percentage',
            'icmp_ratio': 'ICMP traffic percentage',
            'syn_ratio': 'SYN packet ratio',
            'ack_ratio': 'ACK packet ratio',
            'syn_ack_ratio': 'SYN/ACK ratio (connection attempts)',
            
            # Flow
            'flow_count': 'Number of distinct flows',
            'avg_flow_packets': 'Average packets per flow',
            'avg_flow_duration': 'Average flow duration',
            'flow_symmetry_score': 'Bidirectional flow ratio',
            'short_flow_ratio': 'Percentage of short-lived flows'
        }
    
    def explain_decision(self,
                        feature_vector: FeatureVector,
                        detection_result: DetectionResult,
                        mitigation_decision: MitigationDecision) -> Explanation:
        """
        Generate comprehensive explanation for a decision
        
        Args:
            feature_vector: Input features
            detection_result: Detection result
            mitigation_decision: Mitigation decision
            
        Returns:
            Explanation object
        """
        self.explanation_counter += 1
        decision_id = f"EXP_{self.explanation_counter}_{int(feature_vector.timestamp)}"
        
        # Calculate feature importance
        top_features = self._calculate_feature_importance(
            feature_vector,
            detection_result
        )
        
        # Generate text explanation
        if self.generate_text:
            summary = self._generate_summary(
                detection_result,
                mitigation_decision,
                top_features
            )
            
            detailed = self._generate_detailed_explanation(
                feature_vector,
                detection_result,
                top_features
            )
        else:
            summary = f"Anomaly score: {detection_result.anomaly_score:.2f}"
            detailed = "Text generation disabled"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            detection_result,
            mitigation_decision,
            top_features
        )
        
        # Technical details
        technical = {
            'anomaly_score': detection_result.anomaly_score,
            'confidence': detection_result.confidence,
            'detection_stage': detection_result.stage,
            'triggered_rules': detection_result.triggered_rules,
            'feature_contributions': detection_result.feature_contributions
        }
        
        explanation = Explanation(
            decision_id=decision_id,
            timestamp=feature_vector.timestamp,
            is_anomaly=detection_result.is_anomaly,
            anomaly_score=detection_result.anomaly_score,
            action=mitigation_decision.action.value,
            top_features=top_features,
            summary=summary,
            detailed_explanation=detailed,
            technical_details=technical,
            recommended_actions=recommendations
        )
        
        if self.log_explanations:
            self.logger.info(f"Explanation generated: {summary}")
        
        return explanation
    
    def _calculate_feature_importance(self,
                                     feature_vector: FeatureVector,
                                     detection_result: DetectionResult) -> List[Tuple[str, float]]:
        """
        Calculate feature importance for the decision
        
        Uses a combination of statistical deviation and contribution to anomaly score
        """
        importances = []
        feature_dict = feature_vector.to_dict()
        
        # Get contributions from detection result
        contributions = detection_result.feature_contributions
        
        # Calculate importance for each feature
        for feature_name, value in feature_dict.items():
            # Base importance from contribution dict
            if feature_name in contributions:
                importance = abs(contributions[feature_name])
            else:
                # Calculate based on deviation from typical ranges
                importance = self._estimate_importance(feature_name, value)
            
            importances.append((feature_name, importance))
        
        # Sort by importance and return top N
        importances.sort(key=lambda x: x[1], reverse=True)
        
        # Normalize importances to sum to 1
        total = sum(imp for _, imp in importances[:self.top_n_features])
        if total > 0:
            normalized = [
                (name, imp / total)
                for name, imp in importances[:self.top_n_features]
            ]
            return normalized
        
        return importances[:self.top_n_features]
    
    def _estimate_importance(self, feature_name: str, value: float) -> float:
        """Estimate feature importance based on value"""
        # Simple heuristic-based importance
        if 'rate' in feature_name and value > 1000:
            return 0.8
        elif 'entropy' in feature_name and value < 2:
            return 0.7
        elif 'syn_ratio' in feature_name and value > 0.5:
            return 0.9
        elif 'burstiness' in feature_name and value > 2:
            return 0.6
        else:
            return abs(value) / 100.0  # Normalize by arbitrary scale
    
    def _generate_summary(self,
                         detection_result: DetectionResult,
                         mitigation_decision: MitigationDecision,
                         top_features: List[Tuple[str, float]]) -> str:
        """Generate one-line summary"""
        if not detection_result.is_anomaly:
            return "Normal traffic detected. No mitigation required."
        
        top_feature_name = top_features[0][0] if top_features else "unknown"
        action = mitigation_decision.action.value
        score = detection_result.anomaly_score
        
        return (f"Anomaly detected (score: {score:.2f}) - Primary indicator: {top_feature_name}. "
                f"Action: {action}")
    
    def _generate_detailed_explanation(self,
                                      feature_vector: FeatureVector,
                                      detection_result: DetectionResult,
                                      top_features: List[Tuple[str, float]]) -> str:
        """Generate detailed multi-line explanation"""
        lines = []
        
        # Detection summary
        lines.append(f"Detection Stage: {detection_result.stage}")
        lines.append(f"Confidence Level: {detection_result.confidence:.1%}")
        
        if detection_result.triggered_rules:
            lines.append(f"Triggered Rules: {', '.join(detection_result.triggered_rules)}")
        
        lines.append("")
        lines.append("Key Indicators:")
        
        # Explain top features
        feature_dict = feature_vector.to_dict()
        for feature_name, importance in top_features:
            value = feature_dict.get(feature_name, 0)
            description = self.feature_descriptions.get(feature_name, feature_name)
            
            # Generate insight
            insight = self._generate_feature_insight(feature_name, value)
            
            lines.append(f"• {description}")
            lines.append(f"  Value: {value:.2f} | Importance: {importance:.1%}")
            if insight:
                lines.append(f"  → {insight}")
        
        return "\n".join(lines)
    
    def _generate_feature_insight(self, feature_name: str, value: float) -> str:
        """Generate insight for a specific feature"""
        insights = {
            'packet_rate': lambda v: f"Rate is {'extremely high' if v > 10000 else 'elevated' if v > 5000 else 'normal'}",
            'src_ip_entropy': lambda v: f"{'Very low diversity - likely coordinated attack' if v < 1.5 else 'Low diversity' if v < 3 else 'Normal diversity'}",
            'syn_ratio': lambda v: f"{'Possible SYN flood attack' if v > 0.6 else 'Normal SYN ratio' if v < 0.3 else 'Elevated SYN ratio'}",
            'burstiness_index': lambda v: f"{'Extremely bursty traffic pattern' if v > 3 else 'Moderately bursty' if v > 1.5 else 'Consistent traffic'}",
            'syn_ack_ratio': lambda v: f"{'High rate of connection attempts' if v > 2 else 'Normal connection patterns'}",
            'flow_symmetry_score': lambda v: f"{'Very asymmetric - potential one-way attack' if v < 0.3 else 'Normal bidirectional traffic'}"
        }
        
        if feature_name in insights:
            return insights[feature_name](value)
        
        return ""
    
    def _generate_recommendations(self,
                                 detection_result: DetectionResult,
                                 mitigation_decision: MitigationDecision,
                                 top_features: List[Tuple[str, float]]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if not detection_result.is_anomaly:
            recommendations.append("Continue monitoring traffic patterns")
            return recommendations
        
        # Action-specific recommendations
        action = mitigation_decision.action.value
        
        if action == 'drop' or action == 'block':
            recommendations.append("IMMEDIATE: Traffic is being blocked")
            recommendations.append("Investigate source IPs for potential botnet activity")
            recommendations.append("Consider implementing upstream filtering")
            recommendations.append("Review firewall rules and update if needed")
        
        elif action == 'rate_limit':
            recommendations.append("Traffic is being rate-limited")
            recommendations.append("Monitor for legitimate users affected by rate limiting")
            recommendations.append("Consider implementing CAPTCHA for affected endpoints")
        
        elif action == 'traffic_shaping':
            recommendations.append("Traffic is being shaped to reduce impact")
            recommendations.append("Watch for service degradation")
        
        # Feature-specific recommendations
        if top_features:
            top_feature = top_features[0][0]
            
            if 'syn' in top_feature:
                recommendations.append("Enable SYN cookies on target servers")
                recommendations.append("Consider reducing SYN-RECEIVED timeout")
            
            elif 'entropy' in top_feature:
                recommendations.append("Analyze source IP distribution for botnet patterns")
                recommendations.append("Consider geo-blocking if sources are concentrated")
            
            elif 'rate' in top_feature:
                recommendations.append("Verify upstream bandwidth capacity")
                recommendations.append("Consider engaging DDoS mitigation service")
        
        # Confidence-based recommendations
        if detection_result.confidence > 0.8:
            recommendations.append("HIGH CONFIDENCE: Alert SOC team immediately")
        elif detection_result.confidence < 0.5:
            recommendations.append("LOW CONFIDENCE: Continue monitoring before escalating")
        
        return recommendations
