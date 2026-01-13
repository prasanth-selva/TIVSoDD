"""
Traffic Capture & Aggregation Module

High-performance traffic aggregation with sliding windows.
Supports PCAP input and simulated real-time streams.
Designed to be replaceable with eBPF/XDP in production.
"""

import time
import logging
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Iterator
from datetime import datetime, timedelta
import numpy as np

try:
    from scapy.all import rdpcap, PcapReader, Packet, IP, TCP, UDP, ICMP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    logging.warning("Scapy not available. PCAP functionality limited.")


@dataclass
class PacketMetadata:
    """Lightweight packet metadata for aggregation"""
    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str  # TCP, UDP, ICMP, OTHER
    size: int
    flags: str = ""  # TCP flags if applicable
    
    
@dataclass
class TrafficWindow:
    """Aggregated traffic statistics for a time window"""
    start_time: float
    end_time: float
    packet_count: int = 0
    byte_count: int = 0
    packets: List[PacketMetadata] = field(default_factory=list)
    
    # Protocol distribution
    tcp_count: int = 0
    udp_count: int = 0
    icmp_count: int = 0
    other_count: int = 0
    
    # TCP-specific
    syn_count: int = 0
    ack_count: int = 0
    fin_count: int = 0
    rst_count: int = 0
    
    # Source tracking
    unique_src_ips: set = field(default_factory=set)
    unique_dst_ips: set = field(default_factory=set)
    unique_src_ports: set = field(default_factory=set)
    unique_dst_ports: set = field(default_factory=set)
    
    # Flow tracking
    flows: Dict[Tuple, dict] = field(default_factory=dict)
    
    def add_packet(self, pkt: PacketMetadata):
        """Add packet to window and update statistics"""
        self.packets.append(pkt)
        self.packet_count += 1
        self.byte_count += pkt.size
        
        # Protocol counts
        if pkt.protocol == "TCP":
            self.tcp_count += 1
            if "S" in pkt.flags:
                self.syn_count += 1
            if "A" in pkt.flags:
                self.ack_count += 1
            if "F" in pkt.flags:
                self.fin_count += 1
            if "R" in pkt.flags:
                self.rst_count += 1
        elif pkt.protocol == "UDP":
            self.udp_count += 1
        elif pkt.protocol == "ICMP":
            self.icmp_count += 1
        else:
            self.other_count += 1
        
        # Unique tracking
        self.unique_src_ips.add(pkt.src_ip)
        self.unique_dst_ips.add(pkt.dst_ip)
        if pkt.src_port > 0:
            self.unique_src_ports.add(pkt.src_port)
        if pkt.dst_port > 0:
            self.unique_dst_ports.add(pkt.dst_port)
        
        # Flow tracking (5-tuple)
        flow_key = (pkt.src_ip, pkt.dst_ip, pkt.src_port, pkt.dst_port, pkt.protocol)
        if flow_key not in self.flows:
            self.flows[flow_key] = {
                'packets': 0,
                'bytes': 0,
                'start_time': pkt.timestamp,
                'last_time': pkt.timestamp
            }
        self.flows[flow_key]['packets'] += 1
        self.flows[flow_key]['bytes'] += pkt.size
        self.flows[flow_key]['last_time'] = pkt.timestamp
    
    def get_duration(self) -> float:
        """Get window duration in seconds"""
        return self.end_time - self.start_time
    
    def get_packet_rate(self) -> float:
        """Get packets per second"""
        duration = self.get_duration()
        return self.packet_count / duration if duration > 0 else 0
    
    def get_byte_rate(self) -> float:
        """Get bytes per second"""
        duration = self.get_duration()
        return self.byte_count / duration if duration > 0 else 0


class TrafficAggregator:
    """
    High-speed traffic aggregation with sliding windows.
    
    Designed for production use with potential eBPF/XDP replacement.
    Supports both PCAP files and simulated real-time streams.
    """
    
    def __init__(self, 
                 window_size: float = 5.0,
                 overlap: float = 0.5,
                 max_packets_per_window: int = 100000):
        """
        Initialize traffic aggregator
        
        Args:
            window_size: Window duration in seconds
            overlap: Overlap fraction (0.0 to 1.0)
            max_packets_per_window: Maximum packets to store per window
        """
        self.window_size = window_size
        self.overlap = overlap
        self.slide_interval = window_size * (1 - overlap)
        self.max_packets_per_window = max_packets_per_window
        
        self.logger = logging.getLogger(__name__)
        self.current_windows = deque(maxlen=10)  # Keep last 10 windows
        self.packet_buffer = deque(maxlen=max_packets_per_window * 2)
        
    def parse_packet(self, scapy_pkt: 'Packet') -> Optional[PacketMetadata]:
        """
        Parse Scapy packet to lightweight metadata
        
        Args:
            scapy_pkt: Scapy packet object
            
        Returns:
            PacketMetadata or None if parsing fails
        """
        if not SCAPY_AVAILABLE:
            return None
            
        try:
            timestamp = float(scapy_pkt.time)
            size = len(scapy_pkt)
            
            # Extract IP layer
            if not scapy_pkt.haslayer(IP):
                return None
                
            ip_layer = scapy_pkt[IP]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            
            # Extract transport layer
            src_port = 0
            dst_port = 0
            protocol = "OTHER"
            flags = ""
            
            if scapy_pkt.haslayer(TCP):
                tcp_layer = scapy_pkt[TCP]
                src_port = tcp_layer.sport
                dst_port = tcp_layer.dport
                protocol = "TCP"
                flags = str(tcp_layer.flags)
            elif scapy_pkt.haslayer(UDP):
                udp_layer = scapy_pkt[UDP]
                src_port = udp_layer.sport
                dst_port = udp_layer.dport
                protocol = "UDP"
            elif scapy_pkt.haslayer(ICMP):
                protocol = "ICMP"
            
            return PacketMetadata(
                timestamp=timestamp,
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=protocol,
                size=size,
                flags=flags
            )
        except Exception as e:
            self.logger.debug(f"Failed to parse packet: {e}")
            return None
    
    def aggregate_pcap(self, pcap_path: str) -> Iterator[TrafficWindow]:
        """
        Aggregate traffic from PCAP file into sliding windows
        
        Args:
            pcap_path: Path to PCAP file
            
        Yields:
            TrafficWindow objects
        """
        if not SCAPY_AVAILABLE:
            self.logger.error("Scapy not available for PCAP processing")
            return
        
        self.logger.info(f"Processing PCAP: {pcap_path}")
        
        try:
            packets = rdpcap(pcap_path)
            self.logger.info(f"Loaded {len(packets)} packets from PCAP")
            
            # Parse all packets
            parsed_packets = []
            for pkt in packets:
                parsed = self.parse_packet(pkt)
                if parsed:
                    parsed_packets.append(parsed)
            
            self.logger.info(f"Successfully parsed {len(parsed_packets)} packets")
            
            # Create sliding windows
            if not parsed_packets:
                return
            
            start_time = parsed_packets[0].timestamp
            end_time = parsed_packets[-1].timestamp
            current_window_start = start_time
            
            while current_window_start < end_time:
                window_end = current_window_start + self.window_size
                window = TrafficWindow(
                    start_time=current_window_start,
                    end_time=window_end
                )
                
                # Add packets to window
                for pkt in parsed_packets:
                    if current_window_start <= pkt.timestamp < window_end:
                        window.add_packet(pkt)
                
                if window.packet_count > 0:
                    yield window
                
                current_window_start += self.slide_interval
                
        except Exception as e:
            self.logger.error(f"Error processing PCAP: {e}")
            raise
    
    def simulate_realtime_stream(self, 
                                  base_rate: int = 1000,
                                  duration: float = 60.0,
                                  attack_start: float = 20.0,
                                  attack_duration: float = 15.0,
                                  attack_multiplier: float = 10.0) -> Iterator[TrafficWindow]:
        """
        Simulate real-time traffic stream with attack injection
        
        Args:
            base_rate: Normal packets per second
            duration: Total simulation duration
            attack_start: When attack starts (seconds)
            attack_duration: Attack duration (seconds)
            attack_multiplier: Attack traffic multiplier
            
        Yields:
            TrafficWindow objects in real-time
        """
        self.logger.info("Starting simulated traffic stream")
        
        start_time = time.time()
        current_window_start = start_time
        window = TrafficWindow(
            start_time=current_window_start,
            end_time=current_window_start + self.window_size
        )
        
        packet_id = 0
        
        while time.time() - start_time < duration:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Determine if we're in attack period
            in_attack = attack_start <= elapsed < (attack_start + attack_duration)
            current_rate = base_rate * attack_multiplier if in_attack else base_rate
            
            # Generate packets for this tick
            packets_this_tick = int(current_rate * 0.01)  # 10ms ticks
            
            for _ in range(packets_this_tick):
                # Generate simulated packet
                pkt = self._generate_simulated_packet(
                    current_time, 
                    packet_id,
                    is_attack=in_attack
                )
                packet_id += 1
                
                # Check if packet belongs to current window
                if current_window_start <= pkt.timestamp < window.end_time:
                    window.add_packet(pkt)
                else:
                    # Window complete, yield it
                    if window.packet_count > 0:
                        yield window
                    
                    # Start new window
                    current_window_start += self.slide_interval
                    window = TrafficWindow(
                        start_time=current_window_start,
                        end_time=current_window_start + self.window_size
                    )
                    window.add_packet(pkt)
            
            # Small sleep to simulate real-time
            time.sleep(0.01)
        
        # Yield final window
        if window.packet_count > 0:
            yield window
    
    def _generate_simulated_packet(self, 
                                     timestamp: float, 
                                     packet_id: int,
                                     is_attack: bool = False) -> PacketMetadata:
        """Generate a simulated packet with realistic characteristics"""
        
        if is_attack:
            # Attack traffic characteristics
            src_ip = f"192.168.{np.random.randint(0, 255)}.{np.random.randint(1, 255)}"
            dst_ip = "10.0.0.1"  # Target server
            protocol = np.random.choice(["TCP", "UDP", "ICMP"], p=[0.6, 0.3, 0.1])
            size = np.random.choice([64, 128, 512, 1024], p=[0.6, 0.2, 0.15, 0.05])
            
            if protocol == "TCP":
                flags = "S"  # SYN flood
                src_port = np.random.randint(1024, 65535)
                dst_port = np.random.choice([80, 443, 8080])
            else:
                flags = ""
                src_port = np.random.randint(1024, 65535) if protocol == "UDP" else 0
                dst_port = np.random.choice([53, 80, 443]) if protocol == "UDP" else 0
        else:
            # Normal traffic characteristics
            src_ip = f"10.0.{np.random.randint(1, 5)}.{np.random.randint(1, 255)}"
            dst_ip = f"10.0.{np.random.randint(1, 5)}.{np.random.randint(1, 255)}"
            protocol = np.random.choice(["TCP", "UDP"], p=[0.8, 0.2])
            size = int(np.random.normal(800, 400))
            size = max(64, min(size, 1500))
            
            if protocol == "TCP":
                flags = np.random.choice(["S", "A", "SA", "FA"], p=[0.1, 0.6, 0.2, 0.1])
                src_port = np.random.randint(1024, 65535)
                dst_port = np.random.choice([80, 443, 22, 3306, 5432])
            else:
                flags = ""
                src_port = np.random.randint(1024, 65535)
                dst_port = 53
        
        return PacketMetadata(
            timestamp=timestamp,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            size=size,
            flags=flags
        )
