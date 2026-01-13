// ========================================
// Adaptive DDoS Mitigation Dashboard
// ========================================

// Global state
const state = {
    socket: null,
    isConnected: false,
    systemInitialized: false,
    systemTrained: false,
    systemRunning: false,
    charts: {
        anomaly: null,
        mitigation: null,
        detectionStats: null
    }
};

// ========================================
// Initialization
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    initializeNavigation();
    initializeControls();
    initializeCharts();
    updateStatus();
    
    console.log('Dashboard initialized');
});

// ========================================
// WebSocket Connection
// ========================================

function initializeSocket() {
    state.socket = io();
    
    state.socket.on('connect', function() {
        state.isConnected = true;
        updateConnectionStatus(true);
        addLog('Connected to server', 'success');
    });
    
    state.socket.on('disconnect', function() {
        state.isConnected = false;
        updateConnectionStatus(false);
        addLog('Disconnected from server', 'error');
    });
    
    state.socket.on('window_processed', function(data) {
        handleWindowProcessed(data);
    });
    
    state.socket.on('training_complete', function(data) {
        state.systemTrained = true;
        updateControlButtons();
        addLog('Training completed successfully', 'success');
    });
    
    state.socket.on('simulation_complete', function(data) {
        state.systemRunning = false;
        updateControlButtons();
        addLog('Simulation completed', 'info');
    });
    
    state.socket.on('simulation_error', function(data) {
        state.systemRunning = false;
        updateControlButtons();
        addLog('Simulation error: ' + data.error, 'error');
    });
}

function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    if (connected) {
        statusElement.className = 'status-badge status-connected';
        statusElement.innerHTML = '<i class="fas fa-circle"></i> Connected';
    } else {
        statusElement.className = 'status-badge status-disconnected';
        statusElement.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
    }
}

// ========================================
// Navigation
// ========================================

function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active nav item
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
            
            // Show corresponding tab
            const tabId = this.getAttribute('data-tab');
            showTab(tabId);
        });
    });
}

function showTab(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    const targetTab = document.getElementById('tab-' + tabId);
    if (targetTab) {
        targetTab.classList.add('active');
        
        // Refresh data for specific tabs
        if (tabId === 'signatures') {
            loadSignatures();
        } else if (tabId === 'mitigation') {
            loadRules();
        } else if (tabId === 'detection') {
            loadDetectionHistory();
        }
    }
}

// ========================================
// Control Buttons
// ========================================

function initializeControls() {
    document.getElementById('btn-initialize').addEventListener('click', initializeSystem);
    document.getElementById('btn-train').addEventListener('click', trainSystem);
    document.getElementById('btn-start').addEventListener('click', startSimulation);
    document.getElementById('btn-stop').addEventListener('click', stopSimulation);
}

function updateControlButtons() {
    document.getElementById('btn-train').disabled = !state.systemInitialized || state.systemRunning;
    document.getElementById('btn-start').disabled = !state.systemTrained || state.systemRunning;
    document.getElementById('btn-stop').disabled = !state.systemRunning;
}

async function initializeSystem() {
    try {
        addLog('Initializing system...', 'info');
        
        const response = await fetch('/api/system/initialize', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            state.systemInitialized = true;
            updateControlButtons();
            addLog('System initialized successfully', 'success');
        } else {
            addLog('Initialization failed: ' + data.error, 'error');
        }
    } catch (error) {
        addLog('Error initializing system: ' + error.message, 'error');
    }
}

async function trainSystem() {
    try {
        const numWindows = parseInt(document.getElementById('config-train-windows').value);
        
        addLog(`Starting training with ${numWindows} windows...`, 'info');
        
        const response = await fetch('/api/system/train', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ num_windows: numWindows })
        });
        
        const data = await response.json();
        
        if (data.success) {
            addLog(data.message, 'info');
        } else {
            addLog('Training failed: ' + data.error, 'error');
        }
    } catch (error) {
        addLog('Error starting training: ' + error.message, 'error');
    }
}

async function startSimulation() {
    try {
        const config = {
            duration: parseInt(document.getElementById('config-duration').value),
            attack_start: parseInt(document.getElementById('config-attack-start').value),
            attack_duration: parseInt(document.getElementById('config-attack-duration').value),
            base_rate: parseInt(document.getElementById('config-base-rate').value),
            attack_multiplier: parseInt(document.getElementById('config-attack-multiplier').value)
        };
        
        addLog('Starting simulation...', 'info');
        
        const response = await fetch('/api/system/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const data = await response.json();
        
        if (data.success) {
            state.systemRunning = true;
            updateControlButtons();
            addLog(data.message, 'success');
        } else {
            addLog('Failed to start simulation: ' + data.error, 'error');
        }
    } catch (error) {
        addLog('Error starting simulation: ' + error.message, 'error');
    }
}

async function stopSimulation() {
    try {
        addLog('Stopping simulation...', 'info');
        
        const response = await fetch('/api/system/stop', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            state.systemRunning = false;
            updateControlButtons();
            addLog(data.message, 'warning');
        }
    } catch (error) {
        addLog('Error stopping simulation: ' + error.message, 'error');
    }
}

// ========================================
// Charts
// ========================================

function initializeCharts() {
    // Anomaly Score Chart
    const anomalyCtx = document.getElementById('anomalyChart').getContext('2d');
    state.charts.anomaly = new Chart(anomalyCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Anomaly Score',
                data: [],
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#f1f5f9' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                },
                x: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                }
            }
        }
    });
    
    // Mitigation Actions Chart
    const mitigationCtx = document.getElementById('mitigationChart').getContext('2d');
    state.charts.mitigation = new Chart(mitigationCtx, {
        type: 'doughnut',
        data: {
            labels: ['Allow', 'Monitor', 'Rate Limit', 'Shape', 'Drop'],
            datasets: [{
                data: [0, 0, 0, 0, 0],
                backgroundColor: [
                    '#10b981',
                    '#06b6d4',
                    '#f59e0b',
                    '#f97316',
                    '#ef4444'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#f1f5f9' }
                }
            }
        }
    });
    
    // Detection Stats Chart
    const detectionCtx = document.getElementById('detectionStatsChart').getContext('2d');
    state.charts.detectionStats = new Chart(detectionCtx, {
        type: 'bar',
        data: {
            labels: ['Normal', 'Anomalous'],
            datasets: [{
                label: 'Count',
                data: [0, 0],
                backgroundColor: ['#10b981', '#ef4444']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#f1f5f9' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                },
                x: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                }
            }
        }
    });
}

function updateCharts(metrics) {
    // Update anomaly chart
    if (metrics.recent_timestamps && metrics.recent_scores) {
        state.charts.anomaly.data.labels = metrics.recent_timestamps;
        state.charts.anomaly.data.datasets[0].data = metrics.recent_scores;
        state.charts.anomaly.update();
    }
    
    // Update mitigation actions chart
    if (metrics.mitigation_actions) {
        state.charts.mitigation.data.datasets[0].data = [
            metrics.mitigation_actions.allow || 0,
            metrics.mitigation_actions.monitor || 0,
            metrics.mitigation_actions.rate_limit || 0,
            metrics.mitigation_actions.shape || 0,
            metrics.mitigation_actions.drop || 0
        ];
        state.charts.mitigation.update();
    }
}

// ========================================
// Real-time Updates
// ========================================

function handleWindowProcessed(data) {
    // Update KPIs
    updateKPIs(data.metrics);
    
    // Update charts
    updateMetricsAndCharts();
    
    // Add log entry
    const action = data.result.mitigation_action;
    const score = data.result.anomaly_score.toFixed(3);
    const logType = data.result.is_anomaly ? 'warning' : 'info';
    addLog(`Window processed - Score: ${score}, Action: ${action.toUpperCase()}`, logType);
}

function updateKPIs(metrics) {
    document.getElementById('kpi-windows').textContent = metrics.total_windows;
    document.getElementById('kpi-anomalies').textContent = metrics.anomalies_detected;
    document.getElementById('kpi-dropped').textContent = metrics.packets_dropped;
    
    const detectionRate = metrics.total_windows > 0 
        ? (metrics.anomalies_detected / metrics.total_windows * 100).toFixed(1)
        : 0;
    document.getElementById('kpi-detection-rate').textContent = detectionRate + '%';
}

async function updateMetricsAndCharts() {
    try {
        const response = await fetch('/api/metrics/current');
        const metrics = await response.json();
        
        updateCharts(metrics);
        updateStatusInfo(metrics);
    } catch (error) {
        console.error('Error updating metrics:', error);
    }
}

function updateStatusInfo(metrics) {
    document.getElementById('status-signatures').textContent = metrics.active_signatures || 0;
    document.getElementById('status-rules').textContent = metrics.active_rules || 0;
}

async function updateStatus() {
    try {
        const response = await fetch('/api/system/status');
        const status = await response.json();
        
        // Update status badges
        if (status.is_trained) {
            document.getElementById('status-trained').className = 'badge badge-success';
            document.getElementById('status-trained').textContent = 'Trained';
            state.systemTrained = true;
        }
        
        if (status.is_running) {
            document.getElementById('status-running').className = 'badge badge-success';
            document.getElementById('status-running').textContent = 'Running';
            state.systemRunning = true;
        }
        
        updateControlButtons();
    } catch (error) {
        console.error('Error updating status:', error);
    }
    
    // Update periodically
    setTimeout(updateStatus, 2000);
}

// ========================================
// Signatures & Rules
// ========================================

async function loadSignatures() {
    try {
        const response = await fetch('/api/signatures');
        const data = await response.json();
        
        const container = document.getElementById('signatures-list');
        
        if (!data.signatures || data.signatures.length === 0) {
            container.innerHTML = '<p class="no-data">No signatures generated yet</p>';
            return;
        }
        
        container.innerHTML = data.signatures.map(sig => `
            <div class="signature-card">
                <div class="signature-header">
                    <h4>Signature #${sig.signature_id.slice(0, 8)}</h4>
                    <span class="badge badge-warning">Active</span>
                </div>
                <div class="signature-details">
                    <div class="detail-item">
                        <span class="detail-label">Protocol</span>
                        <span class="detail-value">${sig.dominant_protocol}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Packet Rate</span>
                        <span class="detail-value">${sig.packet_rate_pattern.toFixed(0)} pps</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Match Count</span>
                        <span class="detail-value">${sig.match_count}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Created</span>
                        <span class="detail-value">${new Date(sig.created_at * 1000).toLocaleString()}</span>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading signatures:', error);
    }
}

async function loadRules() {
    try {
        const response = await fetch('/api/rules');
        const data = await response.json();
        
        const container = document.getElementById('mitigation-rules');
        
        if (!data.rules || data.rules.length === 0) {
            container.innerHTML = '<p class="no-data">No active mitigation rules</p>';
            return;
        }
        
        container.innerHTML = data.rules.map(rule => `
            <div class="rule-card">
                <div class="rule-header">
                    <h4>Rule #${rule.rule_id.slice(0, 8)}</h4>
                    <span class="badge badge-${getActionBadge(rule.action)}">${rule.action.toUpperCase()}</span>
                </div>
                <div class="rule-details">
                    <div class="detail-item">
                        <span class="detail-label">Anomaly Score</span>
                        <span class="detail-value">${rule.anomaly_score.toFixed(3)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Packets Dropped</span>
                        <span class="detail-value">${rule.packets_dropped}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Created</span>
                        <span class="detail-value">${new Date(rule.created_at * 1000).toLocaleString()}</span>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading rules:', error);
    }
}

function getActionBadge(action) {
    const badges = {
        'allow': 'success',
        'monitor': 'info',
        'rate_limit': 'warning',
        'shape': 'warning',
        'drop': 'danger'
    };
    return badges[action] || 'secondary';
}

// ========================================
// Detection History
// ========================================

async function loadDetectionHistory() {
    try {
        const response = await fetch('/api/detection/history');
        const data = await response.json();
        
        const container = document.getElementById('detection-history');
        
        if (!data.history || data.history.length === 0) {
            container.innerHTML = '<p class="no-data">No detection data available</p>';
            return;
        }
        
        container.innerHTML = data.history.map(item => `
            <div class="detection-item ${item.is_anomaly ? 'anomaly' : 'normal'}">
                <strong>${new Date(item.timestamp * 1000).toLocaleTimeString()}</strong>
                - Score: ${item.score.toFixed(3)}
                - Action: ${item.action.toUpperCase()}
                ${item.is_anomaly ? ' ⚠️ ANOMALY' : ' ✓ Normal'}
            </div>
        `).join('');
        
        // Update detection stats chart
        const normalCount = data.history.filter(h => !h.is_anomaly).length;
        const anomalyCount = data.history.filter(h => h.is_anomaly).length;
        
        state.charts.detectionStats.data.datasets[0].data = [normalCount, anomalyCount];
        state.charts.detectionStats.update();
    } catch (error) {
        console.error('Error loading detection history:', error);
    }
}

// ========================================
// Logging
// ========================================

function addLog(message, type = 'info') {
    const logsContainer = document.getElementById('activity-logs');
    const timestamp = new Date().toLocaleTimeString();
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.textContent = `[${timestamp}] ${message}`;
    
    logsContainer.insertBefore(logEntry, logsContainer.firstChild);
    
    // Keep only last 100 logs
    while (logsContainer.children.length > 100) {
        logsContainer.removeChild(logsContainer.lastChild);
    }
}
