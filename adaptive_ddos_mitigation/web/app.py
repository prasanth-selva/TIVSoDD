"""
Web Application for Adaptive DDoS Mitigation System

Flask-based web dashboard with real-time monitoring and control.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import threading
import time
import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from adaptive_ddos_system import AdaptiveDDoSMitigationSystem

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ddos-mitigation-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global system instance
system = None
system_running = False
simulation_thread = None


class DashboardMetrics:
    """Store real-time metrics for dashboard"""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.total_windows = 0
        self.anomalies_detected = 0
        self.total_packets = 0
        self.packets_dropped = 0
        self.active_signatures = 0
        self.active_rules = 0
        self.recent_scores = []
        self.recent_timestamps = []
        self.detection_history = []
        self.mitigation_actions = {'allow': 0, 'monitor': 0, 'rate_limit': 0, 'shape': 0, 'drop': 0}

metrics = DashboardMetrics()


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/system/status')
def system_status():
    """Get current system status"""
    if system is None:
        return jsonify({
            'status': 'not_initialized',
            'is_trained': False,
            'is_running': False
        })
    
    status = system.get_system_status()
    status['is_running'] = system_running
    status['metrics'] = {
        'total_windows': metrics.total_windows,
        'anomalies_detected': metrics.anomalies_detected,
        'total_packets': metrics.total_packets,
        'packets_dropped': metrics.packets_dropped,
        'drop_rate': (metrics.packets_dropped / metrics.total_packets * 100) if metrics.total_packets > 0 else 0
    }
    
    return jsonify(status)


@app.route('/api/system/initialize', methods=['POST'])
def initialize_system():
    """Initialize the DDoS mitigation system"""
    global system
    
    try:
        config_path = Path(__file__).parent.parent / "config" / "system_config.yaml"
        system = AdaptiveDDoSMitigationSystem(str(config_path))
        
        return jsonify({
            'success': True,
            'message': 'System initialized successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/system/train', methods=['POST'])
def train_system():
    """Train the system on normal traffic"""
    global system
    
    if system is None:
        return jsonify({'success': False, 'error': 'System not initialized'}), 400
    
    try:
        data = request.get_json()
        num_windows = data.get('num_windows', 50)
        
        def train_async():
            system.train(num_windows=num_windows)
            socketio.emit('training_complete', {'success': True})
        
        thread = threading.Thread(target=train_async)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Training started with {num_windows} windows'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/system/start', methods=['POST'])
def start_simulation():
    """Start traffic simulation"""
    global system, system_running, simulation_thread
    
    if system is None:
        return jsonify({'success': False, 'error': 'System not initialized'}), 400
    
    if not system.is_trained:
        return jsonify({'success': False, 'error': 'System not trained'}), 400
    
    if system_running:
        return jsonify({'success': False, 'error': 'Simulation already running'}), 400
    
    try:
        data = request.get_json()
        duration = data.get('duration', 60)
        attack_start = data.get('attack_start', 20)
        attack_duration = data.get('attack_duration', 15)
        base_rate = data.get('base_rate', 1000)
        attack_multiplier = data.get('attack_multiplier', 10)
        
        def run_simulation():
            global system_running
            system_running = True
            metrics.reset()
            
            try:
                stream = system.aggregator.simulate_realtime_stream(
                    base_rate=base_rate,
                    duration=duration,
                    attack_start=attack_start,
                    attack_duration=attack_duration,
                    attack_multiplier=attack_multiplier
                )
                
                for window in stream:
                    if not system_running:
                        break
                    
                    result = system.process_window(window)
                    
                    # Update metrics
                    metrics.total_windows += 1
                    metrics.total_packets += result['mitigation_stats']['total_packets']
                    metrics.packets_dropped += result['mitigation_stats']['packets_dropped']
                    
                    if result['is_anomaly']:
                        metrics.anomalies_detected += 1
                    
                    metrics.recent_scores.append(result['anomaly_score'])
                    metrics.recent_timestamps.append(result['timestamp'])
                    
                    if len(metrics.recent_scores) > 50:
                        metrics.recent_scores.pop(0)
                        metrics.recent_timestamps.pop(0)
                    
                    metrics.mitigation_actions[result['mitigation_action']] += 1
                    
                    metrics.detection_history.append({
                        'timestamp': result['timestamp'],
                        'is_anomaly': result['is_anomaly'],
                        'score': result['anomaly_score'],
                        'action': result['mitigation_action']
                    })
                    
                    if len(metrics.detection_history) > 100:
                        metrics.detection_history.pop(0)
                    
                    # Emit real-time update
                    socketio.emit('window_processed', {
                        'result': result,
                        'metrics': {
                            'total_windows': metrics.total_windows,
                            'anomalies_detected': metrics.anomalies_detected,
                            'total_packets': metrics.total_packets,
                            'packets_dropped': metrics.packets_dropped
                        }
                    })
                    
                    time.sleep(0.1)  # Small delay for visualization
                
            except Exception as e:
                socketio.emit('simulation_error', {'error': str(e)})
            finally:
                system_running = False
                socketio.emit('simulation_complete', {'success': True})
        
        simulation_thread = threading.Thread(target=run_simulation)
        simulation_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Simulation started'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/system/stop', methods=['POST'])
def stop_simulation():
    """Stop running simulation"""
    global system_running
    
    system_running = False
    
    return jsonify({
        'success': True,
        'message': 'Simulation stopped'
    })


@app.route('/api/metrics/current')
def current_metrics():
    """Get current real-time metrics"""
    return jsonify({
        'total_windows': metrics.total_windows,
        'anomalies_detected': metrics.anomalies_detected,
        'total_packets': metrics.total_packets,
        'packets_dropped': metrics.packets_dropped,
        'active_signatures': len(system.signature_generator.get_active_signatures()) if system else 0,
        'active_rules': len(system.mitigation_controller.active_rules) if system else 0,
        'recent_scores': metrics.recent_scores,
        'recent_timestamps': [datetime.fromtimestamp(ts).strftime('%H:%M:%S') for ts in metrics.recent_timestamps],
        'mitigation_actions': metrics.mitigation_actions,
        'detection_rate': (metrics.anomalies_detected / metrics.total_windows * 100) if metrics.total_windows > 0 else 0
    })


@app.route('/api/signatures')
def get_signatures():
    """Get active attack signatures"""
    if system is None:
        return jsonify({'signatures': []})
    
    summary = system.signature_generator.get_signature_summary()
    return jsonify(summary)


@app.route('/api/rules')
def get_rules():
    """Get active mitigation rules"""
    if system is None:
        return jsonify({'rules': []})
    
    summary = system.mitigation_controller.get_active_rules_summary()
    return jsonify(summary)


@app.route('/api/detection/history')
def detection_history():
    """Get detection history"""
    return jsonify({
        'history': metrics.detection_history[-50:]  # Last 50 detections
    })


@app.route('/api/config', methods=['GET', 'POST'])
def configuration():
    """Get or update configuration"""
    config_path = Path(__file__).parent.parent / "config" / "system_config.yaml"
    
    if request.method == 'GET':
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return jsonify(config)
    else:
        # Update configuration
        try:
            data = request.get_json()
            import yaml
            with open(config_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            
            return jsonify({'success': True, 'message': 'Configuration updated'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to DDoS Mitigation Dashboard'})


@socketio.on('request_update')
def handle_update_request():
    """Handle manual update request"""
    if system:
        status = system.get_system_status()
        emit('status_update', status)


if __name__ == '__main__':
    print("=" * 60)
    print("  Adaptive DDoS Mitigation System - Web Dashboard")
    print("=" * 60)
    print("\n  Starting server at http://localhost:5000")
    print("  Press Ctrl+C to stop\n")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
