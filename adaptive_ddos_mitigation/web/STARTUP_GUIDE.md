# 🚀 Complete Startup Guide - Web Dashboard

## Prerequisites Checklist

- [ ] Python 3.8 or higher installed
- [ ] pip package manager available
- [ ] Port 5000 available (or choose custom port)
- [ ] Modern web browser (Chrome, Firefox, Safari, Edge)

## Installation Steps

### 1. Navigate to Web Directory

```bash
cd /home/prasanth/Documents/ATTACK_DDOS/adaptive_ddos_mitigation/web
```

### 2. Install Dependencies

**Option A: Using the startup script (Recommended)**
```bash
./start_dashboard.sh
```

**Option B: Manual installation**
```bash
pip install -r requirements_web.txt
python app.py
```

### 3. Access Dashboard

Open your browser and navigate to:
- **http://localhost:5000**
- **http://127.0.0.1:5000**
- **http://YOUR_IP:5000** (for network access)

## First-Time Usage

### Step 1: Initialize the System

1. Click the **"Initialize"** button in the left sidebar
2. Wait for confirmation: "System initialized successfully"
3. The "Train" button will become enabled

### Step 2: Train ML Models

1. (Optional) Go to **Configuration** tab and adjust "Training Windows" (default: 50)
2. Click **"Train"** button
3. Training typically takes 10-30 seconds
4. Watch the activity logs for progress
5. Wait for "Training completed successfully"

### Step 3: Configure Simulation (Optional)

Navigate to the **Configuration** tab and adjust:

- **Duration**: How long the simulation runs (default: 60 seconds)
- **Attack Start**: When the attack begins (default: 20 seconds)
- **Attack Duration**: How long the attack lasts (default: 15 seconds)
- **Base Rate**: Normal traffic rate in packets/second (default: 1000)
- **Attack Multiplier**: How much traffic increases during attack (default: 10x)

### Step 4: Start Simulation

1. Click **"Start Simulation"** button
2. Watch real-time updates on the dashboard:
   - KPI cards update continuously
   - Charts show live data
   - Activity logs stream events
   - Status indicators change

### Step 5: Explore Tabs

**Dashboard Tab** (Default View)
- Overview with KPIs
- Real-time anomaly score chart
- Mitigation action distribution
- System status panel

**Detection Tab**
- Recent detection events
- Normal vs anomalous traffic statistics
- Detection timeline

**Mitigation Tab**
- Active mitigation rules
- Rule details (score, packets dropped, timestamps)
- Enforcement status

**Signatures Tab**
- Auto-generated attack fingerprints
- Signature details (protocol, rate, match count)
- Pattern information

**Activity Logs Tab**
- Real-time system events
- Color-coded by severity:
  - 🟢 Success (green)
  - 🔵 Info (blue)
  - 🟡 Warning (yellow)
  - 🔴 Error (red)

**Configuration Tab**
- Simulation parameters
- System settings

## Understanding the Dashboard

### KPI Cards

1. **Total Windows**: Number of traffic time windows processed
2. **Anomalies Detected**: Count of suspicious/attack windows
3. **Detection Rate**: Percentage of anomalous traffic
4. **Packets Dropped**: Total packets blocked by mitigation

### Anomaly Score Chart

- X-axis: Time progression
- Y-axis: Anomaly score (0.0 to 1.0)
- Score > 0.7: High confidence attack
- Score 0.5-0.7: Moderate suspicion
- Score < 0.5: Normal traffic

### Mitigation Actions Pie Chart

- **Green (Allow)**: Normal traffic, no action
- **Cyan (Monitor)**: Low-level monitoring only
- **Yellow (Rate Limit)**: Throttling traffic
- **Orange (Shape)**: Traffic shaping applied
- **Red (Drop)**: Blocking malicious packets

### System Status Indicators

- **Training Status**: Shows if ML models are trained
- **Simulation**: Current running state
- **Active Signatures**: Number of learned attack patterns
- **Active Rules**: Number of enforcement rules

## Expected Behavior During Simulation

### Normal Traffic Period (0-20s)
- Low anomaly scores (< 0.3)
- Action: ALLOW or MONITOR
- Steady packet rates
- Green indicators

### Attack Period (20-35s)
- Anomaly scores spike (> 0.7)
- Actions escalate: RATE_LIMIT → SHAPE → DROP
- Packet drop count increases
- Red/yellow indicators
- Signatures auto-generated

### Recovery Period (35-60s)
- Anomaly scores decrease
- Actions de-escalate
- Some signatures may persist (TTL)
- Gradual return to normal

## Troubleshooting

### Can't Connect to Dashboard

**Issue**: Browser shows "Connection refused"

**Solutions**:
1. Verify server is running: Check terminal for "Running on http://..."
2. Try http://127.0.0.1:5000 instead of localhost
3. Check firewall isn't blocking port 5000
4. Ensure no other service is using port 5000

**Check port availability**:
```bash
netstat -an | grep 5000
# or
lsof -i :5000
```

### WebSocket Not Connecting

**Issue**: Status shows "Disconnected"

**Solutions**:
1. Refresh browser page (Ctrl+F5 or Cmd+Shift+R)
2. Clear browser cache
3. Check browser console (F12) for errors
4. Ensure Socket.IO CDN is accessible

### Charts Not Rendering

**Issue**: Empty chart areas

**Solutions**:
1. Ensure Chart.js CDN is accessible (check internet connection)
2. Clear browser cache
3. Check browser console (F12) for JavaScript errors
4. Try different browser

### Training Takes Too Long

**Issue**: Training exceeds 2 minutes

**Solutions**:
1. Reduce training windows in Configuration tab
2. Check CPU usage (training is CPU-intensive)
3. Close other applications
4. For slow machines, use 20-30 windows instead of 50

### Simulation Doesn't Start

**Issue**: "Start Simulation" button doesn't work

**Checklist**:
- [ ] System initialized? (Click "Initialize" first)
- [ ] Training complete? (Click "Train" and wait)
- [ ] Check Activity Logs for error messages
- [ ] Refresh page and retry

### High Memory Usage

**Issue**: Browser uses excessive RAM

**Solutions**:
1. Limit simulation duration to < 120 seconds
2. Refresh page periodically for long sessions
3. Close unused browser tabs
4. Chart data is limited to last 50 points automatically

## Advanced Configuration

### Changing Server Port

Edit `web/app.py` line 340:
```python
socketio.run(app, debug=True, host='0.0.0.0', port=YOUR_PORT)
```

### Enabling Network Access

By default, server binds to `0.0.0.0` (all interfaces).

Access from another machine:
```
http://YOUR_SERVER_IP:5000
```

**Security Warning**: For production, enable authentication and HTTPS!

### Custom Themes

Edit `web/static/css/dashboard.css` CSS variables:
```css
:root {
    --primary-color: #YOUR_COLOR;
    --bg-dark: #YOUR_BACKGROUND;
    /* ... customize colors ... */
}
```

## Performance Tips

1. **Shorter Simulations**: For demo purposes, use 30-60 second durations
2. **Reduce Training**: 30-40 windows sufficient for testing
3. **Single Client**: Multiple browsers multiply server load
4. **Close Tabs**: Close inactive dashboard tabs
5. **Modern Browser**: Use latest Chrome/Firefox for best performance

## Keyboard Shortcuts

- **Ctrl+F5** / **Cmd+Shift+R**: Hard refresh (clear cache)
- **F12**: Open browser developer tools
- **Ctrl+Shift+I** / **Cmd+Option+I**: Open inspector

## Next Steps

After successful deployment:

1. **Experiment**: Try different attack parameters
2. **Analyze**: Study signature generation patterns
3. **Customize**: Modify detection thresholds in code
4. **Extend**: Add custom charts or metrics
5. **Export**: Use results for research/presentation

## Getting Help

If issues persist:

1. Check activity logs in dashboard
2. Review terminal/console output
3. Check browser console (F12 → Console tab)
4. Verify all dependencies installed: `pip list`
5. Test basic system: `cd demo && python quickstart.py`

## System Requirements

### Minimum
- 4GB RAM
- 2 CPU cores
- 500MB disk space
- 1920x1080 screen resolution

### Recommended
- 8GB+ RAM
- 4+ CPU cores
- Modern SSD
- 2560x1440+ screen resolution

## Browser Compatibility

✅ **Fully Supported**:
- Chrome 90+
- Edge 90+
- Firefox 88+
- Safari 14+

⚠️ **Limited Support**:
- Older browsers may have chart rendering issues
- Mobile browsers (responsive design included but not optimized)

## Demo Workflow Example

**Perfect for presentations/hackathons**:

1. Open dashboard → Initialize (10s)
2. Train system (30s)
3. Configure attack: 60s duration, 20s start, 15s attack, 10x multiplier
4. Start simulation
5. Watch live as:
   - Normal traffic flows (0-20s)
   - Attack detected (20s)
   - Mitigation activates (21s)
   - Signatures generated (22s)
   - Attack blocked (23-35s)
   - System recovers (35-60s)
6. Switch to tabs to show:
   - Detection history
   - Active signatures
   - Mitigation rules
7. Export results from activity logs

**Total demo time: ~2 minutes + Q&A**

## Success Indicators

You'll know everything is working when:

✅ Connection status shows "Connected" (green)
✅ KPI cards update in real-time
✅ Charts animate smoothly
✅ Activity logs stream events
✅ Status badges change appropriately
✅ No errors in browser console (F12)

Enjoy your professional DDoS mitigation dashboard! 🛡️
