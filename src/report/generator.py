"""
PTSD Session Report Generator
==============================

Generates a downloadable HTML report at the end of a monitoring session.

Report includes:
  - Patient info & session summary
  - PTSD risk assessment (overall probability)
  - Heart rate analysis (min/max/avg + sparkline)
  - Emotion distribution
  - Audio trigger log
  - Gesture analysis
  - Object trigger summary
  - Risk score timeline
  - Clinical recommendation
"""

from datetime import datetime


def _risk_color(score):
    if score < 30: return "#22c55e"
    if score < 60: return "#f59e0b"
    return "#ef4444"


def _risk_label(score):
    if score < 20: return "Very Low"
    if score < 35: return "Low"
    if score < 50: return "Moderate"
    if score < 70: return "High"
    return "Very High"


def _risk_verdict(avg_risk, max_risk, high_pct):
    """Generate clinical verdict based on session data."""
    if avg_risk < 20 and max_risk < 40:
        return (
            "UNLIKELY",
            "The patient showed minimal signs of stress or PTSD-related triggers during this session. "
            "Physiological and behavioral indicators remained within normal ranges.",
            "#22c55e"
        )
    elif avg_risk < 40:
        return (
            "LOW PROBABILITY",
            "The patient displayed occasional signs of mild anxiety or stress. "
            "Some trigger responses were detected but remained brief and low-intensity. "
            "Continued monitoring is recommended.",
            "#38bdf8"
        )
    elif avg_risk < 60:
        return (
            "MODERATE PROBABILITY",
            "The patient exhibited recurring signs of distress across multiple modalities. "
            f"High-risk episodes were detected in {high_pct:.0f}% of the session. "
            "A follow-up evaluation with a mental health professional is strongly recommended.",
            "#f59e0b"
        )
    else:
        return (
            "HIGH PROBABILITY",
            "The patient showed significant and sustained PTSD-related trigger responses. "
            f"Risk scores exceeded the critical threshold in {high_pct:.0f}% of the session. "
            "Immediate referral to a qualified mental health specialist is recommended.",
            "#ef4444"
        )


def _sparkline_svg(values, color, width=400, height=50):
    """Generate an inline SVG sparkline from a list of values."""
    if not values or len(values) < 2:
        return ""
    max_v = max(values) if max(values) > 0 else 1
    min_v = min(values)
    rng = max_v - min_v if max_v != min_v else 1
    step = width / (len(values) - 1)
    points = []
    for i, v in enumerate(values):
        x = round(i * step, 1)
        y = round(height - ((v - min_v) / rng) * (height - 4) - 2, 1)
        points.append(f"{x},{y}")
    polyline = " ".join(points)
    return f'''<svg width="{width}" height="{height}" style="display:block">
        <polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>
    </svg>'''


def generate_report(session_data: dict) -> str:
    """
    Generate an HTML report from session data.

    Args:
        session_data: dict with keys:
            patient_name: str
            session_start: datetime
            session_end: datetime
            risk_history: list[float]
            hr_history: list[float]
            emotion_history: list[str]
            audio_triggers: list[dict]    — [{time, name}]
            gesture_history: list[str]
            object_history: list[str]
            trigger_log: list[dict]       — [{type, time, text}]
            module_scores: dict           — {emotion, object, audio, stress, gesture} avg scores
    """
    # ── Extract data ──
    name = session_data.get("patient_name", "Anonymous")
    start = session_data.get("session_start", datetime.now())
    end = session_data.get("session_end", datetime.now())
    duration = end - start
    mins = int(duration.total_seconds() // 60)
    secs = int(duration.total_seconds() % 60)

    risk_hist = list(session_data.get("risk_history", []))
    hr_hist = list(session_data.get("hr_history", []))
    emotions = session_data.get("emotion_history", [])
    audio_triggers = session_data.get("audio_triggers", [])
    gestures = session_data.get("gesture_history", [])
    objects = session_data.get("object_history", [])
    trigger_log = session_data.get("trigger_log", [])
    module_scores = session_data.get("module_scores", {})

    # ── Calculate stats ──
    avg_risk = sum(risk_hist) / len(risk_hist) if risk_hist else 0
    max_risk = max(risk_hist) if risk_hist else 0
    min_risk = min(risk_hist) if risk_hist else 0
    high_count = sum(1 for r in risk_hist if r >= 60)
    high_pct = (high_count / len(risk_hist) * 100) if risk_hist else 0

    avg_hr = sum(hr_hist) / len(hr_hist) if hr_hist else 0
    max_hr = max(hr_hist) if hr_hist else 0
    min_hr = min(hr_hist) if hr_hist else 0

    # Emotion distribution
    emotion_counts = {}
    for e in emotions:
        emotion_counts[e] = emotion_counts.get(e, 0) + 1
    total_emo = len(emotions) or 1
    emotion_pcts = {k: round(v / total_emo * 100, 1) for k, v in emotion_counts.items()}
    dominant_emo = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"

    # Gesture frequency
    gesture_counts = {}
    for g in gestures:
        gesture_counts[g] = gesture_counts.get(g, 0) + 1

    # Object frequency
    object_counts = {}
    for o in objects:
        object_counts[o] = object_counts.get(o, 0) + 1

    # Verdict
    verdict_label, verdict_text, verdict_color = _risk_verdict(avg_risk, max_risk, high_pct)

    # Sparklines
    risk_svg = _sparkline_svg(risk_hist, _risk_color(avg_risk), 500, 60)
    hr_svg = _sparkline_svg(hr_hist, "#38bdf8", 500, 60)

    # ── Build emotion bars HTML ──
    emo_colors = {
        "happy": "#22c55e", "neutral": "#94a3b8", "surprise": "#a78bfa",
        "fear": "#ef4444", "angry": "#f97316", "sad": "#3b82f6",
        "disgust": "#84cc16", "contempt": "#f59e0b"
    }
    emo_bars_html = ""
    for emo, pct in sorted(emotion_pcts.items(), key=lambda x: -x[1]):
        c = emo_colors.get(emo, "#94a3b8")
        emo_bars_html += f'''
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
            <div style="width:80px;font-size:12px;color:#cbd5e1;text-transform:capitalize">{emo}</div>
            <div style="flex:1;background:#1e293b;border-radius:99px;height:8px;overflow:hidden">
                <div style="height:100%;width:{pct}%;background:{c};border-radius:99px"></div>
            </div>
            <div style="width:40px;font-size:12px;color:#94a3b8;text-align:right">{pct:.0f}%</div>
        </div>'''

    # ── Gesture table rows ──
    gesture_rows = ""
    for g, count in sorted(gesture_counts.items(), key=lambda x: -x[1]):
        gesture_rows += f'<tr><td style="padding:6px 12px;color:#cbd5e1">{g}</td><td style="padding:6px 12px;color:#f59e0b;text-align:center">{count}</td></tr>'
    if not gesture_rows:
        gesture_rows = '<tr><td colspan="2" style="padding:12px;color:#64748b;text-align:center">No distress gestures detected</td></tr>'

    # ── Audio trigger rows ──
    audio_rows = ""
    for t in audio_triggers[:20]:
        audio_rows += f'<tr><td style="padding:6px 12px;color:#64748b;font-family:monospace;font-size:12px">{t.get("time", "")}</td><td style="padding:6px 12px;color:#fca5a5">{t.get("name", "")}</td></tr>'
    if not audio_rows:
        audio_rows = '<tr><td colspan="2" style="padding:12px;color:#64748b;text-align:center">No audio triggers detected</td></tr>'

    # ── Object rows ──
    object_tags = ""
    for o, count in sorted(object_counts.items(), key=lambda x: -x[1]):
        object_tags += f'<span style="display:inline-block;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:#fca5a5;font-size:12px;padding:4px 12px;border-radius:99px;margin:3px">{o} ×{count}</span>'
    if not object_tags:
        object_tags = '<span style="color:#64748b">No trigger objects detected</span>'

    # ── Trigger log rows ──
    log_rows = ""
    for ev in list(trigger_log)[:30]:
        icon = "🔊" if ev.get("type") == "audio" else "🤜" if ev.get("type") == "gesture" else "⚠️"
        log_rows += f'''<div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid #1e293b;font-size:12px">
            <span style="color:#64748b;font-family:monospace;white-space:nowrap">{ev.get("time", "")}</span>
            <span style="color:#cbd5e1">{icon} {ev.get("text", "")}</span>
        </div>'''

    # ── Module score bars ──
    mod_labels = {"emotion": "😨 Emotion", "object": "🎯 Objects", "audio": "🔊 Audio", "stress": "💓 Stress", "gesture": "🤜 Gesture"}
    module_bars = ""
    for mod, label in mod_labels.items():
        sc = module_scores.get(mod, 0)
        c = _risk_color(sc)
        module_bars += f'''
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
            <div style="width:100px;font-size:12px;color:#cbd5e1">{label}</div>
            <div style="flex:1;background:#1e293b;border-radius:99px;height:8px;overflow:hidden">
                <div style="height:100%;width:{sc:.0f}%;background:{c};border-radius:99px"></div>
            </div>
            <div style="width:40px;font-size:13px;color:{c};text-align:right;font-weight:600">{sc:.0f}%</div>
        </div>'''

    # ── Generate HTML ──
    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>PTSD Session Report — {name}</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{
        font-family: 'DM Sans', sans-serif;
        background: #0f172a;
        color: #e2e8f0;
        padding: 40px;
        max-width: 900px;
        margin: 0 auto;
    }}
    .card {{
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }}
    .card-title {{
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 16px;
    }}
    h1 {{
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 4px;
    }}
    .subtitle {{
        color: #64748b;
        font-size: 14px;
    }}
    .verdict-box {{
        border-radius: 12px;
        padding: 24px;
        margin: 20px 0;
        border: 2px solid;
    }}
    .stat-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
    }}
    .stat-item {{
        background: #0f172a;
        border-radius: 8px;
        padding: 14px;
        text-align: center;
    }}
    .stat-value {{
        font-family: 'DM Mono', monospace;
        font-size: 24px;
        font-weight: 600;
    }}
    .stat-label {{
        font-size: 11px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 4px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
    }}
    th {{
        text-align: left;
        font-size: 11px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 8px 12px;
        border-bottom: 1px solid #334155;
    }}
    .footer {{
        text-align: center;
        color: #475569;
        font-size: 12px;
        margin-top: 30px;
        padding-top: 20px;
        border-top: 1px solid #1e293b;
    }}
    @media print {{
        body {{ background: #fff; color: #000; padding: 20px; }}
        .card {{ border-color: #ddd; background: #f9f9f9; }}
        .stat-item {{ background: #eee; }}
    }}
</style>
</head>
<body>

<!-- HEADER -->
<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:30px">
    <div>
        <h1>🧠 PTSD Session Report</h1>
        <div class="subtitle">Generated by PTSD Sentinel — AI Trigger Detection System</div>
    </div>
    <div style="text-align:right;font-size:12px;color:#64748b;line-height:1.8">
        <div><strong style="color:#cbd5e1">{name}</strong></div>
        <div>{start.strftime("%d %B %Y")}</div>
        <div>{start.strftime("%I:%M %p")} — {end.strftime("%I:%M %p")}</div>
        <div>Duration: {mins}m {secs}s</div>
    </div>
</div>

<!-- VERDICT -->
<div class="verdict-box" style="border-color:{verdict_color};background:rgba({int(verdict_color[1:3],16)},{int(verdict_color[3:5],16)},{int(verdict_color[5:7],16)},0.08)">
    <div style="font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:#64748b;margin-bottom:8px">PTSD Assessment</div>
    <div style="font-size:28px;font-weight:700;color:{verdict_color};margin-bottom:8px">{verdict_label}</div>
    <div style="font-size:14px;color:#94a3b8;line-height:1.6">{verdict_text}</div>
</div>

<!-- OVERALL STATS -->
<div class="card">
    <div class="card-title">📊 Session Overview</div>
    <div class="stat-grid">
        <div class="stat-item">
            <div class="stat-value" style="color:{_risk_color(avg_risk)}">{avg_risk:.0f}%</div>
            <div class="stat-label">Avg Risk</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" style="color:{_risk_color(max_risk)}">{max_risk:.0f}%</div>
            <div class="stat-label">Peak Risk</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" style="color:#f59e0b">{high_pct:.0f}%</div>
            <div class="stat-label">Time in High Risk</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" style="color:#94a3b8">{len(risk_hist)}</div>
            <div class="stat-label">Data Points</div>
        </div>
    </div>
</div>

<!-- MODULE SCORES -->
<div class="card">
    <div class="card-title">🤖 Module Score Averages</div>
    {module_bars}
</div>

<!-- RISK TIMELINE -->
<div class="card">
    <div class="card-title">📈 Risk Score Timeline</div>
    <div style="background:#0f172a;border-radius:8px;padding:16px">
        {risk_svg}
        <div style="display:flex;justify-content:space-between;font-size:11px;color:#64748b;margin-top:6px">
            <span>Session Start</span>
            <span>Min: {min_risk:.0f}% · Avg: {avg_risk:.0f}% · Max: {max_risk:.0f}%</span>
            <span>Session End</span>
        </div>
    </div>
</div>

<!-- HEART RATE -->
<div class="card">
    <div class="card-title">💓 Heart Rate Analysis</div>
    <div class="stat-grid" style="grid-template-columns:repeat(3,1fr);margin-bottom:16px">
        <div class="stat-item">
            <div class="stat-value" style="color:#22c55e">{min_hr:.0f}</div>
            <div class="stat-label">Min BPM</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" style="color:#38bdf8">{avg_hr:.0f}</div>
            <div class="stat-label">Avg BPM</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" style="color:#ef4444">{max_hr:.0f}</div>
            <div class="stat-label">Max BPM</div>
        </div>
    </div>
    <div style="background:#0f172a;border-radius:8px;padding:16px">
        {hr_svg}
    </div>
</div>

<!-- EMOTION -->
<div class="card">
    <div class="card-title">😨 Emotion Distribution</div>
    <div style="margin-bottom:12px;font-size:13px;color:#94a3b8">
        Dominant mood: <strong style="color:#e2e8f0;text-transform:capitalize">{dominant_emo}</strong>
        &nbsp;·&nbsp; {len(emotions)} readings
    </div>
    {emo_bars_html}
</div>

<!-- GESTURES -->
<div class="card">
    <div class="card-title">🤜 Gesture Analysis</div>
    <table>
        <tr><th>Gesture</th><th style="text-align:center">Occurrences</th></tr>
        {gesture_rows}
    </table>
</div>

<!-- AUDIO TRIGGERS -->
<div class="card">
    <div class="card-title">🔊 Audio Triggers Detected</div>
    <table>
        <tr><th style="width:100px">Time</th><th>Sound</th></tr>
        {audio_rows}
    </table>
</div>

<!-- OBJECTS -->
<div class="card">
    <div class="card-title">🎯 Trigger Objects Detected</div>
    <div style="padding:8px 0">{object_tags}</div>
</div>

<!-- EVENT LOG -->
<div class="card">
    <div class="card-title">📋 Trigger Event Log</div>
    <div style="max-height:300px;overflow-y:auto">
        {log_rows if log_rows else '<div style="color:#64748b;text-align:center;padding:16px">No trigger events recorded</div>'}
    </div>
</div>

<!-- FOOTER -->
<div class="footer">
    <div>PTSD Sentinel — AI-Based Trigger Detection System</div>
    <div style="margin-top:4px">Report generated on {datetime.now().strftime("%d %B %Y at %I:%M %p")}</div>
    <div style="margin-top:4px">This report is for informational purposes only and does not constitute a medical diagnosis.</div>
</div>

</body>
</html>'''

    return html
