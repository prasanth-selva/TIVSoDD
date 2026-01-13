#!/usr/bin/env python3
"""
Demo Script - Real-time DDoS Detection and Mitigation

Demonstrates the adaptive DDoS mitigation system with simulated traffic
and live visualization of detection and mitigation decisions.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adaptive_ddos_system import AdaptiveDDoSMitigationSystem


def print_banner():
    """Print demo banner"""
    print("=" * 80)
    print(" " * 20 + "ADAPTIVE DDOS MITIGATION SYSTEM DEMO")
    print("=" * 80)
    print()


def print_system_status(system):
    """Print current system status"""
    status = system.get_system_status()
    
    print("\n" + "─" * 80)
    print("SYSTEM STATUS:")
    print(f"  Trained: {status['is_trained']}")
    print(f"  Active Signatures: {status['active_signatures']}")
    print(f"  Active Mitigation Rules: {status['active_mitigation_rules']}")
    print(f"  Recent Avg Anomaly Score: {status['recent_avg_anomaly_score']:.3f}")
    print("─" * 80 + "\n")


def print_window_result(result, window_num):
    """Print result for a single window"""
    timestamp = datetime.fromtimestamp(result['timestamp']).strftime('%H:%M:%S')
    
    status = "🔴 ATTACK" if result['is_anomaly'] else "🟢 NORMAL"
    
    print(f"[{timestamp}] Window #{window_num}")
    print(f"  Status: {status}")
    print(f"  Anomaly Score: {result['anomaly_score']:.3f}")
    print(f"  Confidence: {result['confidence']:.3f}")
    print(f"  Action: {result['mitigation_action']}")
    
    if result['matched_signature']:
        print(f"  Matched Signature: {result['matched_signature']}")
    
    stats = result['mitigation_stats']
    print(f"  Packets: {stats['total_packets']} total, "
          f"{stats['packets_dropped']} dropped, "
          f"{stats['packets_allowed']} allowed")
    
    print(f"  Processing Time: {result['processing_time_ms']:.2f} ms")
    
    # Print explanation summary
    if 'explanation' in result:
        exp = result['explanation']
        print(f"\n  Explanation: {exp['summary']}")
        
        if exp['top_features']:
            print("  Top Contributing Features:")
            for feat in exp['top_features'][:3]:
                print(f"    - {feat['name']}: {feat['importance']:.1%}")
    
    print()


def run_basic_demo():
    """Run basic demonstration"""
    print_banner()
    print("DEMO MODE: Simulated Traffic with Attack Injection\n")
    
    # Initialize system
    config_path = Path(__file__).parent.parent / "config" / "system_config.yaml"
    print(f"Loading configuration from: {config_path}")
    
    system = AdaptiveDDoSMitigationSystem(str(config_path))
    
    # Train the system
    print("\n[1/3] Training system on normal traffic...")
    system.train(num_windows=50)
    print("     ✓ Training complete\n")
    
    # Display initial status
    print_system_status(system)
    
    # Run simulation
    print("[2/3] Running simulation with attack injection...")
    print("     - Normal traffic: 0-20s")
    print("     - Attack period: 20-35s (15s duration)")
    print("     - Recovery: 35-60s\n")
    
    results = system.run_simulation(
        duration=60.0,
        attack_start=20.0,
        attack_duration=15.0,
        base_rate=1000,
        attack_multiplier=10.0
    )
    
    # Display results
    print("\n[3/3] Simulation Results:\n")
    
    # Show a subset of windows
    print("Sample Windows (showing key moments):\n")
    
    # Show normal traffic
    print("═══ NORMAL TRAFFIC ═══")
    for i, result in enumerate(results[:2]):
        print_window_result(result, i + 1)
    
    # Show attack detection
    print("\n═══ ATTACK DETECTED ═══")
    attack_windows = [r for r in results if r['is_anomaly']]
    for i, result in enumerate(attack_windows[:3]):
        idx = results.index(result) + 1
        print_window_result(result, idx)
    
    # Show recovery
    print("\n═══ RECOVERY PHASE ═══")
    for i, result in enumerate(results[-2:]):
        idx = results.index(result) + 1
        print_window_result(result, idx)
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS:")
    print("=" * 80)
    
    total_windows = len(results)
    anomalies_detected = sum(1 for r in results if r['is_anomaly'])
    total_packets = sum(r['mitigation_stats']['total_packets'] for r in results)
    total_dropped = sum(r['mitigation_stats']['packets_dropped'] for r in results)
    avg_processing_time = sum(r['processing_time_ms'] for r in results) / total_windows
    
    print(f"Total Windows Processed: {total_windows}")
    print(f"Anomalies Detected: {anomalies_detected} ({anomalies_detected/total_windows*100:.1f}%)")
    print(f"Total Packets: {total_packets}")
    print(f"Packets Dropped: {total_dropped} ({total_dropped/total_packets*100:.1f}%)")
    print(f"Average Processing Time: {avg_processing_time:.2f} ms/window")
    
    # Final system status
    print_system_status(system)
    
    # Export detailed results
    output_dir = Path(__file__).parent.parent / "demo_output"
    output_dir.mkdir(exist_ok=True)
    
    results_file = output_dir / f"demo_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results exported to: {results_file}")
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)


def print_soc_report_demo(system, result):
    """Print a sample SOC report"""
    print("\n" + "=" * 80)
    print("SAMPLE SOC INCIDENT REPORT")
    print("=" * 80 + "\n")
    
    if 'explanation' in result:
        # This would normally come from the explanation object
        print("Generating SOC-friendly report...")
        print()
        
        exp = result['explanation']
        print(f"Incident ID: {exp['decision_id']}")
        print(f"Timestamp: {exp['datetime']}")
        print(f"Severity: {'HIGH' if result['anomaly_score'] > 0.7 else 'MEDIUM' if result['anomaly_score'] > 0.5 else 'LOW'}")
        print(f"Status: {'ATTACK DETECTED' if result['is_anomaly'] else 'NORMAL'}")
        print()
        print(f"Summary: {exp['summary']}")
        print()
        print("Recommended Actions:")
        for i, action in enumerate(exp['recommended_actions'], 1):
            print(f"  {i}. {action}")
        print()


if __name__ == "__main__":
    try:
        run_basic_demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nError running demo: {e}")
        import traceback
        traceback.print_exc()
