"""
Evaluation Framework

Benchmarks the adaptive DDoS mitigation system against baselines:
- No defense
- Traditional rate limiting
- Proposed ML-based adaptive system

Metrics: detection latency, mitigation latency, false positives/negatives,
packet drop accuracy, throughput
"""

import time
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    logging.warning("Matplotlib/Seaborn not available. Plotting disabled.")


@dataclass
class EvaluationMetrics:
    """Metrics for evaluation"""
    system_name: str
    
    # Detection metrics
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    
    # Latency metrics (seconds)
    detection_latencies: List[float] = field(default_factory=list)
    mitigation_latencies: List[float] = field(default_factory=list)
    
    # Throughput metrics
    total_packets_processed: int = 0
    attack_packets_seen: int = 0
    legitimate_packets_seen: int = 0
    packets_dropped: int = 0
    packets_allowed: int = 0
    
    # Performance
    cpu_time: float = 0.0
    memory_peak_mb: float = 0.0
    
    def calculate_derived_metrics(self) -> Dict:
        """Calculate derived metrics"""
        # Precision, Recall, F1
        precision = self.true_positives / (self.true_positives + self.false_positives) \
                   if (self.true_positives + self.false_positives) > 0 else 0
        
        recall = self.true_positives / (self.true_positives + self.false_negatives) \
                if (self.true_positives + self.false_negatives) > 0 else 0
        
        f1_score = 2 * (precision * recall) / (precision + recall) \
                  if (precision + recall) > 0 else 0
        
        # Accuracy
        total = self.true_positives + self.false_positives + \
                self.true_negatives + self.false_negatives
        accuracy = (self.true_positives + self.true_negatives) / total if total > 0 else 0
        
        # False positive rate
        fpr = self.false_positives / (self.false_positives + self.true_negatives) \
             if (self.false_positives + self.true_negatives) > 0 else 0
        
        # Packet drop accuracy (how well we drop attack packets vs legitimate)
        attack_drop_rate = 0
        if self.attack_packets_seen > 0:
            # Estimate: we want to drop attack packets
            attack_drops = min(self.packets_dropped, self.attack_packets_seen)
            attack_drop_rate = attack_drops / self.attack_packets_seen
        
        legitimate_keep_rate = 0
        if self.legitimate_packets_seen > 0:
            # Estimate: we want to keep legitimate packets
            legit_kept = max(0, self.packets_allowed - self.attack_packets_seen)
            legitimate_keep_rate = legit_kept / self.legitimate_packets_seen
        
        # Latency statistics
        avg_detection_latency = np.mean(self.detection_latencies) \
                               if self.detection_latencies else 0
        avg_mitigation_latency = np.mean(self.mitigation_latencies) \
                                if self.mitigation_latencies else 0
        
        return {
            'system': self.system_name,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'accuracy': accuracy,
            'false_positive_rate': fpr,
            'attack_drop_rate': attack_drop_rate,
            'legitimate_keep_rate': legitimate_keep_rate,
            'avg_detection_latency_ms': avg_detection_latency * 1000,
            'avg_mitigation_latency_ms': avg_mitigation_latency * 1000,
            'total_packets': self.total_packets_processed,
            'packets_dropped': self.packets_dropped,
            'cpu_time_seconds': self.cpu_time,
            'memory_peak_mb': self.memory_peak_mb
        }


class Evaluator:
    """
    Evaluation framework for DDoS mitigation systems
    """
    
    def __init__(self, output_dir: str = "evaluation_results"):
        """
        Initialize evaluator
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Results storage
        self.results: Dict[str, EvaluationMetrics] = {}
    
    def evaluate_system(self,
                       system_name: str,
                       traffic_stream,
                       attack_ground_truth: List[Tuple[float, float]],
                       system_callback) -> EvaluationMetrics:
        """
        Evaluate a mitigation system
        
        Args:
            system_name: Name of the system being evaluated
            traffic_stream: Iterator of traffic windows
            attack_ground_truth: List of (start_time, end_time) for attacks
            system_callback: Function that processes windows and returns decisions
            
        Returns:
            EvaluationMetrics
        """
        self.logger.info(f"Evaluating system: {system_name}")
        
        metrics = EvaluationMetrics(system_name=system_name)
        
        start_cpu_time = time.process_time()
        
        for window in traffic_stream:
            window_start = window.start_time
            window_end = window.end_time
            
            # Determine ground truth
            is_attack_window = self._is_attack_period(
                window_start, window_end, attack_ground_truth
            )
            
            # Track packets
            metrics.total_packets_processed += window.packet_count
            if is_attack_window:
                metrics.attack_packets_seen += window.packet_count
            else:
                metrics.legitimate_packets_seen += window.packet_count
            
            # Process window with system
            detection_start = time.time()
            result = system_callback(window)
            detection_end = time.time()
            
            # Record detection latency
            detection_latency = detection_end - detection_start
            metrics.detection_latencies.append(detection_latency)
            
            # Evaluate detection
            if result['is_anomaly']:
                if is_attack_window:
                    metrics.true_positives += 1
                else:
                    metrics.false_positives += 1
            else:
                if is_attack_window:
                    metrics.false_negatives += 1
                else:
                    metrics.true_negatives += 1
            
            # Track mitigation
            if 'mitigation_stats' in result:
                stats = result['mitigation_stats']
                metrics.packets_dropped += stats.get('packets_dropped', 0)
                metrics.packets_allowed += stats.get('packets_allowed', 0)
                
                if result['is_anomaly']:
                    # Mitigation latency is time to apply mitigation after detection
                    mitigation_latency = result.get('mitigation_latency', 0)
                    metrics.mitigation_latencies.append(mitigation_latency)
        
        metrics.cpu_time = time.process_time() - start_cpu_time
        
        self.results[system_name] = metrics
        self.logger.info(f"Evaluation complete for {system_name}")
        
        return metrics
    
    def _is_attack_period(self,
                         window_start: float,
                         window_end: float,
                         attack_periods: List[Tuple[float, float]]) -> bool:
        """Check if window overlaps with attack period"""
        for attack_start, attack_end in attack_periods:
            # Check for overlap
            if not (window_end < attack_start or window_start > attack_end):
                return True
        return False
    
    def compare_systems(self) -> pd.DataFrame:
        """
        Compare all evaluated systems
        
        Returns:
            DataFrame with comparison metrics
        """
        if not self.results:
            self.logger.warning("No results to compare")
            return pd.DataFrame()
        
        comparison_data = []
        
        for system_name, metrics in self.results.items():
            derived = metrics.calculate_derived_metrics()
            comparison_data.append(derived)
        
        df = pd.DataFrame(comparison_data)
        return df
    
    def generate_report(self, filename: str = "evaluation_report.txt"):
        """Generate text report"""
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("DDoS MITIGATION SYSTEM EVALUATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            comparison_df = self.compare_systems()
            
            if not comparison_df.empty:
                f.write("COMPARATIVE METRICS:\n")
                f.write("-" * 80 + "\n")
                f.write(comparison_df.to_string(index=False))
                f.write("\n\n")
                
                # Highlight best performers
                f.write("BEST PERFORMERS:\n")
                f.write("-" * 80 + "\n")
                
                metrics_to_maximize = ['precision', 'recall', 'f1_score', 'accuracy',
                                       'attack_drop_rate', 'legitimate_keep_rate']
                metrics_to_minimize = ['false_positive_rate', 'avg_detection_latency_ms',
                                      'avg_mitigation_latency_ms']
                
                for metric in metrics_to_maximize:
                    if metric in comparison_df.columns:
                        best_idx = comparison_df[metric].idxmax()
                        best_system = comparison_df.loc[best_idx, 'system']
                        best_value = comparison_df.loc[best_idx, metric]
                        f.write(f"  Best {metric}: {best_system} ({best_value:.4f})\n")
                
                for metric in metrics_to_minimize:
                    if metric in comparison_df.columns:
                        best_idx = comparison_df[metric].idxmin()
                        best_system = comparison_df.loc[best_idx, 'system']
                        best_value = comparison_df.loc[best_idx, metric]
                        f.write(f"  Lowest {metric}: {best_system} ({best_value:.4f})\n")
                
                f.write("\n")
            
            f.write("=" * 80 + "\n")
        
        self.logger.info(f"Report generated: {output_path}")
        return str(output_path)
    
    def generate_plots(self):
        """Generate comparison plots"""
        if not PLOTTING_AVAILABLE:
            self.logger.warning("Plotting libraries not available")
            return
        
        if not self.results:
            self.logger.warning("No results to plot")
            return
        
        comparison_df = self.compare_systems()
        
        # Set style
        sns.set_style("whitegrid")
        
        # 1. Performance metrics comparison
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('DDoS Mitigation System Performance Comparison', fontsize=16)
        
        # Precision, Recall, F1
        ax = axes[0, 0]
        metrics = ['precision', 'recall', 'f1_score']
        x = np.arange(len(comparison_df))
        width = 0.25
        
        for i, metric in enumerate(metrics):
            if metric in comparison_df.columns:
                ax.bar(x + i * width, comparison_df[metric], width, label=metric.replace('_', ' ').title())
        
        ax.set_xlabel('System')
        ax.set_ylabel('Score')
        ax.set_title('Detection Performance Metrics')
        ax.set_xticks(x + width)
        ax.set_xticklabels(comparison_df['system'], rotation=15, ha='right')
        ax.legend()
        ax.set_ylim([0, 1.1])
        
        # False Positive Rate
        ax = axes[0, 1]
        if 'false_positive_rate' in comparison_df.columns:
            ax.bar(comparison_df['system'], comparison_df['false_positive_rate'])
            ax.set_xlabel('System')
            ax.set_ylabel('Rate')
            ax.set_title('False Positive Rate (Lower is Better)')
            ax.tick_params(axis='x', rotation=15)
        
        # Latency comparison
        ax = axes[1, 0]
        if 'avg_detection_latency_ms' in comparison_df.columns:
            x = np.arange(len(comparison_df))
            width = 0.35
            
            ax.bar(x - width/2, comparison_df['avg_detection_latency_ms'], 
                  width, label='Detection')
            
            if 'avg_mitigation_latency_ms' in comparison_df.columns:
                ax.bar(x + width/2, comparison_df['avg_mitigation_latency_ms'],
                      width, label='Mitigation')
            
            ax.set_xlabel('System')
            ax.set_ylabel('Latency (ms)')
            ax.set_title('Latency Comparison')
            ax.set_xticks(x)
            ax.set_xticklabels(comparison_df['system'], rotation=15, ha='right')
            ax.legend()
        
        # Packet handling accuracy
        ax = axes[1, 1]
        if 'attack_drop_rate' in comparison_df.columns and 'legitimate_keep_rate' in comparison_df.columns:
            x = np.arange(len(comparison_df))
            width = 0.35
            
            ax.bar(x - width/2, comparison_df['attack_drop_rate'], 
                  width, label='Attack Drop Rate')
            ax.bar(x + width/2, comparison_df['legitimate_keep_rate'],
                  width, label='Legitimate Keep Rate')
            
            ax.set_xlabel('System')
            ax.set_ylabel('Rate')
            ax.set_title('Packet Handling Accuracy')
            ax.set_xticks(x)
            ax.set_xticklabels(comparison_df['system'], rotation=15, ha='right')
            ax.legend()
            ax.set_ylim([0, 1.1])
        
        plt.tight_layout()
        plot_path = self.output_dir / "performance_comparison.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Performance plots saved to {plot_path}")
        
        # 2. Resource usage comparison
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle('Resource Usage Comparison', fontsize=14)
        
        if 'cpu_time_seconds' in comparison_df.columns:
            ax1.bar(comparison_df['system'], comparison_df['cpu_time_seconds'])
            ax1.set_xlabel('System')
            ax1.set_ylabel('CPU Time (seconds)')
            ax1.set_title('CPU Usage')
            ax1.tick_params(axis='x', rotation=15)
        
        if 'memory_peak_mb' in comparison_df.columns:
            ax2.bar(comparison_df['system'], comparison_df['memory_peak_mb'])
            ax2.set_xlabel('System')
            ax2.set_ylabel('Memory (MB)')
            ax2.set_title('Peak Memory Usage')
            ax2.tick_params(axis='x', rotation=15)
        
        plt.tight_layout()
        resource_plot_path = self.output_dir / "resource_usage.png"
        plt.savefig(resource_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Resource plots saved to {resource_plot_path}")
    
    def export_results(self, filename: str = "evaluation_results.json"):
        """Export results to JSON"""
        output_path = self.output_dir / filename
        
        export_data = {}
        for system_name, metrics in self.results.items():
            export_data[system_name] = metrics.calculate_derived_metrics()
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Results exported to {output_path}")
        return str(output_path)
