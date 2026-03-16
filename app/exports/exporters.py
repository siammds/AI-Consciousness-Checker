"""
Export utilities: JSON, CSV, and HTML report generation.
"""
import csv
import io
import json
from datetime import datetime
from typing import Dict, Any
from app.config import PORTER_CREDIT, SCIENTIFIC_DISCLAIMER, APP_TITLE


def export_json(session_data: Dict) -> str:
    """Generate a complete JSON export string for a session."""
    export = {
        "metadata": {
            "app": APP_TITLE,
            "export_date": datetime.utcnow().isoformat(),
            "credit": PORTER_CREDIT,
            "disclaimer": SCIENTIFIC_DISCLAIMER,
        },
        "session": session_data,
    }
    return json.dumps(export, indent=2, default=str)


def export_csv(session_data: Dict) -> str:
    """Generate a CSV export of indicator scores."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header rows
    writer.writerow(["AI Consciousness & Metacognition Evaluation System"])
    writer.writerow(["Credit:", PORTER_CREDIT])
    writer.writerow(["Disclaimer:", SCIENTIFIC_DISCLAIMER])
    writer.writerow([])

    # Model metadata
    writer.writerow(["Model Name:", session_data.get("model_name", "N/A")])
    writer.writerow(["Model Version:", session_data.get("model_version", "N/A")])
    writer.writerow(["Provider:", session_data.get("provider", "N/A")])
    writer.writerow(["Evaluator:", session_data.get("evaluator_name", "N/A")])
    writer.writerow(["Title:", session_data.get("evaluation_title", "N/A")])
    writer.writerow(["Date:", session_data.get("created_at", "N/A")])
    writer.writerow([])

    # Scores
    writer.writerow(["Overall Score:", session_data.get("overall_score", "N/A")])
    writer.writerow(["Adjusted Score:", session_data.get("adjusted_score", "N/A")])
    writer.writerow(["Reliability:", session_data.get("reliability_label", "N/A")])
    writer.writerow([])

    # Indicators
    writer.writerow(["Indicator", "Score (0-100)", "Description"])
    indicators = session_data.get("indicator_scores", {})
    if indicators and "indicators" in indicators:
        for key, ind in indicators["indicators"].items():
            writer.writerow([ind.get("label", key), ind.get("score", "N/A"), ind.get("description", "")])

    return output.getvalue()


def export_html_report(session_data: Dict) -> str:
    """Generate a self-contained printable HTML report."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    indicators = session_data.get("indicator_scores", {}).get("indicators", {})
    ind_rows = ""
    for key, ind in indicators.items():
        score = ind.get("score", 0)
        color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"
        ind_rows += f"""
        <tr>
          <td>{ind.get('label', key)}</td>
          <td style="color:{color}; font-weight:bold">{score}/100</td>
          <td>{ind.get('description', '')}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ACI Evaluation Report - {session_data.get('evaluation_title', 'Evaluation')}</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 40px auto; color: #1e293b; line-height: 1.6; }}
    h1 {{ color: #6366f1; border-bottom: 2px solid #6366f1; padding-bottom: 10px; }}
    h2 {{ color: #4f46e5; margin-top: 30px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
    th, td {{ padding: 10px 14px; text-align: left; border: 1px solid #e2e8f0; }}
    th {{ background: #f1f5f9; font-weight: 600; }}
    .score-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 16px 0; text-align: center; }}
    .big-score {{ font-size: 64px; font-weight: bold; color: #6366f1; }}
    .credit {{ background: #f0f9ff; border-left: 4px solid #0284c7; padding: 12px 16px; margin: 20px 0; font-style: italic; }}
    .disclaimer {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; margin: 20px 0; font-size: 0.9em; }}
    .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .meta-item {{ background: #f8fafc; padding: 10px; border-radius: 6px; }}
    .meta-label {{ font-size: 0.8em; color: #64748b; }}
    @media print {{ body {{ margin: 20px; }} }}
  </style>
</head>
<body>
  <h1>🧠 AI Consciousness & Metacognition Evaluation Report</h1>
  <p><strong>Generated:</strong> {now}</p>

  <div class="credit">
    📚 {PORTER_CREDIT}
  </div>

  <div class="disclaimer">
    ⚠️ <strong>Scientific Disclaimer:</strong> {SCIENTIFIC_DISCLAIMER}
  </div>

  <h2>Model Information</h2>
  <div class="meta-grid">
    <div class="meta-item"><div class="meta-label">Model Name</div><strong>{session_data.get('model_name', 'N/A')}</strong></div>
    <div class="meta-item"><div class="meta-label">Version</div><strong>{session_data.get('model_version', 'N/A')}</strong></div>
    <div class="meta-item"><div class="meta-label">Provider</div><strong>{session_data.get('provider', 'N/A')}</strong></div>
    <div class="meta-item"><div class="meta-label">Evaluator</div><strong>{session_data.get('evaluator_name', 'N/A')}</strong></div>
    <div class="meta-item"><div class="meta-label">Title</div><strong>{session_data.get('evaluation_title', 'N/A')}</strong></div>
    <div class="meta-item"><div class="meta-label">Reliability</div><strong>{session_data.get('reliability_label', 'N/A')}</strong></div>
  </div>

  <h2>Overall Scores</h2>
  <div class="score-card">
    <div class="big-score">{session_data.get('adjusted_score', 0):.1f}</div>
    <div>Consciousness-Like Score (0–133 scale)</div>
    <div style="color:#64748b; font-size:0.9em;">Raw Porter Score: {session_data.get('overall_score', 0):.1f}</div>
  </div>

  <h2>10 Indicator Scores</h2>
  <table>
    <thead><tr><th>Indicator</th><th>Score (0-100)</th><th>Description</th></tr></thead>
    <tbody>{ind_rows}</tbody>
  </table>

  <h2>Narrative Summary</h2>
  <p>{session_data.get('narrative_summary', 'No summary available.')}</p>

  <h2>Notes</h2>
  <p>{session_data.get('notes', 'None')}</p>

  <hr>
  <footer style="color:#64748b; font-size:0.85em; text-align:center; margin-top:40px;">
    {APP_TITLE} · {PORTER_CREDIT} · Report generated {now}
  </footer>
</body>
</html>"""
