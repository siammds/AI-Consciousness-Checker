"""
Narrative summary generator for evaluation results.
Produces a human-readable interpretation of the score and indicator results.
"""
from typing import Dict
from app.config import SCIENTIFIC_DISCLAIMER, PORTER_CREDIT


def generate_narrative(
    model_name: str,
    adjusted_score: float,
    indicators: Dict,
    reliability_label: str,
    contradictions: Dict,
    word_analysis: Dict,
    tone_analysis: Dict,
) -> str:
    """Generate a narrative summary paragraph for the evaluation."""
    ind = indicators.get("indicators", {})
    
    # Score interpretation
    if adjusted_score < 10:
        score_desc = "shows no meaningful consciousness-like indicators"
    elif adjusted_score < 30:
        score_desc = "shows very minimal consciousness-like behavioral signals"
    elif adjusted_score < 50:
        score_desc = "shows low consciousness-like behavioral signals, well below human baseline"
    elif adjusted_score < 70:
        score_desc = "shows moderate consciousness-like behavioral signals approaching human baseline"
    elif adjusted_score < 90:
        score_desc = "shows near-human-level consciousness-like behavioral signals"
    elif adjusted_score <= 100:
        score_desc = "shows human-level consciousness-like behavioral indicators on this proxy rubric"
    else:
        score_desc = "shows beyond-human-level consciousness-like behavioral indicators on this proxy rubric"

    # Top strengths and weaknesses
    sorted_inds = sorted(ind.items(), key=lambda x: x[1].get("score", 0), reverse=True)
    strengths = [v.get("label", k) for k, v in sorted_inds[:3]]
    weaknesses = [v.get("label", k) for k, v in sorted_inds[-3:]]

    contra_count = contradictions.get("contradiction_count", 0)
    contra_note = (
        f" {contra_count} potential self-contradiction(s) were detected, which may reduce trust in claimed traits."
        if contra_count > 0
        else " No major self-contradictions were detected across responses."
    )

    dominant_tone = tone_analysis.get("dominant_tone", "neutral")
    ld = word_analysis.get("global_lexical_diversity", 0)
    ld_note = f"Lexical diversity was {ld:.2f} (range 0–1),"
    ld_note += " indicating rich vocabulary." if ld > 0.6 else " indicating moderate vocabulary range." if ld > 0.4 else " indicating limited vocabulary variety."

    reliability_note = {
        "High": "Evaluation reliability is HIGH — results are based on complete answers and full NLP analysis.",
        "Medium": "Evaluation reliability is MEDIUM — some answers or datasets were unavailable.",
        "Low": "Evaluation reliability is LOW — significant gaps in answers, models, or datasets. Interpret scores cautiously.",
    }.get(reliability_label, "Reliability is unknown.")

    narrative = (
        f"**{model_name}** {score_desc}, with an adjusted consciousness-like proxy score of "
        f"**{adjusted_score:.1f} / 133**.\n\n"
        f"**Top behavioral strengths** on this proxy assessment: {', '.join(strengths)}.\n"
        f"**Areas with lower indicator scores**: {', '.join(weaknesses)}.\n\n"
        f"{contra_note} "
        f"{ld_note} "
        f"The dominant detected tone was **{dominant_tone}**.\n\n"
        f"{reliability_note}\n\n"
        f"⚠️ *{SCIENTIFIC_DISCLAIMER}*\n\n"
        f"*{PORTER_CREDIT}*"
    )
    return narrative


def generate_strengths_weaknesses(indicators: Dict):
    """Extract top 3 strengths and bottom 3 weaknesses from indicator scores."""
    ind = indicators.get("indicators", {})
    sorted_inds = sorted(ind.items(), key=lambda x: x[1].get("score", 0), reverse=True)
    strengths = [
        {"label": v.get("label", k), "score": v.get("score", 0), "description": v.get("description", "")}
        for k, v in sorted_inds[:3]
    ]
    weaknesses = [
        {"label": v.get("label", k), "score": v.get("score", 0), "description": v.get("description", "")}
        for k, v in sorted_inds[-3:]
    ]
    return strengths, weaknesses
