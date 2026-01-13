"""
Advanced Feature Engineering Module

Extracts comprehensive features from traffic windows:
- Temporal: inter-arrival variance, burstiness
- Statistical: entropy, distributions
- Protocol: TCP/UDP/ICMP ratios, flag analysis
- Flow-level: session characteristics, symmetry
"""

import logging
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from scipy import stats
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler

from .traffic_aggregator import TrafficWindow


@dataclass
class FeatureVector:
    """Structured feature vector with metadata"""
    features: np.ndarray
    feature_names: List[str]
    timestamp: float
    raw_stats: Dict
    window_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format"""
        return {name: value for name, value in zip(self.feature_names, self.features)}


class FeatureEngineer:
    """
    Advanced feature extraction from traffic windows.
    
    Produces normalized, ML-ready feature vectors with comprehensive
    temporal, statistical, protocol, and flow-level characteristics.
    """
    
    def __init__(self, 
                 normalization: str = "minmax",
                 enable_temporal: bool = True,
                 enable_statistical: bool = True,
                 enable_protocol: bool = True,
                 enable_flow: bool = True):
        """
        Initialize feature engineer
        
        Args:
            normalization: Normalization method (minmax, standard, robust)
            enable_temporal: Extract temporal features
            enable_statistical: Extract statistical features
            enable_protocol: Extract protocol features
            enable_flow: Extract flow-level features
        """
        self.normalization = normalization
        self.enable_temporal = enable_temporal
        self.enable_statistical = enable_statistical
        self.enable_protocol = enable_protocol
        self.enable_flow = enable_flow
        
        self.logger = logging.getLogger(__name__)
        self.scaler = self._get_scaler(normalization)
        self.is_fitted = False
        
        # Feature name registry
        self.feature_names = self._build_feature_names()
        
    def _get_scaler(self, method: str):
        """Get appropriate scaler"""
        if method == "minmax":
            return MinMaxScaler()
        elif method == "standard":
            return StandardScaler()
        elif method == "robust":
            return RobustScaler()
        else:
            self.logger.warning(f"Unknown normalization: {method}, using minmax")
            return MinMaxScaler()
    
    def _build_feature_names(self) -> List[str]:
        """Build ordered list of feature names"""
        names = []
        
        # Basic statistics
        names.extend([
            "packet_count",
            "byte_count",
            "avg_packet_size",
            "packet_rate",
            "byte_rate"
        ])
        
        if self.enable_temporal:
            names.extend([
                "inter_arrival_mean",
                "inter_arrival_std",
                "inter_arrival_variance",
                "burstiness_index",
                "coefficient_of_variation"
            ])
        
        if self.enable_statistical:
            names.extend([
                "src_ip_entropy",
                "dst_ip_entropy",
                "src_port_entropy",
                "dst_port_entropy",
                "packet_size_entropy",
                "packet_size_std",
                "unique_src_ips",
                "unique_dst_ips",
                "src_dst_ratio"
            ])
        
        if self.enable_protocol:
            names.extend([
                "tcp_ratio",
                "udp_ratio",
                "icmp_ratio",
                "syn_ratio",
                "ack_ratio",
                "fin_ratio",
                "rst_ratio",
                "syn_ack_ratio"
            ])
        
        if self.enable_flow:
            names.extend([
                "flow_count",
                "avg_flow_packets",
                "avg_flow_duration",
                "max_flow_packets",
                "flow_symmetry_score",
                "short_flow_ratio"
            ])
        
        return names
    
    def extract_features(self, window: TrafficWindow) -> FeatureVector:
        """
        Extract all enabled features from a traffic window
        
        Args:
            window: TrafficWindow object
            
        Returns:
            FeatureVector with normalized features
        """
        features = []
        raw_stats = {}
        
        # Basic statistics
        basic = self._extract_basic_features(window)
        features.extend(basic['values'])
        raw_stats.update(basic['stats'])
        
        # Temporal features
        if self.enable_temporal:
            temporal = self._extract_temporal_features(window)
            features.extend(temporal['values'])
            raw_stats.update(temporal['stats'])
        
        # Statistical features
        if self.enable_statistical:
            statistical = self._extract_statistical_features(window)
            features.extend(statistical['values'])
            raw_stats.update(statistical['stats'])
        
        # Protocol features
        if self.enable_protocol:
            protocol = self._extract_protocol_features(window)
            features.extend(protocol['values'])
            raw_stats.update(protocol['stats'])
        
        # Flow features
        if self.enable_flow:
            flow = self._extract_flow_features(window)
            features.extend(flow['values'])
            raw_stats.update(flow['stats'])
        
        feature_array = np.array(features, dtype=np.float64)
        
        # Handle NaN/Inf values
        feature_array = np.nan_to_num(feature_array, nan=0.0, posinf=1e6, neginf=-1e6)
        
        return FeatureVector(
            features=feature_array,
            feature_names=self.feature_names,
            timestamp=window.start_time,
            raw_stats=raw_stats,
            window_id=f"window_{window.start_time}"
        )
    
    def _extract_basic_features(self, window: TrafficWindow) -> Dict:
        """Extract basic traffic statistics"""
        duration = window.get_duration()
        duration = max(duration, 0.001)  # Avoid division by zero
        
        packet_count = window.packet_count
        byte_count = window.byte_count
        avg_packet_size = byte_count / packet_count if packet_count > 0 else 0
        packet_rate = window.get_packet_rate()
        byte_rate = window.get_byte_rate()
        
        return {
            'values': [packet_count, byte_count, avg_packet_size, packet_rate, byte_rate],
            'stats': {
                'packet_count': packet_count,
                'byte_count': byte_count,
                'avg_packet_size': avg_packet_size,
                'packet_rate': packet_rate,
                'byte_rate': byte_rate
            }
        }
    
    def _extract_temporal_features(self, window: TrafficWindow) -> Dict:
        """Extract temporal characteristics"""
        if len(window.packets) < 2:
            return {
                'values': [0, 0, 0, 0, 0],
                'stats': {}
            }
        
        # Calculate inter-arrival times
        timestamps = [pkt.timestamp for pkt in window.packets]
        inter_arrivals = np.diff(timestamps)
        
        if len(inter_arrivals) == 0:
            return {
                'values': [0, 0, 0, 0, 0],
                'stats': {}
            }
        
        mean_iat = np.mean(inter_arrivals)
        std_iat = np.std(inter_arrivals)
        var_iat = np.var(inter_arrivals)
        
        # Burstiness index (Hurst-like parameter)
        # Higher values indicate more bursty traffic
        burstiness = std_iat / mean_iat if mean_iat > 0 else 0
        
        # Coefficient of variation
        cv = std_iat / mean_iat if mean_iat > 0 else 0
        
        return {
            'values': [mean_iat, std_iat, var_iat, burstiness, cv],
            'stats': {
                'inter_arrival_mean': mean_iat,
                'inter_arrival_std': std_iat,
                'burstiness': burstiness
            }
        }
    
    def _extract_statistical_features(self, window: TrafficWindow) -> Dict:
        """Extract statistical features including entropy"""
        
        # Calculate entropy for different dimensions
        src_ip_entropy = self._calculate_entropy([pkt.src_ip for pkt in window.packets])
        dst_ip_entropy = self._calculate_entropy([pkt.dst_ip for pkt in window.packets])
        
        src_ports = [pkt.src_port for pkt in window.packets if pkt.src_port > 0]
        dst_ports = [pkt.dst_port for pkt in window.packets if pkt.dst_port > 0]
        
        src_port_entropy = self._calculate_entropy(src_ports) if src_ports else 0
        dst_port_entropy = self._calculate_entropy(dst_ports) if dst_ports else 0
        
        # Packet size statistics
        sizes = [pkt.size for pkt in window.packets]
        size_entropy = self._calculate_entropy(sizes)
        size_std = np.std(sizes) if sizes else 0
        
        # Unique counts
        unique_src = len(window.unique_src_ips)
        unique_dst = len(window.unique_dst_ips)
        src_dst_ratio = unique_src / unique_dst if unique_dst > 0 else 0
        
        return {
            'values': [
                src_ip_entropy, dst_ip_entropy,
                src_port_entropy, dst_port_entropy,
                size_entropy, size_std,
                unique_src, unique_dst, src_dst_ratio
            ],
            'stats': {
                'src_ip_entropy': src_ip_entropy,
                'dst_ip_entropy': dst_ip_entropy,
                'unique_src_ips': unique_src,
                'unique_dst_ips': unique_dst
            }
        }
    
    def _extract_protocol_features(self, window: TrafficWindow) -> Dict:
        """Extract protocol distribution features"""
        total = window.packet_count
        if total == 0:
            return {
                'values': [0] * 8,
                'stats': {}
            }
        
        tcp_ratio = window.tcp_count / total
        udp_ratio = window.udp_count / total
        icmp_ratio = window.icmp_count / total
        
        # TCP flag ratios
        syn_ratio = window.syn_count / total
        ack_ratio = window.ack_count / total
        fin_ratio = window.fin_count / total
        rst_ratio = window.rst_count / total
        
        # SYN/ACK ratio (indicator of connection establishment vs. established)
        syn_ack_ratio = window.syn_count / window.ack_count if window.ack_count > 0 else 0
        
        return {
            'values': [
                tcp_ratio, udp_ratio, icmp_ratio,
                syn_ratio, ack_ratio, fin_ratio, rst_ratio,
                syn_ack_ratio
            ],
            'stats': {
                'tcp_ratio': tcp_ratio,
                'syn_ratio': syn_ratio,
                'syn_ack_ratio': syn_ack_ratio
            }
        }
    
    def _extract_flow_features(self, window: TrafficWindow) -> Dict:
        """Extract flow-level features"""
        if not window.flows:
            return {
                'values': [0] * 6,
                'stats': {}
            }
        
        flow_count = len(window.flows)
        
        # Flow packet counts
        flow_packets = [flow['packets'] for flow in window.flows.values()]
        avg_flow_packets = np.mean(flow_packets)
        max_flow_packets = np.max(flow_packets)
        
        # Flow durations
        flow_durations = [
            flow['last_time'] - flow['start_time']
            for flow in window.flows.values()
        ]
        avg_flow_duration = np.mean(flow_durations)
        
        # Flow symmetry (bidirectional flow detection)
        forward_flows = set()
        reverse_flows = set()
        for flow_key in window.flows.keys():
            src_ip, dst_ip, src_port, dst_port, proto = flow_key
            forward_flows.add(flow_key)
            reverse_key = (dst_ip, src_ip, dst_port, src_port, proto)
            if reverse_key in window.flows:
                reverse_flows.add(flow_key)
        
        flow_symmetry = len(reverse_flows) / len(forward_flows) if forward_flows else 0
        
        # Short flow ratio (flows with < 3 packets)
        short_flows = sum(1 for count in flow_packets if count < 3)
        short_flow_ratio = short_flows / flow_count if flow_count > 0 else 0
        
        return {
            'values': [
                flow_count, avg_flow_packets, avg_flow_duration,
                max_flow_packets, flow_symmetry, short_flow_ratio
            ],
            'stats': {
                'flow_count': flow_count,
                'avg_flow_packets': avg_flow_packets,
                'flow_symmetry': flow_symmetry
            }
        }
    
    def _calculate_entropy(self, values: List) -> float:
        """Calculate Shannon entropy of a list of values"""
        if not values:
            return 0.0
        
        # Count occurrences
        unique, counts = np.unique(values, return_counts=True)
        probabilities = counts / len(values)
        
        # Calculate entropy
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        return entropy
    
    def fit_scaler(self, feature_vectors: List[FeatureVector]):
        """
        Fit normalization scaler on training data
        
        Args:
            feature_vectors: List of FeatureVector objects
        """
        if not feature_vectors:
            self.logger.warning("No feature vectors provided for scaler fitting")
            return
        
        features_matrix = np.array([fv.features for fv in feature_vectors])
        self.scaler.fit(features_matrix)
        self.is_fitted = True
        self.logger.info(f"Scaler fitted on {len(feature_vectors)} samples")
    
    def normalize(self, feature_vector: FeatureVector) -> FeatureVector:
        """
        Normalize feature vector using fitted scaler
        
        Args:
            feature_vector: FeatureVector to normalize
            
        Returns:
            Normalized FeatureVector
        """
        if not self.is_fitted:
            self.logger.warning("Scaler not fitted, returning unnormalized features")
            return feature_vector
        
        normalized_features = self.scaler.transform(feature_vector.features.reshape(1, -1))[0]
        
        return FeatureVector(
            features=normalized_features,
            feature_names=feature_vector.feature_names,
            timestamp=feature_vector.timestamp,
            raw_stats=feature_vector.raw_stats,
            window_id=feature_vector.window_id
        )
    
    def extract_and_normalize(self, window: TrafficWindow) -> FeatureVector:
        """
        Extract features and normalize in one step
        
        Args:
            window: TrafficWindow object
            
        Returns:
            Normalized FeatureVector
        """
        feature_vector = self.extract_features(window)
        if self.is_fitted:
            return self.normalize(feature_vector)
        return feature_vector
