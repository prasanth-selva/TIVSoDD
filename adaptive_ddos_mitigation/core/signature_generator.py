"""
Auto-Signature Generation Module

Automatically extracts attack fingerprints when anomalies are confirmed.
Generates temporary mitigation signatures with expiry logic.
"""

import time
import logging
import numpy as np
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import hashlib

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.traffic_aggregator import TrafficWindow
from core.feature_engineering import FeatureVector


@dataclass
class AttackSignature:
    """Attack fingerprint signature"""
    signature_id: str
    creation_time: float
    expiry_time: float
    confidence: float
    
    # Fingerprint characteristics
    dominant_protocols: List[str]
    packet_size_distribution: Dict[str, float]  # ranges -> probability
    rate_characteristics: Dict[str, float]
    source_patterns: Dict[str, any]
    timing_patterns: Dict[str, float]
    
    # Tracking
    match_count: int = 0
    last_match_time: float = 0
    false_positive_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if signature has expired"""
        return time.time() > self.expiry_time
    
    def should_extend(self, current_time: float, extension_seconds: float = 300) -> bool:
        """Check if signature should be extended"""
        # Extend if actively matching
        if current_time - self.last_match_time < 60 and self.match_count > 5:
            return True
        return False
    
    def extend_ttl(self, extension_seconds: float = 300):
        """Extend signature time-to-live"""
        self.expiry_time = time.time() + extension_seconds
    
    def record_match(self):
        """Record a signature match"""
        self.match_count += 1
        self.last_match_time = time.time()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'signature_id': self.signature_id,
            'creation_time': self.creation_time,
            'expiry_time': self.expiry_time,
            'confidence': self.confidence,
            'dominant_protocols': self.dominant_protocols,
            'packet_size_distribution': self.packet_size_distribution,
            'rate_characteristics': self.rate_characteristics,
            'match_count': self.match_count,
            'age_seconds': time.time() - self.creation_time
        }


class SignatureGenerator:
    """
    Automatic attack signature generation.
    
    Analyzes confirmed attack traffic to extract dominant patterns
    and create reusable mitigation signatures.
    """
    
    def __init__(self,
                 min_attack_duration: float = 10.0,
                 signature_ttl: float = 300.0,
                 max_signatures: int = 100):
        """
        Initialize signature generator
        
        Args:
            min_attack_duration: Minimum attack duration before creating signature
            signature_ttl: Default signature time-to-live (seconds)
            max_signatures: Maximum number of active signatures
        """
        self.min_attack_duration = min_attack_duration
        self.signature_ttl = signature_ttl
        self.max_signatures = max_signatures
        
        self.logger = logging.getLogger(__name__)
        
        # Active signatures
        self.signatures: Dict[str, AttackSignature] = {}
        
        # Attack observation buffers
        self.attack_windows = []
        self.attack_start_time = None
    
    def observe_attack(self, window: TrafficWindow, feature_vector: FeatureVector):
        """
        Observe attack traffic for signature generation
        
        Args:
            window: Traffic window containing attack
            feature_vector: Extracted features
        """
        if self.attack_start_time is None:
            self.attack_start_time = window.start_time
        
        self.attack_windows.append((window, feature_vector))
        
        # Check if we have enough data to generate signature
        attack_duration = window.end_time - self.attack_start_time
        
        if attack_duration >= self.min_attack_duration and len(self.attack_windows) >= 3:
            self._generate_signature()
    
    def reset_attack_observation(self):
        """Reset attack observation buffer"""
        self.attack_windows = []
        self.attack_start_time = None
    
    def _generate_signature(self):
        """Generate signature from observed attack windows"""
        if not self.attack_windows:
            return
        
        self.logger.info(f"Generating signature from {len(self.attack_windows)} attack windows")
        
        # Extract fingerprint
        fingerprint = self._extract_fingerprint(self.attack_windows)
        
        # Create signature
        signature_id = self._generate_signature_id(fingerprint)
        
        # Check if signature already exists
        if signature_id in self.signatures:
            self.logger.debug(f"Signature {signature_id} already exists, extending TTL")
            self.signatures[signature_id].extend_ttl(self.signature_ttl)
            return
        
        # Create new signature
        signature = AttackSignature(
            signature_id=signature_id,
            creation_time=time.time(),
            expiry_time=time.time() + self.signature_ttl,
            confidence=self._calculate_signature_confidence(fingerprint),
            dominant_protocols=fingerprint['protocols'],
            packet_size_distribution=fingerprint['packet_sizes'],
            rate_characteristics=fingerprint['rates'],
            source_patterns=fingerprint['sources'],
            timing_patterns=fingerprint['timing']
        )
        
        # Add signature
        self.signatures[signature_id] = signature
        self.logger.info(f"Created signature {signature_id} (confidence: {signature.confidence:.2f})")
        
        # Cleanup old signatures if needed
        self._cleanup_signatures()
        
        # Reset observation buffer
        self.reset_attack_observation()
    
    def _extract_fingerprint(self, attack_windows: List) -> Dict:
        """Extract attack fingerprint from windows"""
        all_packets = []
        all_features = []
        
        for window, feature_vector in attack_windows:
            all_packets.extend(window.packets)
            all_features.append(feature_vector)
        
        fingerprint = {}
        
        # Protocol distribution
        protocol_counts = Counter([pkt.protocol for pkt in all_packets])
        total_packets = len(all_packets)
        protocols = [
            proto for proto, count in protocol_counts.most_common(3)
            if count / total_packets > 0.1  # At least 10%
        ]
        fingerprint['protocols'] = protocols
        
        # Packet size distribution
        sizes = [pkt.size for pkt in all_packets]
        size_ranges = {
            'tiny': (0, 100),
            'small': (100, 500),
            'medium': (500, 1000),
            'large': (1000, 1500)
        }
        
        size_dist = {}
        for range_name, (min_size, max_size) in size_ranges.items():
            count = sum(1 for s in sizes if min_size <= s < max_size)
            size_dist[range_name] = count / total_packets if total_packets > 0 else 0
        
        fingerprint['packet_sizes'] = size_dist
        
        # Rate characteristics
        rates = [fv.raw_stats.get('packet_rate', 0) for _, fv in attack_windows]
        fingerprint['rates'] = {
            'mean_rate': float(np.mean(rates)),
            'max_rate': float(np.max(rates)),
            'std_rate': float(np.std(rates))
        }
        
        # Source patterns
        src_ips = [pkt.src_ip for pkt in all_packets]
        unique_srcs = len(set(src_ips))
        fingerprint['sources'] = {
            'unique_count': unique_srcs,
            'diversity': unique_srcs / total_packets if total_packets > 0 else 0,
            'top_sources': [ip for ip, _ in Counter(src_ips).most_common(10)]
        }
        
        # Timing patterns
        if len(all_packets) > 1:
            timestamps = [pkt.timestamp for pkt in all_packets]
            inter_arrivals = np.diff(timestamps)
            fingerprint['timing'] = {
                'mean_iat': float(np.mean(inter_arrivals)),
                'std_iat': float(np.std(inter_arrivals)),
                'burstiness': float(np.std(inter_arrivals) / np.mean(inter_arrivals))
                              if np.mean(inter_arrivals) > 0 else 0
            }
        else:
            fingerprint['timing'] = {'mean_iat': 0, 'std_iat': 0, 'burstiness': 0}
        
        return fingerprint
    
    def _generate_signature_id(self, fingerprint: Dict) -> str:
        """Generate unique signature ID from fingerprint"""
        # Create a hash of key fingerprint characteristics
        key_features = [
            str(fingerprint['protocols']),
            str(sorted(fingerprint['packet_sizes'].items())),
            f"{fingerprint['rates']['mean_rate']:.0f}",
            f"{fingerprint['sources']['unique_count']}"
        ]
        
        signature_string = "_".join(key_features)
        hash_object = hashlib.md5(signature_string.encode())
        return f"sig_{hash_object.hexdigest()[:12]}"
    
    def _calculate_signature_confidence(self, fingerprint: Dict) -> float:
        """Calculate confidence score for signature"""
        confidence = 0.5  # Base confidence
        
        # More confidence if protocols are consistent
        if len(fingerprint['protocols']) <= 2:
            confidence += 0.2
        
        # More confidence if packet sizes are concentrated
        max_size_prob = max(fingerprint['packet_sizes'].values())
        if max_size_prob > 0.6:
            confidence += 0.15
        
        # More confidence if rate is high
        if fingerprint['rates']['mean_rate'] > 5000:
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def match_signature(self, window: TrafficWindow, feature_vector: FeatureVector) -> Optional[AttackSignature]:
        """
        Check if traffic matches any known attack signature
        
        Args:
            window: Traffic window
            feature_vector: Extracted features
            
        Returns:
            Matching signature or None
        """
        if not self.signatures:
            return None
        
        # Extract current fingerprint
        current_fp = self._extract_fingerprint([(window, feature_vector)])
        
        # Check against all signatures
        best_match = None
        best_score = 0.0
        
        for sig_id, signature in self.signatures.items():
            if signature.is_expired():
                continue
            
            score = self._calculate_match_score(current_fp, signature)
            
            if score > 0.7 and score > best_score:  # 70% match threshold
                best_score = score
                best_match = signature
        
        if best_match:
            best_match.record_match()
            self.logger.debug(f"Traffic matched signature {best_match.signature_id} (score: {best_score:.2f})")
        
        return best_match
    
    def _calculate_match_score(self, fingerprint: Dict, signature: AttackSignature) -> float:
        """Calculate how well a fingerprint matches a signature"""
        score = 0.0
        weights = {
            'protocols': 0.3,
            'packet_sizes': 0.3,
            'rates': 0.2,
            'sources': 0.1,
            'timing': 0.1
        }
        
        # Protocol match
        protocol_overlap = len(set(fingerprint['protocols']) & set(signature.dominant_protocols))
        if signature.dominant_protocols:
            protocol_score = protocol_overlap / len(signature.dominant_protocols)
            score += protocol_score * weights['protocols']
        
        # Packet size distribution similarity
        size_score = 0.0
        for range_name in fingerprint['packet_sizes']:
            fp_prob = fingerprint['packet_sizes'][range_name]
            sig_prob = signature.packet_size_distribution.get(range_name, 0)
            size_score += 1.0 - abs(fp_prob - sig_prob)
        size_score /= len(fingerprint['packet_sizes'])
        score += size_score * weights['packet_sizes']
        
        # Rate similarity
        fp_rate = fingerprint['rates']['mean_rate']
        sig_rate = signature.rate_characteristics['mean_rate']
        if sig_rate > 0:
            rate_score = 1.0 - min(abs(fp_rate - sig_rate) / sig_rate, 1.0)
            score += rate_score * weights['rates']
        
        # Source diversity similarity
        fp_diversity = fingerprint['sources']['diversity']
        sig_diversity = signature.source_patterns['diversity']
        diversity_score = 1.0 - abs(fp_diversity - sig_diversity)
        score += diversity_score * weights['sources']
        
        # Timing similarity
        fp_burstiness = fingerprint['timing']['burstiness']
        sig_burstiness = signature.timing_patterns['burstiness']
        if sig_burstiness > 0:
            timing_score = 1.0 - min(abs(fp_burstiness - sig_burstiness) / sig_burstiness, 1.0)
            score += timing_score * weights['timing']
        
        return score
    
    def _cleanup_signatures(self):
        """Remove expired signatures and enforce max limit"""
        # Remove expired
        expired = [sid for sid, sig in self.signatures.items() if sig.is_expired()]
        for sid in expired:
            del self.signatures[sid]
            self.logger.debug(f"Removed expired signature {sid}")
        
        # Enforce max limit
        if len(self.signatures) > self.max_signatures:
            # Remove least recently matched signatures
            sorted_sigs = sorted(
                self.signatures.items(),
                key=lambda x: x[1].last_match_time
            )
            
            to_remove = len(self.signatures) - self.max_signatures
            for sid, _ in sorted_sigs[:to_remove]:
                del self.signatures[sid]
                self.logger.debug(f"Removed signature {sid} due to limit")
    
    def get_active_signatures(self) -> List[AttackSignature]:
        """Get list of active signatures"""
        self._cleanup_signatures()
        return list(self.signatures.values())
    
    def get_signature_summary(self) -> Dict:
        """Get summary of signature database"""
        active = self.get_active_signatures()
        
        return {
            'total_signatures': len(active),
            'avg_confidence': np.mean([s.confidence for s in active]) if active else 0,
            'total_matches': sum(s.match_count for s in active),
            'signatures': [s.to_dict() for s in active]
        }
