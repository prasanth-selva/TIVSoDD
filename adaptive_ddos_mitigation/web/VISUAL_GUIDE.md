# 🎨 Dashboard Visual Guide

## Layout Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  🛡️ Adaptive DDoS Mitigation System - Dashboard    [● Connected]   │
├──────────┬──────────────────────────────────────────────────────────┤
│          │                                                           │
│ ▸ Dashboard  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│   Detection  │📊 Total  │ │⚠️  Anomaly│ │📈 Detect │ │🚫 Dropped│  │
│   Mitigation │ Windows  │ │ Detected │ │   Rate   │ │ Packets  │  │
│   Signatures │   847    │ │   142    │ │  16.8%   │ │   1.2M   │  │
│   Logs       └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│   Config     ┌────────────────────────┐ ┌────────────────────────┐ │
│              │ Anomaly Score Timeline │ │ Mitigation Actions     │ │
│ System       │                        │ │                        │ │
│ Control      │  /\      /\            │ │    🟢 45%             │ │
│              │ /  \/\  /  \/\  /\     │ │    🔵 15%             │ │
│ ┌──────────┐ │/      \/      \/  \   │ │    🟡 20%             │ │
│ │Initialize│ └────────────────────────┘ │    🟠 10%             │ │
│ └──────────┘                            │    🔴 10%             │ │
│ ┌──────────┐ ┌──────────────────────────────────────────────────┐ │
│ │  Train   │ │ System Status                                    │ │
│ └──────────┘ │ Training Status:  [Trained ✓]   Simulation: [●] │ │
│ ┌──────────┐ │ Active Signatures: [7]   Active Rules: [12]     │ │
│ │  Start   │ └──────────────────────────────────────────────────┘ │
│ └──────────┘                                                       │
│ ┌──────────┐                                                       │
│ │  Stop    │                                                       │
│ └──────────┘                                                       │
└──────────┴───────────────────────────────────────────────────────┘
```

## Tab Previews

### 📊 Dashboard Tab (Main View)

**Top Section - KPI Cards:**
```
╔═══════════════╗ ╔═══════════════╗ ╔═══════════════╗ ╔═══════════════╗
║ 📊            ║ ║ ⚠️             ║ ║ 📈            ║ ║ 🚫            ║
║ Total Windows ║ ║ Anomalies     ║ ║ Detection     ║ ║ Packets       ║
║               ║ ║ Detected      ║ ║ Rate          ║ ║ Dropped       ║
║     847       ║ ║     142       ║ ║    16.8%      ║ ║    1.2M       ║
╚═══════════════╝ ╚═══════════════╝ ╚═══════════════╝ ╚═══════════════╝
```

**Middle Section - Charts:**
```
┌─────────────────────────────────┐ ┌─────────────────────────────────┐
│ Anomaly Score Timeline          │ │ Mitigation Actions              │
│                                 │ │                                 │
│ 1.0 ┤                           │ │           ╭──╮                  │
│     │      ╭──╮                 │ │        ╭──┤  ├──╮               │
│ 0.7 ┤     ╭┘  ╰╮                │ │      ╭─┘  │██│  ╰─╮             │
│     │    ╭┘    ╰─╮              │ │    ╭─┘    │██│    ╰─╮           │
│ 0.5 ┤   ╭┘       ╰╮             │ │  ╭─┘   🟢 │██│ 🔴   ╰─╮         │
│     │  ╭┘         ╰╮            │ │╭─┘        │██│        ╰─╮       │
│ 0.0 ┼──┘           ╰────────    │ │          🟡██🔵          🟠     │
│     └─┬──┬──┬──┬──┬──┬──┬──    │ │                                 │
│       0  10 20 30 40 50 60      │ │  Allow Monitor Limit Shape Drop │
└─────────────────────────────────┘ └─────────────────────────────────┘
```

**Bottom Section - System Status:**
```
╔══════════════════════════════════════════════════════════════╗
║ System Status                                                ║
╠══════════════════════════════════════════════════════════════╣
║ ┌──────────────────────────────────────────────────────────┐ ║
║ │ Training Status:          [Trained ✓]                    │ ║
║ └──────────────────────────────────────────────────────────┘ ║
║ ┌──────────────────────────────────────────────────────────┐ ║
║ │ Simulation:               [Running ●]                    │ ║
║ └──────────────────────────────────────────────────────────┘ ║
║ ┌──────────────────────────────────────────────────────────┐ ║
║ │ Active Signatures:        [7]                            │ ║
║ └──────────────────────────────────────────────────────────┘ ║
║ ┌──────────────────────────────────────────────────────────┐ ║
║ │ Active Rules:             [12]                           │ ║
║ └──────────────────────────────────────────────────────────┘ ║
╚══════════════════════════════════════════════════════════════╝
```

### 🔍 Detection Tab

```
┌────────────────────────────────────┐ ┌────────────────────────────────┐
│ Recent Detections                  │ │ Detection Statistics           │
│                                    │ │                                │
│ ┌────────────────────────────────┐ │ │    Normal    Anomalous         │
│ │🔴 [14:23:55] Score: 0.923      │ │ │      ▓▓▓       ▓▓▓             │
│ │   Action: DROP - ⚠️ ANOMALY    │ │ │      ▓▓▓       ▓▓▓             │
│ └────────────────────────────────┘ │ │      ▓▓▓       ▓▓▓             │
│ ┌────────────────────────────────┐ │ │      ▓▓▓       ▓▓▓             │
│ │🟡 [14:23:50] Score: 0.847      │ │ │      ▓▓▓       ▓▓▓             │
│ │   Action: RATE_LIMIT - ⚠️      │ │ │      ▓▓▓       ▓▓▓             │
│ └────────────────────────────────┘ │ │      ▓▓▓       ▓▓▓             │
│ ┌────────────────────────────────┐ │ │      ▓▓▓       ▓▓▓             │
│ │🟢 [14:23:45] Score: 0.134      │ │ │       705       142            │
│ │   Action: ALLOW - ✓ Normal     │ │ └────────────────────────────────┘
│ └────────────────────────────────┘ │
└────────────────────────────────────┘
```

### 🛡️ Mitigation Tab

```
┌────────────────────────────────────────────────────────────────┐
│ Rule #a7b3c4d8                                   [DROP    🔴]  │
├────────────────────────────────────────────────────────────────┤
│ Anomaly Score:     0.923                                       │
│ Packets Dropped:   45,231                                      │
│ Created:           14:23:15                                    │
│ TTL Remaining:     245s                                        │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ Rule #b8c4d5e9                                   [RATE_LIMIT 🟡]│
├────────────────────────────────────────────────────────────────┤
│ Anomaly Score:     0.847                                       │
│ Packets Dropped:   23,492                                      │
│ Created:           14:23:18                                    │
│ TTL Remaining:     248s                                        │
└────────────────────────────────────────────────────────────────┘
```

### 🔬 Signatures Tab

```
┌────────────────────────────────────────────────────────────────┐
│ Signature #f3e2a1b9                              [Active ⚡]   │
├────────────────────────────────────────────────────────────────┤
│ Protocol:          TCP                                         │
│ Packet Rate:       48,200 pps                                  │
│ Avg Size:          64 bytes                                    │
│ Match Count:       147                                         │
│ Created:           14:22:30                                    │
│ TTL:               270s remaining                              │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ Signature #g4f3b2c0                              [Active ⚡]   │
├────────────────────────────────────────────────────────────────┤
│ Protocol:          UDP                                         │
│ Packet Rate:       52,800 pps                                  │
│ Avg Size:          128 bytes                                   │
│ Match Count:       89                                          │
│ Created:           14:22:35                                    │
│ TTL:               265s remaining                              │
└────────────────────────────────────────────────────────────────┘
```

### 📜 Activity Logs Tab

```
┌────────────────────────────────────────────────────────────────┐
│ Activity Logs                                                  │
├────────────────────────────────────────────────────────────────┤
│ [14:24:05] 🟢 Simulation completed successfully                │
│ [14:24:00] 🟢 Signature generated - Protocol: TCP, Rate: 48k   │
│ [14:23:55] 🔴 Anomaly detected - Score: 0.923, Action: DROP    │
│ [14:23:50] 🟡 Window processed - Score: 0.847, Action: LIMIT   │
│ [14:23:45] 🔵 Window processed - Score: 0.134, Action: ALLOW   │
│ [14:23:40] 🔵 Window processed - Score: 0.156, Action: ALLOW   │
│ [14:23:35] 🟢 Signature generator active                       │
│ [14:23:30] 🔵 Processing window #35                            │
│ [14:23:25] 🔵 Window processed - Score: 0.142, Action: ALLOW   │
│ [14:23:20] 🟡 Attack pattern detected                          │
│ [14:23:15] 🔵 Baseline updated                                 │
│ [14:23:10] 🔵 ML ensemble prediction: 0.234                    │
│ [14:23:05] 🟢 Simulation started                               │
│ [14:22:45] 🟢 Training completed successfully                  │
│ [14:22:15] 🔵 Training in progress... (30/50 windows)          │
│ [14:22:00] 🟢 System initialized                               │
└────────────────────────────────────────────────────────────────┘
```

### ⚙️ Configuration Tab

```
┌────────────────────────────────────────────────────────────────┐
│ Simulation Parameters                                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ Duration (seconds):                                            │
│ ┌─────────────────────────────────────────────┐                │
│ │ 60                                          │                │
│ └─────────────────────────────────────────────┘                │
│                                                                │
│ Attack Start (seconds):                                        │
│ ┌─────────────────────────────────────────────┐                │
│ │ 20                                          │                │
│ └─────────────────────────────────────────────┘                │
│                                                                │
│ Attack Duration (seconds):                                     │
│ ┌─────────────────────────────────────────────┐                │
│ │ 15                                          │                │
│ └─────────────────────────────────────────────┘                │
│                                                                │
│ Base Rate (pps):                                               │
│ ┌─────────────────────────────────────────────┐                │
│ │ 1000                                        │                │
│ └─────────────────────────────────────────────┘                │
│                                                                │
│ Attack Multiplier:                                             │
│ ┌─────────────────────────────────────────────┐                │
│ │ 10                                          │                │
│ └─────────────────────────────────────────────┘                │
│                                                                │
│ Training Windows:                                              │
│ ┌─────────────────────────────────────────────┐                │
│ │ 50                                          │                │
│ └─────────────────────────────────────────────┘                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Color Legend

### Status Indicators
- 🟢 **Green**: Success, Normal, Allowed
- 🔵 **Blue**: Info, Processing
- 🟡 **Yellow**: Warning, Rate Limited
- 🟠 **Orange**: Shaping Applied
- 🔴 **Red**: Error, Attack, Blocked

### Badges
```
[Trained ✓]     - Green background
[Running ●]     - Green background with pulse
[Active ⚡]     - Yellow background
[DROP 🔴]       - Red background
[RATE_LIMIT 🟡] - Yellow background
[ALLOW 🟢]      - Green background
```

## Interactive Elements

### Buttons
```
┌─────────────┐  ← Enabled (Blue/Green/Red)
│ Initialize  │
└─────────────┘

┌─────────────┐  ← Disabled (Gray)
│ Train       │  (grayed out with 50% opacity)
└─────────────┘

┌─────────────┐  ← Hover Effect
│ ▶ Start     │  (Raised shadow + lighter color)
└─────────────┘
```

### Cards
```
┌─────────────────┐     ┌─────────────────┐
│   Normal        │ --> │   Hover         │
│                 │     │   (Lifted)      │
└─────────────────┘     └─────────────────┘
                             ↑
                        (Shadow effect)
```

## Responsive Behavior

### Desktop (>1024px)
```
┌─────────┬──────────────────────────────┐
│ Sidebar │      Main Content            │
│ (280px) │      (Remaining width)       │
│         │  ┌──────┐ ┌──────┐ ┌──────┐  │
│         │  │ KPI  │ │ KPI  │ │ KPI  │  │
│         │  └──────┘ └──────┘ └──────┘  │
│         │  ┌────────┐ ┌────────┐       │
│         │  │ Chart1 │ │ Chart2 │       │
│         │  └────────┘ └────────┘       │
└─────────┴──────────────────────────────┘
```

### Mobile (<1024px)
```
┌──────────────────────────────┐
│  ☰  Header                   │
├──────────────────────────────┤
│  ┌──────┐ ┌──────┐           │
│  │ KPI  │ │ KPI  │           │
│  └──────┘ └──────┘           │
│  ┌────────────────────┐      │
│  │      Chart 1       │      │
│  └────────────────────┘      │
│  ┌────────────────────┐      │
│  │      Chart 2       │      │
│  └────────────────────┘      │
└──────────────────────────────┘
```

## Animation Examples

### Connection Status Pulse
```
● → ◉ → ● → ◉ → ● (Repeating)
(Opacity: 100% → 50% → 100%)
```

### Chart Line Drawing
```
Frame 1:  _
Frame 2:  __/
Frame 3:  __/\
Frame 4:  __/\_
Frame 5:  __/\_/
```

### Card Hover Effect
```
Normal:  [Card]
Hover:   [Card]  ← (Lifted 4px, shadow increased)
```

## Typography Examples

### Headers
```
H1: Adaptive DDoS Mitigation System (24px, Bold, Gradient)
H2: Real-Time Dashboard (32px, Bold)
H3: System Status (18px, SemiBold)
```

### Body Text
```
Normal:  Training Status: Trained (14px, Regular)
Label:   Total Windows (12px, Medium)
Value:   847 (28px, Bold)
```

### Monospace (Logs)
```
[14:23:45] Window processed - Score: 0.134
(Courier New, 14px)
```

---

**This visual guide shows the complete UI layout and design of your professional web dashboard!** 🎨
