"""
Generate Dashboard Preview Image
Creates a visual representation of the web dashboard
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(16, 10))
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis('off')

# Colors
bg_dark = '#0f172a'
bg_light = '#1e293b'
border_color = '#334155'
primary_color = '#2563eb'
success_color = '#10b981'
danger_color = '#ef4444'
warning_color = '#f59e0b'
text_color = '#f1f5f9'

fig.patch.set_facecolor(bg_dark)

# Header
header = FancyBboxPatch((0, 9), 16, 1, boxstyle="round,pad=0.02", 
                        facecolor=bg_light, edgecolor=border_color, linewidth=2)
ax.add_patch(header)
ax.text(0.3, 9.5, '🛡️ Adaptive DDoS Mitigation System - Dashboard', 
        fontsize=18, color=primary_color, weight='bold', va='center')
ax.text(14.5, 9.5, '● Connected', fontsize=12, color=success_color, va='center')

# Sidebar
sidebar = Rectangle((0, 0), 2.5, 9, facecolor=bg_light, edgecolor=border_color, linewidth=2)
ax.add_patch(sidebar)

# Navigation items
nav_items = [
    ('Dashboard', 8.2, True),
    ('Detection', 7.6, False),
    ('Mitigation', 7.0, False),
    ('Signatures', 6.4, False),
    ('Activity Logs', 5.8, False),
    ('Configuration', 5.2, False)
]

for label, y_pos, active in nav_items:
    color = primary_color if active else '#64748b'
    ax.text(0.2, y_pos, f'▸ {label}', fontsize=11, color=color, weight='bold' if active else 'normal')

# Control buttons
button_y = 4.0
for i, (btn_label, btn_color) in enumerate([
    ('Initialize', primary_color),
    ('Train', '#64748b'),
    ('Start Simulation', success_color),
    ('Stop', danger_color)
]):
    btn_box = FancyBboxPatch((0.3, button_y - i*0.5), 1.9, 0.35, 
                             boxstyle="round,pad=0.02", facecolor=btn_color, 
                             edgecolor=btn_color, linewidth=1.5)
    ax.add_patch(btn_box)
    ax.text(1.25, button_y - i*0.5 + 0.175, btn_label, fontsize=9, 
            color='white', weight='bold', ha='center', va='center')

# Main content area
main_bg = Rectangle((2.6, 0), 13.4, 9, facecolor=bg_dark, edgecolor='none')
ax.add_patch(main_bg)

# KPI Cards
kpi_y = 8.2
kpi_width = 3.0
kpi_data = [
    ('Total Windows', '847', primary_color, '📊'),
    ('Anomalies Detected', '142', danger_color, '⚠️'),
    ('Detection Rate', '16.8%', '#06b6d4', '📈'),
    ('Packets Dropped', '1.2M', warning_color, '🚫')
]

for i, (title, value, color, icon) in enumerate(kpi_data):
    x_pos = 2.9 + i * 3.2
    kpi_box = FancyBboxPatch((x_pos, kpi_y), kpi_width, 0.8, 
                             boxstyle="round,pad=0.03", facecolor=bg_light, 
                             edgecolor=border_color, linewidth=1.5)
    ax.add_patch(kpi_box)
    
    # Icon
    ax.text(x_pos + 0.3, kpi_y + 0.4, icon, fontsize=24, va='center')
    
    # Text
    ax.text(x_pos + 1.0, kpi_y + 0.55, title, fontsize=9, color='#94a3b8', weight='normal')
    ax.text(x_pos + 1.0, kpi_y + 0.2, value, fontsize=16, color=text_color, weight='bold')

# Chart 1: Anomaly Score Timeline
chart1_box = FancyBboxPatch((2.9, 4.5), 6.2, 3.3, boxstyle="round,pad=0.03",
                           facecolor=bg_light, edgecolor=border_color, linewidth=1.5)
ax.add_patch(chart1_box)
ax.text(3.2, 7.5, 'Anomaly Score Timeline', fontsize=11, color='#94a3b8', weight='bold')

# Simulated line chart
x_data = np.linspace(3.2, 8.8, 50)
y_data = 4.8 + 0.3 * np.sin(x_data * 2) + 0.8 * (np.sin(x_data * 0.5) > 0.3)
y_data = np.clip(y_data, 4.8, 7.3)
ax.plot(x_data, y_data, color=danger_color, linewidth=2, alpha=0.8)
ax.fill_between(x_data, 4.8, y_data, color=danger_color, alpha=0.1)

# Chart 2: Mitigation Actions
chart2_box = FancyBboxPatch((9.4, 4.5), 6.2, 3.3, boxstyle="round,pad=0.03",
                           facecolor=bg_light, edgecolor=border_color, linewidth=1.5)
ax.add_patch(chart2_box)
ax.text(9.7, 7.5, 'Mitigation Actions', fontsize=11, color='#94a3b8', weight='bold')

# Simulated pie chart
center_x, center_y = 12.5, 6.1
radius = 1.0
colors_pie = [success_color, '#06b6d4', warning_color, '#f97316', danger_color]
sizes = [45, 15, 20, 10, 10]
start_angle = 0

for size, color in zip(sizes, colors_pie):
    angle = size * 3.6
    wedge = patches.Wedge((center_x, center_y), radius, start_angle, 
                          start_angle + angle, facecolor=color, edgecolor=bg_light, linewidth=2)
    ax.add_patch(wedge)
    start_angle += angle

# Legend
legend_items = ['Allow', 'Monitor', 'Rate Limit', 'Shape', 'Drop']
for i, (label, color) in enumerate(zip(legend_items, colors_pie)):
    legend_x = 9.7 + (i % 3) * 2.0
    legend_y = 5.0 - (i // 3) * 0.3
    ax.add_patch(Rectangle((legend_x, legend_y), 0.15, 0.15, facecolor=color))
    ax.text(legend_x + 0.25, legend_y + 0.075, label, fontsize=8, color=text_color, va='center')

# Status Panel
status_box = FancyBboxPatch((2.9, 0.3), 12.7, 4.0, boxstyle="round,pad=0.03",
                           facecolor=bg_light, edgecolor=border_color, linewidth=1.5)
ax.add_patch(status_box)
ax.text(3.2, 4.0, 'System Status', fontsize=11, color='#94a3b8', weight='bold')

# Status items
status_items = [
    ('Training Status:', 'Trained', success_color),
    ('Simulation:', 'Running', success_color),
    ('Active Signatures:', '7', '#06b6d4'),
    ('Active Rules:', '12', '#06b6d4')
]

for i, (label, value, color) in enumerate(status_items):
    y_pos = 3.4 - i * 0.35
    status_item_box = FancyBboxPatch((3.3, y_pos), 11.8, 0.3, 
                                     boxstyle="round,pad=0.01", 
                                     facecolor=bg_dark, edgecolor='none')
    ax.add_patch(status_item_box)
    ax.text(3.5, y_pos + 0.15, label, fontsize=9, color='#94a3b8', va='center')
    
    badge_box = FancyBboxPatch((13.5, y_pos + 0.05), 1.2, 0.2, 
                               boxstyle="round,pad=0.02", 
                               facecolor=color, edgecolor=color, linewidth=1, alpha=0.2)
    ax.add_patch(badge_box)
    ax.text(14.1, y_pos + 0.15, value, fontsize=8, color=color, 
            weight='bold', ha='center', va='center')

# Recent logs
log_y_start = 2.2
logs = [
    ('[14:23:45] Window processed - Score: 0.134, Action: ALLOW', '#06b6d4'),
    ('[14:23:50] Window processed - Score: 0.847, Action: RATE_LIMIT', warning_color),
    ('[14:23:55] Anomaly detected - Score: 0.923, Action: DROP', danger_color),
    ('[14:24:00] Signature generated - Protocol: TCP, Rate: 48.2k pps', success_color)
]

for i, (log_text, log_color) in enumerate(logs):
    y_pos = log_y_start - i * 0.25
    ax.text(3.4, y_pos, log_text, fontsize=7, color=log_color, 
            family='monospace', alpha=0.9)

# Title
plt.suptitle('Adaptive DDoS Mitigation System - Professional Web Dashboard', 
             fontsize=20, color=primary_color, weight='bold', y=0.98)

# Save
plt.tight_layout()
plt.savefig('dashboard_preview.png', dpi=200, facecolor=bg_dark, 
            edgecolor='none', bbox_inches='tight')
print("Dashboard preview saved as 'dashboard_preview.png'")
