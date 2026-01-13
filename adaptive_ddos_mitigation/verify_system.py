#!/usr/bin/env python3
"""
System Verification Script

Checks that all components are properly installed and functional.
"""

import sys
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_dependencies():
    """Check if required dependencies are installed"""
    print_header("CHECKING DEPENDENCIES")
    
    required = {
        'numpy': 'NumPy',
        'pandas': 'Pandas',
        'sklearn': 'scikit-learn',
        'yaml': 'PyYAML',
        'scapy': 'Scapy (optional for PCAP)'
    }
    
    optional = {
        'tensorflow': 'TensorFlow (for Autoencoder)',
        'matplotlib': 'Matplotlib (for plots)',
        'seaborn': 'Seaborn (for plots)'
    }
    
    print("\nRequired Dependencies:")
    for module, name in required.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - MISSING")
            return False
    
    print("\nOptional Dependencies:")
    for module, name in optional.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ○ {name} - Not installed (optional)")
    
    return True

def check_modules():
    """Check if core modules can be imported"""
    print_header("CHECKING CORE MODULES")
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    modules = [
        ('core.traffic_aggregator', 'Traffic Aggregator'),
        ('core.feature_engineering', 'Feature Engineering'),
        ('core.hybrid_detector', 'Hybrid Detector'),
        ('core.signature_generator', 'Signature Generator'),
        ('core.mitigation_controller', 'Mitigation Controller'),
        ('core.explainability', 'Explainability Engine'),
        ('models.ml_ensemble', 'ML Ensemble'),
        ('adaptive_ddos_system', 'Main System')
    ]
    
    all_ok = True
    for module, name in modules:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ✗ {name} - ERROR: {e}")
            all_ok = False
    
    return all_ok

def check_config():
    """Check if configuration file exists"""
    print_header("CHECKING CONFIGURATION")
    
    config_path = Path(__file__).parent / 'config' / 'system_config.yaml'
    
    if config_path.exists():
        print(f"  ✓ Configuration file found: {config_path}")
        return True
    else:
        print(f"  ✗ Configuration file not found: {config_path}")
        return False

def run_quick_test():
    """Run a quick functionality test"""
    print_header("RUNNING QUICK TEST")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from adaptive_ddos_system import AdaptiveDDoSMitigationSystem
        
        print("  → Initializing system...")
        config_path = Path(__file__).parent / "config" / "system_config.yaml"
        system = AdaptiveDDoSMitigationSystem(str(config_path))
        
        print("  → Training on 10 windows...")
        system.train(num_windows=10)
        
        print("  → Running mini simulation...")
        results = system.run_simulation(duration=10.0, attack_start=5.0, attack_duration=3.0)
        
        anomalies = sum(1 for r in results if r['is_anomaly'])
        print(f"  ✓ Test complete! Processed {len(results)} windows, detected {anomalies} anomalies")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verification checks"""
    print("\n" + "█"*60)
    print("  ADAPTIVE DDOS MITIGATION SYSTEM")
    print("  System Verification")
    print("█"*60)
    
    results = []
    
    # Check dependencies
    results.append(("Dependencies", check_dependencies()))
    
    # Check modules
    results.append(("Core Modules", check_modules()))
    
    # Check configuration
    results.append(("Configuration", check_config()))
    
    # Run quick test
    results.append(("Functionality Test", run_quick_test()))
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    all_passed = all(passed for _, passed in results)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name:.<30} {status}")
    
    print()
    
    if all_passed:
        print("  🎉 ALL CHECKS PASSED!")
        print("  System is ready to use.")
        print("\n  Next steps:")
        print("    cd demo")
        print("    python quickstart.py")
    else:
        print("  ⚠️  SOME CHECKS FAILED")
        print("  Please install missing dependencies:")
        print("    pip install -r requirements.txt")
    
    print("\n" + "█"*60 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
