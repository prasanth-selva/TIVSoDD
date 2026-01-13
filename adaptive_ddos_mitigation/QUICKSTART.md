# QUICK START - 3 Steps to Running Demo

## Step 1: Install Dependencies (1 minute)

```bash
cd adaptive_ddos_mitigation
pip install -r requirements.txt
```

**Note**: If TensorFlow installation fails (large download), you can run without it by disabling the autoencoder in `config/system_config.yaml`:

```yaml
ml_ensemble:
  models:
    autoencoder:
      enabled: false
```

## Step 2: Run Quick Demo (30 seconds)

```bash
cd demo
python quickstart.py
```

**Expected Output**:
```
Adaptive DDoS Mitigation System - Quick Start

[1/3] Initializing system...
[2/3] Training on simulated normal traffic...
[3/3] Running attack simulation...

======================================================
SUMMARY
======================================================
Windows processed: 6
Anomalies detected: 2
Detection rate: 33.3%

Sample Attack Detection:
  Anomaly Score: 0.87
  Action Taken: rate_limit
  Explanation: Anomaly detected (score: 0.87) - Primary indicator: packet_rate...

✓ Quick start complete!
```

## Step 3: Explore Full Features

### Option A: Full Real-Time Demo
```bash
python demo_realtime.py
```

Shows detailed detection, mitigation, and explainability for each window.

### Option B: Comparative Evaluation
```bash
python demo_evaluation.py
```

Compares your system against baselines with metrics and plots.

---

## Troubleshooting

### Issue: TensorFlow not installing

**Quick Fix**: Disable autoencoder in config
```yaml
ml_ensemble:
  models:
    autoencoder:
      enabled: false
```

### Issue: Scapy import error

**Solution**:
```bash
# On Ubuntu/Debian
sudo apt-get install tcpdump python3-dev

# Then
pip install scapy
```

### Issue: No plots generated

**Solution**: matplotlib/seaborn not installed
```bash
pip install matplotlib seaborn
```

---

## What to Present

1. **Run `demo_realtime.py`** - Shows live detection
2. **Show the output logs** - Explains each decision
3. **Open `demo_output/demo_results_*.json`** - Detailed results
4. **Run `demo_evaluation.py`** - Shows comparative advantage
5. **Show plots** in `evaluation_results/` folder

---

## Next Steps

- **Customize**: Edit `config/system_config.yaml`
- **Add PCAP**: Place .pcap files and modify demo scripts
- **Extend**: Add features in `core/feature_engineering.py`
- **Deploy**: See `TECHNICAL_DOCUMENTATION.md` for production path

---

**Total time from clone to demo: 2 minutes**
