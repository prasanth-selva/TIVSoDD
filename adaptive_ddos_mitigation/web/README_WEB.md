# Web Dashboard for Adaptive DDoS Mitigation System

Professional web-based monitoring and control interface for the DDoS mitigation system.

## Features

- **Real-Time Monitoring**: Live dashboard with WebSocket updates
- **Interactive Charts**: Anomaly scores, mitigation actions, detection statistics
- **System Control**: Initialize, train, and run simulations from the browser
- **Multiple Tabs**:
  - Dashboard: Overview with KPIs and charts
  - Detection: Detailed anomaly detection analysis
  - Mitigation: Active rules and enforcement status
  - Signatures: Auto-generated attack fingerprints
  - Activity Logs: Real-time system events
  - Configuration: Adjust simulation parameters

## Quick Start

### 1. Install Dependencies

```bash
cd web
pip install -r requirements_web.txt
```

### 2. Start the Web Server

```bash
python app.py
```

### 3. Open Dashboard

Navigate to http://localhost:5000 in your browser

## Usage Guide

### Step 1: Initialize System

Click the **Initialize** button in the sidebar to load the DDoS mitigation system.

### Step 2: Train on Normal Traffic

Click **Train** to train the ML models on simulated normal traffic (default: 50 windows).

### Step 3: Configure Simulation (Optional)

Go to the **Configuration** tab to adjust:
- Simulation duration
- Attack timing and duration
- Traffic rates and attack multiplier
- Number of training windows

### Step 4: Start Simulation

Click **Start Simulation** to begin real-time traffic processing with attack injection.

### Step 5: Monitor in Real-Time

Watch the dashboard update live with:
- Anomaly scores
- Mitigation actions
- Active signatures
- System metrics

## Dashboard Sections

### KPI Cards
- **Total Windows**: Number of traffic windows processed
- **Anomalies Detected**: Count of anomalous windows
- **Detection Rate**: Percentage of anomalies detected
- **Packets Dropped**: Total packets blocked/dropped

### Charts
- **Anomaly Score Timeline**: Real-time anomaly scores over time
- **Mitigation Actions**: Distribution of mitigation responses
- **Detection Statistics**: Normal vs anomalous traffic breakdown

### System Status
- Training status
- Simulation running state
- Active signatures count
- Active mitigation rules count

## API Endpoints

### System Management
- `POST /api/system/initialize` - Initialize the DDoS system
- `POST /api/system/train` - Train ML models
- `POST /api/system/start` - Start traffic simulation
- `POST /api/system/stop` - Stop simulation
- `GET /api/system/status` - Get system status

### Data Retrieval
- `GET /api/metrics/current` - Current real-time metrics
- `GET /api/signatures` - Active attack signatures
- `GET /api/rules` - Active mitigation rules
- `GET /api/detection/history` - Detection history
- `GET /api/config` - System configuration

## WebSocket Events

### Client → Server
- `connect` - Establish connection
- `request_update` - Request status update

### Server → Client
- `connected` - Connection established
- `window_processed` - New traffic window processed
- `training_complete` - Training finished
- `simulation_complete` - Simulation ended
- `simulation_error` - Error occurred

## Technology Stack

- **Backend**: Flask + Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Charts**: Chart.js
- **Icons**: Font Awesome 6
- **Real-time**: Socket.IO

## Architecture

```
web/
├── app.py                 # Flask application
├── templates/
│   └── dashboard.html     # Main dashboard template
├── static/
│   ├── css/
│   │   └── dashboard.css  # Styles
│   └── js/
│       └── dashboard.js   # Client-side logic
└── requirements_web.txt   # Python dependencies
```

## Customization

### Changing Ports

Edit `app.py`:
```python
socketio.run(app, debug=True, host='0.0.0.0', port=YOUR_PORT)
```

### Adjusting Update Frequency

Edit `dashboard.js` and modify the polling interval:
```javascript
setTimeout(updateStatus, YOUR_INTERVAL_MS);
```

### Custom Themes

Modify CSS variables in `dashboard.css`:
```css
:root {
    --primary-color: #your-color;
    --bg-dark: #your-background;
    /* ... */
}
```

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Troubleshooting

### WebSocket Connection Failed
- Check firewall settings
- Ensure port 5000 is not blocked
- Try `http://127.0.0.1:5000` instead of `localhost`

### Charts Not Rendering
- Clear browser cache
- Ensure Chart.js CDN is accessible
- Check browser console for errors

### Simulation Not Starting
- Verify system is initialized
- Ensure training is completed
- Check activity logs for errors

## Performance Tips

1. **Large Simulations**: For long simulations (>120s), consider reducing update frequency
2. **Multiple Clients**: WebSocket broadcasts to all connected clients
3. **Chart Data**: History limited to last 50 points for performance

## Security Notes

⚠️ **Development Use Only**
- Secret key is hardcoded (change for production)
- CORS allows all origins (restrict for production)
- No authentication (add for production deployment)

## License

Part of the Adaptive DDoS Mitigation System project.
