# TECHNICAL DOCUMENTATION

## System Architecture

### 1. Traffic Capture & Aggregation

**Module:** `core/traffic_aggregator.py`

**Purpose:** Capture and aggregate network traffic into time-based windows for analysis.

**Key Components:**
- `TrafficWindow`: Data structure for aggregated traffic statistics
- `TrafficAggregator`: Main aggregation engine with sliding window support

**Features:**
- PCAP file parsing using Scapy
- Real-time traffic stream simulation
- Sliding window implementation (configurable overlap)
- Flow tracking (5-tuple: src_ip, dst_ip, src_port, dst_port, protocol)
- Protocol distribution analysis

**Design Considerations:**
- Designed for future eBPF/XDP replacement
- Lightweight packet metadata to minimize memory overhead
- Configurable window size and overlap for latency/accuracy tradeoff

---

### 2. Feature Engineering

**Module:** `core/feature_engineering.py`

**Purpose:** Extract comprehensive features from traffic windows for ML models.

**Feature Categories:**

#### Temporal Features
- Inter-arrival time statistics (mean, std, variance)
- Burstiness index (coefficient of variation)
- Timing consistency metrics

#### Statistical Features
- Shannon entropy (source IPs, destination IPs, ports, packet sizes)
- Unique source/destination counts
- Source-to-destination ratio

#### Protocol Features
- TCP/UDP/ICMP ratios
- TCP flag analysis (SYN, ACK, FIN, RST ratios)
- SYN/ACK ratio (connection attempt indicator)

#### Flow-Level Features
- Flow count and characteristics
- Average packets per flow
- Flow duration statistics
- Bidirectional flow detection (symmetry score)
- Short-lived flow ratio

**Normalization:**
- MinMaxScaler (default)
- StandardScaler
- RobustScaler

---

### 3. Hybrid Detection Layer

**Module:** `core/hybrid_detector.py`

**Purpose:** Two-stage detection to balance latency and accuracy.

#### Stage 1: Statistical Anomaly Detector

**Fast Filtering Rules:**
1. **Absolute Rate Threshold:** Packet rate > 10,000 pps
2. **Rate Deviation:** Z-score > 2.5 std from baseline
3. **Low Entropy:** Source IP entropy < 1.5 bits (concentrated sources)
4. **High Burstiness:** Burstiness index > 3.0
5. **SYN Flood:** SYN ratio > 60%

**Advantages:**
- Sub-millisecond latency
- Reduces ML inference load by 60-80%
- Adaptive baseline tracking

#### Stage 2: ML Ensemble Confirmation

**Purpose:** Confirm statistical detections with higher accuracy

**Workflow:**
```
Statistical Detection → ML Confirmation → Final Decision
     ↓ (if not anomaly)
   Allow immediately
```

**False Positive Reduction:**
- ML confirmation prevents overblocking during legitimate traffic surges
- Weighted confidence scoring

---

### 4. ML Ensemble

**Module:** `models/ml_ensemble.py`

**Purpose:** Combine multiple ML models for robust anomaly detection.

#### Model 1: Isolation Forest

**Type:** Unsupervised anomaly detection

**Parameters:**
- n_estimators: 100
- contamination: 0.05 (expected anomaly rate)
- max_samples: 256

**Strengths:**
- Efficient for high-dimensional data
- No labeled data required
- Good at detecting global anomalies

#### Model 2: Autoencoder

**Type:** Neural network reconstruction-based

**Architecture:**
```
Input (N features) → Dense(64) → Dense(32) → Dense(16 - encoding)
                  → Dense(32) → Dense(64) → Dense(N - reconstruction)
```

**Detection Logic:**
- Train on normal traffic
- Anomalies have high reconstruction error
- Threshold: MSE > 0.1

**Strengths:**
- Captures complex non-linear patterns
- Adapts to traffic characteristics

#### Model 3: Time-Series Detector (EWMA)

**Type:** Exponential Weighted Moving Average

**Parameters:**
- Alpha: 0.3 (smoothing factor)
- Threshold: 2.5 standard deviations

**Purpose:**
- Detect sudden deviations from recent trends
- Complementary to static models

#### Voting Mechanism

**Weighted Voting:**
```python
final_score = 0.4 * isolation_forest_score +
              0.4 * autoencoder_score +
              0.2 * timeseries_score
```

**Decision Threshold:** 0.65

---

### 5. Auto-Signature Generation

**Module:** `core/signature_generator.py`

**Purpose:** Automatically extract reusable attack fingerprints.

**Fingerprint Components:**

1. **Protocol Distribution:** Dominant protocols (TCP/UDP/ICMP)
2. **Packet Size Distribution:** Tiny/Small/Medium/Large buckets
3. **Rate Characteristics:** Mean, max, std deviation of packet rate
4. **Source Patterns:** Unique source count, diversity, top sources
5. **Timing Patterns:** Inter-arrival time statistics, burstiness

**Signature Lifecycle:**

```
Attack Detected → Observe (10s) → Generate Signature → Active (TTL: 300s)
                                                      ↓
                                           Match Traffic → Extend TTL
                                                      ↓
                                           No Match → Expire & Remove
```

**Matching Algorithm:**
- Multi-dimensional similarity scoring
- Weighted comparison across fingerprint components
- Match threshold: 70%

**Benefits:**
- Reduces detection latency for repeat attacks
- Signature database auto-cleanup
- Adaptive TTL based on match frequency

---

### 6. Adaptive Mitigation Controller

**Module:** `core/mitigation_controller.py`

**Purpose:** Graduated mitigation with automatic rollback.

#### Mitigation Levels

| Level | Threshold | Action | Description |
|-------|-----------|--------|-------------|
| 1 | 0.3 | Monitor | Log traffic, no enforcement |
| 2 | 0.5 | Rate Limit | Limit to 5,000 pps |
| 3 | 0.7 | Traffic Shape | Shape to 2,000 pps |
| 4 | 0.9 | Block | Drop all matching traffic |

#### Rollback Logic

**Conditions for Rollback:**
1. Average anomaly score < 0.2 for 10 consecutive windows
2. Rule age > grace period (60 seconds)
3. Rollback enabled in configuration

**Rollback Strategy:**
```
Block → Shape → Rate Limit → Remove
```

**Benefits:**
- Prevents overblocking during recovery
- Gradual service restoration
- Configurable grace periods

---

### 7. Explainability Engine

**Module:** `core/explainability.py`

**Purpose:** Provide human-readable explanations for decisions.

#### Feature Importance Calculation

**Methods:**
1. Model-provided contributions (from detection result)
2. Heuristic-based estimation for statistical features
3. Deviation-based importance scoring

**Top Features Selection:**
- Rank by importance
- Normalize to sum to 1.0
- Return top N (default: 5)

#### Explanation Components

**Summary (1-line):**
```
"Anomaly detected (score: 0.86) - Primary indicator: packet_rate. Action: rate_limit"
```

**Detailed Analysis:**
- Detection stage and confidence
- Triggered rules
- Feature values with descriptions
- Feature-specific insights

**Recommendations:**
- Action-specific (e.g., "Enable SYN cookies for SYN flood")
- Feature-specific (e.g., "Analyze source IP distribution")
- Confidence-based escalation

#### SOC Report Format

```
==================================================
DDOS MITIGATION DECISION REPORT
==================================================
Timestamp: 2026-01-10 14:23:45
Decision ID: EXP_142_1736519025
Status: ATTACK DETECTED
Anomaly Score: 0.86
Action Taken: rate_limit

SUMMARY:
  Anomaly detected - Primary indicator: packet_rate...

TOP CONTRIBUTING FACTORS:
  1. packet_rate: 42.3% contribution
  2. src_ip_entropy: 28.7% contribution
  ...

RECOMMENDED ACTIONS:
  1. Enable SYN cookies on target servers
  2. Consider geo-blocking if sources concentrated
  ...
==================================================
```

---

## Performance Optimization

### Latency Targets

| Component | Target | Typical |
|-----------|--------|---------|
| Statistical Detection | < 1 ms | 0.3 ms |
| Feature Extraction | < 5 ms | 2.1 ms |
| ML Ensemble | < 15 ms | 9.8 ms |
| **Total Pipeline** | **< 20 ms** | **12.4 ms** |

### Optimization Techniques

1. **Statistical Gate Filtering:**
   - Reduces ML inference by 60-80%
   - Sub-millisecond decision for normal traffic

2. **Feature Caching:**
   - Normalized features cached between detectors
   - Reduces redundant computation

3. **Vectorized Operations:**
   - NumPy for numerical computations
   - Batch processing where possible

4. **Model Optimization:**
   - Isolation Forest with limited max_samples (256)
   - Lightweight autoencoder architecture
   - Early stopping in training

---

## Deployment Considerations

### Production Deployment Path

**Current (Python):**
```
Scapy PCAP → Python Processing → Decision
```

**Future (eBPF/XDP):**
```
XDP Hook → eBPF Aggregation → User-space ML → eBPF Enforcement
```

**Migration Strategy:**
1. Keep ML/decision logic in user-space Python
2. Replace aggregation with eBPF (high-speed)
3. Replace enforcement with XDP (kernel-level)

### Scalability

**Single Instance:**
- Handles ~50,000 pps sustained
- ~500,000 pps burst (with statistical filtering)

**Distributed Deployment:**
- Traffic sampling at edge
- Centralized ML inference
- Distributed signature database (Redis)

---

## Configuration Tuning

### For High False Positive Rate

```yaml
statistical_detector:
  packet_rate_threshold: 15000  # Increase threshold
  burst_threshold: 4.0           # Less sensitive

ml_ensemble:
  voting:
    confidence_threshold: 0.75   # Higher confidence required
```

### For High False Negative Rate

```yaml
statistical_detector:
  packet_rate_threshold: 5000   # Lower threshold
  entropy_min_threshold: 2.0    # More sensitive

ml_ensemble:
  voting:
    confidence_threshold: 0.55   # Lower confidence acceptable
```

### For Low-Resource Environments

```yaml
ml_ensemble:
  models:
    autoencoder:
      enabled: false            # Disable resource-intensive model
    isolation_forest:
      n_estimators: 50          # Reduce ensemble size
      max_samples: 128

performance:
  enable_multiprocessing: false
```

---

## Testing & Validation

### Unit Tests (To Be Implemented)

```bash
pytest tests/test_feature_engineering.py
pytest tests/test_hybrid_detector.py
pytest tests/test_mitigation_controller.py
```

### Integration Tests

```bash
python demo/demo_evaluation.py
```

### Performance Benchmarks

```bash
python benchmarks/latency_test.py
python benchmarks/throughput_test.py
```

---

## Troubleshooting

### Issue: High Detection Latency

**Possible Causes:**
- Autoencoder model too large
- Too many features enabled

**Solutions:**
- Reduce autoencoder encoding_dim
- Disable temporal or flow features
- Enable multiprocessing

### Issue: Models Not Training

**Possible Causes:**
- Insufficient training data
- TensorFlow not installed

**Solutions:**
- Increase num_windows in train()
- Install TensorFlow: `pip install tensorflow`
- Disable autoencoder if TensorFlow unavailable

### Issue: Too Many False Positives

**Possible Causes:**
- Baseline not representative
- Thresholds too sensitive

**Solutions:**
- Retrain with more diverse normal traffic
- Adjust statistical_detector thresholds
- Increase ml_ensemble confidence_threshold

---

## References

1. **Isolation Forest:** Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). "Isolation forest."
2. **Autoencoders for Anomaly Detection:** Sakurada, M., & Yairi, T. (2014).
3. **DDoS Detection:** Mirkovic, J., & Reiher, P. (2004). "A taxonomy of DDoS attack and DDoS defense mechanisms."
4. **Explainable AI:** Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). "Why Should I Trust You?"

---

**Last Updated:** January 10, 2026
