#!/usr/bin/env python3
"""
Quick Start Script - Minimal Example

Demonstrates the simplest possible usage of the system.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from adaptive_ddos_system import AdaptiveDDoSMitigationSystem


def main():
    print("Adaptive DDoS Mitigation System - Quick Start\n")
    
    # 1. Initialize system
    print("[1/3] Initializing system...")
    config_path = Path(__file__).parent.parent / "config" / "system_config.yaml"
    system = AdaptiveDDoSMitigationSystem(str(config_path))
    
    # 2. Train on normal traffic
    print("[2/3] Training on simulated normal traffic...")
    system.train(num_windows=30)
    
    # 3. Run simulation with attack
    print("[3/3] Running attack simulation...")
    results = system.run_simulation(
        duration=30.0,
        attack_start=10.0,
        attack_duration=10.0
    )
    
    # Display summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    anomalies = sum(1 for r in results if r['is_anomaly'])
    print(f"Windows processed: {len(results)}")
    print(f"Anomalies detected: {anomalies}")
    print(f"Detection rate: {anomalies/len(results)*100:.1f}%")
    
    # Show one attack window details
    attack_result = next((r for r in results if r['is_anomaly']), None)
    if attack_result:
        print("\nSample Attack Detection:")
        print(f"  Anomaly Score: {attack_result['anomaly_score']:.2f}")
        print(f"  Action Taken: {attack_result['mitigation_action']}")
        print(f"  Explanation: {attack_result['explanation']['summary']}")
    
    print("\n✓ Quick start complete!")


if __name__ == "__main__":
    main()
