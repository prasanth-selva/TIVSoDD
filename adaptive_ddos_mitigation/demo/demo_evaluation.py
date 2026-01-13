#!/usr/bin/env python3
"""
Evaluation Demo - Comparative System Evaluation

Compares three approaches:
1. No defense (baseline)
2. Traditional rate limiting
3. Adaptive ML-based system
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from adaptive_ddos_system import AdaptiveDDoSMitigationSystem
from evaluation.evaluator import Evaluator
from core.traffic_aggregator import TrafficAggregator


def no_defense_callback(window):
    """Baseline: No defense"""
    return {
        'is_anomaly': False,
        'anomaly_score': 0.0,
        'mitigation_stats': {
            'packets_dropped': 0,
            'packets_allowed': window.packet_count,
            'packets_shaped': 0,
            'total_packets': window.packet_count
        },
        'mitigation_latency': 0
    }


def traditional_rate_limit_callback(window, rate_threshold=5000):
    """Traditional rate limiting"""
    packet_rate = window.get_packet_rate()
    is_attack = packet_rate > rate_threshold
    
    if is_attack:
        # Drop excess packets
        allowed = min(window.packet_count, int(rate_threshold * window.get_duration()))
        dropped = window.packet_count - allowed
    else:
        allowed = window.packet_count
        dropped = 0
    
    return {
        'is_anomaly': is_attack,
        'anomaly_score': 1.0 if is_attack else 0.0,
        'mitigation_stats': {
            'packets_dropped': dropped,
            'packets_allowed': allowed,
            'packets_shaped': 0,
            'total_packets': window.packet_count
        },
        'mitigation_latency': 0.001  # Simulated
    }


def adaptive_ml_callback(system):
    """Adaptive ML-based system"""
    def callback(window):
        result = system.process_window(window)
        return result
    
    return callback


def run_evaluation():
    """Run comparative evaluation"""
    print("=" * 80)
    print("COMPARATIVE EVALUATION: DDoS Mitigation Systems")
    print("=" * 80)
    print()
    
    # Initialize evaluator
    evaluator = Evaluator(output_dir="evaluation_results")
    
    # Initialize adaptive system
    config_path = Path(__file__).parent.parent / "config" / "system_config.yaml"
    adaptive_system = AdaptiveDDoSMitigationSystem(str(config_path))
    
    print("[1/5] Training adaptive system...")
    adaptive_system.train(num_windows=50)
    print("      ✓ Training complete\n")
    
    # Define attack periods for ground truth
    attack_periods = [
        (20.0, 35.0)  # Attack from 20s to 35s
    ]
    
    print("[2/5] Evaluating: No Defense (Baseline)...")
    aggregator1 = TrafficAggregator(window_size=5.0, overlap=0.5)
    stream1 = aggregator1.simulate_realtime_stream(
        base_rate=1000,
        duration=60.0,
        attack_start=20.0,
        attack_duration=15.0,
        attack_multiplier=10.0
    )
    
    metrics1 = evaluator.evaluate_system(
        system_name="No Defense",
        traffic_stream=stream1,
        attack_ground_truth=attack_periods,
        system_callback=no_defense_callback
    )
    print(f"      ✓ Processed {metrics1.total_packets_processed} packets\n")
    
    print("[3/5] Evaluating: Traditional Rate Limiting...")
    aggregator2 = TrafficAggregator(window_size=5.0, overlap=0.5)
    stream2 = aggregator2.simulate_realtime_stream(
        base_rate=1000,
        duration=60.0,
        attack_start=20.0,
        attack_duration=15.0,
        attack_multiplier=10.0
    )
    
    metrics2 = evaluator.evaluate_system(
        system_name="Traditional Rate Limiting",
        traffic_stream=stream2,
        attack_ground_truth=attack_periods,
        system_callback=traditional_rate_limit_callback
    )
    print(f"      ✓ Processed {metrics2.total_packets_processed} packets\n")
    
    print("[4/5] Evaluating: Adaptive ML-Based System...")
    aggregator3 = TrafficAggregator(window_size=5.0, overlap=0.5)
    stream3 = aggregator3.simulate_realtime_stream(
        base_rate=1000,
        duration=60.0,
        attack_start=20.0,
        attack_duration=15.0,
        attack_multiplier=10.0
    )
    
    metrics3 = evaluator.evaluate_system(
        system_name="Adaptive ML System",
        traffic_stream=stream3,
        attack_ground_truth=attack_periods,
        system_callback=adaptive_ml_callback(adaptive_system)
    )
    print(f"      ✓ Processed {metrics3.total_packets_processed} packets\n")
    
    print("[5/5] Generating results...")
    
    # Generate comparison report
    comparison_df = evaluator.compare_systems()
    
    print("\n" + "=" * 80)
    print("COMPARATIVE RESULTS:")
    print("=" * 80 + "\n")
    print(comparison_df.to_string(index=False))
    print()
    
    # Generate detailed report
    report_path = evaluator.generate_report()
    print(f"\nDetailed report saved to: {report_path}")
    
    # Export results
    json_path = evaluator.export_results()
    print(f"JSON results exported to: {json_path}")
    
    # Generate plots
    try:
        evaluator.generate_plots()
        print(f"Plots saved to: {evaluator.output_dir}")
    except Exception as e:
        print(f"Could not generate plots: {e}")
    
    print("\n" + "=" * 80)
    print("KEY INSIGHTS:")
    print("=" * 80)
    
    # Extract key metrics for comparison
    ml_f1 = comparison_df[comparison_df['system'] == 'Adaptive ML System']['f1_score'].values[0]
    trad_f1 = comparison_df[comparison_df['system'] == 'Traditional Rate Limiting']['f1_score'].values[0]
    
    ml_fpr = comparison_df[comparison_df['system'] == 'Adaptive ML System']['false_positive_rate'].values[0]
    trad_fpr = comparison_df[comparison_df['system'] == 'Traditional Rate Limiting']['false_positive_rate'].values[0]
    
    print(f"\n1. Detection Accuracy:")
    print(f"   - Adaptive ML System achieves {ml_f1:.1%} F1-score")
    print(f"   - Traditional approach achieves {trad_f1:.1%} F1-score")
    print(f"   - Improvement: {((ml_f1 - trad_f1) / trad_f1 * 100):.1f}%")
    
    print(f"\n2. False Positive Rate:")
    print(f"   - Adaptive ML System: {ml_fpr:.1%}")
    print(f"   - Traditional approach: {trad_fpr:.1%}")
    
    if ml_fpr < trad_fpr:
        print(f"   - Adaptive system has {((trad_fpr - ml_fpr) / trad_fpr * 100):.1f}% fewer false positives")
    
    print("\n3. Adaptive Capabilities:")
    print("   - ML system learns attack patterns and generates signatures")
    print("   - Graduated mitigation reduces impact on legitimate users")
    print("   - Explainable decisions enable SOC operator understanding")
    
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        run_evaluation()
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user")
    except Exception as e:
        print(f"\n\nError running evaluation: {e}")
        import traceback
        traceback.print_exc()
