"""
combined_bias_engine.py
━━━━━━━━━━━━━━━━━━━━━━━
Chapter 17 & 18  —  Combined Bias Decision Engine
NIFTY Options Analysis Dashboard  ·  Shantanu Samanta

PURPOSE
-------
Pure-function module that implements the 4-Quadrant Decision Matrix (Chapter 17)
and the 5 Divergence Type detectors (Chapter 18) from the NIFTY Combined Manual.

Takes the outputs of two already-computed engines:
  • compute_section34_bias()   →  s34  dict
  • classify_iv_smile_scenario() →  smile dict
  • compute_metrics()           →  m    dict   (for pcr, atm, support, resistance)

Returns a single verdict dict consumed by the dashboard panel.

NO STREAMLIT IMPORTS — this file must remain a plain Python module.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# S3/4 SCORE BAND
# ─────────────────────────────────────────────────────────────────────────────

def get_s34_band(score: float) -> str:
    """Map S3/4 bias score to a band letter A–E."""
    if   score >= 51:   return "A"   # Strong Bull
    elif score >= 16:   return "B"   # Mild Bull
    elif score >= -15:  return "C"   # Neutral
    elif score >= -50:  return "D"   # Mild Bear
    else:               return "E"   # Strong Bear


# ─────────────────────────────────────────────────────────────────────────────
# IV SMILE BUCKET
# ─────────────────────────────────────────────────────────────────────────────

# Scenario IDs that represent a "Bearish / Fear" sentiment on the smile
_BEARISH_FEAR_IDS  = {1, 2, 3, 9}   # Put Skew, Crash Fear, Bearish Drift, Two-Sided Fork
# Scenario IDs that represent a "Bullish / Neutral" smile
_BULLISH_NEUTRAL_IDS = {4, 5, 6}    # Call Skew, Melt-Up, Post-Crash Relief
# Everything else (0, 7, 8, 10, 11, 12) → NEUTRAL

def get_smile_bucket(scenario_id: int) -> str:
    """Classify IV smile into one of three composite buckets."""
    if scenario_id in _BEARISH_FEAR_IDS:
        return "BEARISH_FEAR"
    elif scenario_id in _BULLISH_NEUTRAL_IDS:
        return "BULLISH_NEUTRAL"
    else:
        return "NEUTRAL"


# ─────────────────────────────────────────────────────────────────────────────
# 4-QUADRANT CLASSIFICATION  (Chapter 17)
# ─────────────────────────────────────────────────────────────────────────────

_QUADRANT_META = {
    "Q1": {
        "name":   "Full Bull Alignment",
        "short":  "Q1 — FULL BULL",
        "color":  "#059669",          # GREEN
        "badge_bg": "#ECFDF5",
        "description": (
            "Structure is bullish (S3/4 positive) AND the IV Smile confirms "
            "that sentiment is NOT overly fearful. Both engines agree — highest "
            "probability bullish environment. Favour long delta, call spreads, "
            "and systematic put-selling when IV rank is elevated."
        ),
        "action": "LEAN BULLISH  —  long delta, call debit spreads, theta-selling below spot",
    },
    "Q2": {
        "name":   "Structural Bull / Sentiment Cautious",
        "short":  "Q2 — STRUCTURAL BULL / CAUTIOUS",
        "color":  "#D97706",          # AMBER
        "badge_bg": "#FFFBEB",
        "description": (
            "OI structure and momentum are bullish BUT the IV Smile is showing "
            "put-skew or fear. Institutions are hedging into the rally. The move "
            "can continue but at risk of a sharp reversal if the put-wing keeps "
            "building. Reduce position size; favour protective collars or limited-risk "
            "long structures. Watch S4 IV Skew component for further divergence."
        ),
        "action": "BULLISH WITH CAUTION  —  reduced size, hedge with put spreads, trail stops",
    },
    "Q3": {
        "name":   "Structural Bear / Sentiment Recovering",
        "short":  "Q3 — STRUCTURAL BEAR / RECOVERING",
        "color":  "#2563EB",          # BLUE
        "badge_bg": "#EFF6FF",
        "description": (
            "OI structure and momentum are bearish BUT the IV Smile is showing "
            "relief or call buying — fear is deflating. This is the most nuanced "
            "quadrant: it can precede a bottom or be a dead-cat bounce. Do NOT "
            "short aggressively into a deflating put-wing. Wait for S3/4 score to "
            "turn less negative before adding long exposure."
        ),
        "action": "CAUTIOUSLY BEARISH  —  cover shorts on IV crush, wait for structure to improve",
    },
    "Q4": {
        "name":   "Full Bear Alignment",
        "short":  "Q4 — FULL BEAR",
        "color":  "#DC2626",          # RED
        "badge_bg": "#FEF2F2",
        "description": (
            "Structure is bearish (S3/4 negative) AND the IV Smile confirms "
            "fear / put-skew. Both engines agree — highest probability bearish "
            "environment. Favour short delta, put spreads, and call-selling above "
            "resistance. Highest confidence short signal when S3/4 ≤ −40 and "
            "smile is Crash Fear (Sc02)."
        ),
        "action": "LEAN BEARISH  —  short delta, put debit spreads, bear call spreads above resistance",
    },
    "CN": {
        "name":   "Neutral / No Edge",
        "short":  "CN — NEUTRAL",
        "color":  "#6B7280",          # MUTED
        "badge_bg": "#F9FAFB",
        "description": (
            "Either the S3/4 score is in the neutral band (−15 to +15) or the IV "
            "Smile is indeterminate / pre-event. Neither engine provides a reliable "
            "directional edge. Avoid directional positions; favour premium-selling "
            "structures (iron condors) only if IV rank supports it."
        ),
        "action": "NO DIRECTIONAL EDGE  —  avoid naked direction, favour non-directional structures",
    },
}


def classify_quadrant(s34_score: float, scenario_id: int) -> dict:
    """
    Returns a dict:
      { quadrant, name, short, color, badge_bg, description, action, smile_bucket }
    """
    band         = get_s34_band(s34_score)
    smile_bucket = get_smile_bucket(scenario_id)

    # Neutral S3/4 band → always CN regardless of smile
    if band == "C":
        q = "CN"
    # Positive S3/4 (A or B)
    elif band in ("A", "B"):
        if smile_bucket == "BULLISH_NEUTRAL":
            q = "Q1"
        elif smile_bucket == "BEARISH_FEAR":
            q = "Q2"
        else:                               # NEUTRAL smile
            q = "Q1"                        # lean bullish when structure is bullish
    # Negative S3/4 (D or E)
    else:
        if smile_bucket == "BULLISH_NEUTRAL":
            q = "Q3"
        elif smile_bucket == "BEARISH_FEAR":
            q = "Q4"
        else:                               # NEUTRAL smile
            q = "Q4"                        # lean bearish when structure is bearish

    meta = _QUADRANT_META[q]
    return {
        "quadrant":     q,
        "name":         meta["name"],
        "short":        meta["short"],
        "color":        meta["color"],
        "badge_bg":     meta["badge_bg"],
        "description":  meta["description"],
        "action":       meta["action"],
        "smile_bucket": smile_bucket,
        "s34_band":     band,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DIVERGENCE DETECTION  (Chapter 18)
# ─────────────────────────────────────────────────────────────────────────────

_DIVERGENCE_META = {
    1: {
        "type":   "Type 1 — Capitulation Bottom",
        "color":  "#059669",
        "badge_bg": "#ECFDF5",
        "detail": (
            "S3/4 is at extreme bear levels (≤−51) AND the IV Smile is showing "
            "Crash Fear (Sc02, put wing >12pts + IV rank ≥65). When both engines "
            "simultaneously hit maximum bearish readings, the risk/reward for new "
            "short positions deteriorates sharply. Hedgers are already in — they "
            "are the sellers of the rally that follows. Watch for put-wing deflation "
            "as the first sign of capitulation completing."
        ),
        "warning": "POTENTIAL CAPITULATION BOTTOM — do not initiate new shorts at these levels",
    },
    2: {
        "type":   "Type 2 — Structural Ceiling",
        "color":  "#D97706",
        "badge_bg": "#FFFBEB",
        "detail": (
            "S3/4 is at strong bull levels (≥+51) BUT the IV Smile is building "
            "a put-skew (Sc01/Sc03). This indicates institutions are hedging long "
            "positions even as the structural score peaks. Smart money is reducing "
            "risk at the top — a classic ceiling pattern. Reduce longs and avoid "
            "adding fresh long exposure at these combined readings."
        ),
        "warning": "STRUCTURAL CEILING SIGNAL — smart money hedging long positions; consider reducing longs",
    },
    3: {
        "type":   "Type 3 — Squeeze Warning",
        "color":  "#9333EA",
        "badge_bg": "#FAF5FF",
        "detail": (
            "S3/4 is neutral (−15 to +15) AND the IV Smile is showing maximum "
            "compression (Sc08 — Coiled Spring / IV rank ≤20). The market is "
            "building energy for a move of unknown direction. Directional biases "
            "are unreliable here. Favour long-vol structures (straddles/strangles) "
            "but be mindful of theta decay — time the entry carefully."
        ),
        "warning": "SQUEEZE WARNING — breakout imminent; direction unknown; favour long vol",
    },
    4: {
        "type":   "Type 4 — Bear Trap",
        "color":  "#2563EB",
        "badge_bg": "#EFF6FF",
        "detail": (
            "S3/4 is negative (D or E band, score ≤−16) BUT the IV Smile is "
            "showing call buying or relief (Sc04, Sc05, Sc06). Sentiment is "
            "recovering even as the structure looks bearish — the hallmark of a "
            "bear trap. Shorts caught in this divergence face a rapid squeeze. "
            "Cover or reduce short exposure when this signal activates."
        ),
        "warning": "BEAR TRAP RISK — call buying despite bearish OI structure; cover shorts",
    },
    5: {
        "type":   "Type 5 — Pre-Move Setup",
        "color":  "#B45309",
        "badge_bg": "#FEF3C7",
        "detail": (
            "PCR is at an extreme level AND S3/4 is moderately biased AND the "
            "IV Smile is directionally aligned. This combination suggests smart "
            "money positioning ahead of a move. Watch for confirmation via "
            "intraday OI velocity and gamma flip proximity before acting."
        ),
        "warning": "PRE-MOVE SETUP — smart money positioning; wait for OI velocity / GEX confirmation",
    },
}


def detect_divergence_type(
    s34_score: float,
    scenario_id: int,
    pcr: float = 1.0,
) -> dict | None:
    """
    Returns a divergence dict or None if no divergence is active.

    Priority order: Type 1 > Type 2 > Type 4 > Type 3 > Type 5
    (most actionable first)
    """
    band         = get_s34_band(s34_score)
    smile_bucket = get_smile_bucket(scenario_id)

    # Type 1: Capitulation Bottom
    if band == "E" and scenario_id == 2:
        d = _DIVERGENCE_META[1].copy()
        d["divergence_id"] = 1
        return d

    # Type 2: Structural Ceiling
    if band == "A" and scenario_id in (1, 3):
        d = _DIVERGENCE_META[2].copy()
        d["divergence_id"] = 2
        return d

    # Type 4: Bear Trap
    if band in ("D", "E") and smile_bucket == "BULLISH_NEUTRAL":
        d = _DIVERGENCE_META[4].copy()
        d["divergence_id"] = 4
        return d

    # Type 3: Squeeze Warning
    if band == "C" and scenario_id == 8:
        d = _DIVERGENCE_META[3].copy()
        d["divergence_id"] = 3
        return d

    # Type 5: Pre-Move Setup
    # Extreme PCR (very bullish: <0.70 or very bearish: >1.55) + moderate bias + directional smile
    if (pcr < 0.70 or pcr > 1.55) and abs(s34_score) >= 20 and scenario_id in (1, 2, 3, 4, 5, 6):
        d = _DIVERGENCE_META[5].copy()
        d["divergence_id"] = 5
        return d

    return None


# ─────────────────────────────────────────────────────────────────────────────
# CONFIDENCE LABEL
# ─────────────────────────────────────────────────────────────────────────────

def _confidence_label(s34_score: float, smile_confidence: float, quadrant: str) -> tuple[str, str]:
    """
    Returns (label, color) for the overall combined confidence.
    Combined confidence uses smile confidence (from the classifier) + S3/4 score magnitude.
    Only Q1 and Q4 (both engines aligned) reach HIGH.
    """
    magnitude = abs(s34_score)

    if quadrant in ("Q1", "Q4"):
        if magnitude >= 51 and smile_confidence >= 75:
            return "HIGH", "#059669"
        elif magnitude >= 20 and smile_confidence >= 60:
            return "MODERATE-HIGH", "#16A34A"
        else:
            return "MODERATE", "#D97706"
    elif quadrant in ("Q2", "Q3"):
        return "MODERATE", "#D97706"
    else:
        return "LOW", "#6B7280"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def generate_combined_decision(
    s34: dict,
    smile: dict | None,
    m: dict,
) -> dict:
    """
    Master function.  Call with the three already-computed dicts.

    Returns:
    {
        quadrant:          str          "Q1" / "Q2" / "Q3" / "Q4" / "CN"
        quadrant_name:     str          e.g. "Full Bull Alignment"
        quadrant_short:    str          e.g. "Q1 — FULL BULL"
        quadrant_color:    str          hex colour
        badge_bg:          str          hex colour (background for badge)
        action:            str          one-liner trade action
        explanation_lines: list[str]    3-5 lines of rationale
        divergence:        dict | None  populated if a divergence type is active
        confidence_label:  str          "HIGH" / "MODERATE-HIGH" / "MODERATE" / "LOW"
        confidence_color:  str          hex colour
        s34_score:         float
        s34_direction:     str
        s34_band:          str
        smile_scenario:    str
        smile_bucket:      str
        smile_confidence:  float
        pcr:               float
        available:         bool         False if inputs were insufficient
    }
    """
    # Fallback if either engine not yet ready
    fallback_smile_id   = 0
    fallback_smile_name = "Indeterminate"
    fallback_smile_conf = 0.0

    s34_score     = float(s34.get("bias_score", 0))
    s34_direction = s34.get("direction", "NEUTRAL")
    s34_breakdown = s34.get("signal_breakdown", {})

    pcr = float(m.get("pcr", 1.0)) if m else 1.0

    if smile is None:
        scenario_id   = fallback_smile_id
        scenario_name = fallback_smile_name
        smile_conf    = fallback_smile_conf
    else:
        scenario_id   = int(smile.get("scenario_id", 0))
        scenario_name = smile.get("scenario_name", "Unknown")
        smile_conf    = float(smile.get("confidence", 0))

    smile_bucket = get_smile_bucket(scenario_id)
    quad_info    = classify_quadrant(s34_score, scenario_id)
    divergence   = detect_divergence_type(s34_score, scenario_id, pcr)
    conf_label, conf_color = _confidence_label(s34_score, smile_conf, quad_info["quadrant"])

    # ── Build explanation lines ───────────────────────────────────────────────
    lines: list[str] = []

    # Line 1: S3/4 summary
    band = quad_info["s34_band"]
    band_desc = {
        "A": "strong bull (+51 to +100)",
        "B": "mild bull (+16 to +50)",
        "C": "neutral (−15 to +15)",
        "D": "mild bear (−50 to −16)",
        "E": "strong bear (−100 to −51)",
    }
    lines.append(
        f"S3/4 Engine: score {s34_score:+.0f} → Band {band} ({band_desc.get(band, '')}) "
        f"— {s34_direction} structural bias."
    )

    # Line 2: IV Smile summary
    if smile is None:
        lines.append("IV Smile Engine: insufficient data — classification pending.")
    else:
        lines.append(
            f"IV Smile Engine: {scenario_name} (Sc{scenario_id:02d}) "
            f"→ {smile_bucket.replace('_', ' ')} bucket "
            f"[confidence {smile_conf:.0f}%]."
        )

    # Line 3: Quadrant result
    lines.append(
        f"Combined Quadrant: {quad_info['short']}. {quad_info['description']}"
    )

    # Line 4: Signal bridge (S4 IV Skew)
    s4_val = s34_breakdown.get("S4 IV Skew", None)
    if s4_val is not None:
        s4_sign = "put-skew detected" if s4_val < 0 else ("call-skew / flat" if s4_val > 0 else "neutral")
        lines.append(
            f"S4 IV Skew (bridge signal): {s4_val:+.0f}/12 → {s4_sign}. "
            "This shared signal links both engines — use it to validate alignment."
        )

    # Line 5: Divergence note (if active)
    if divergence:
        lines.append(
            f"⚠ DIVERGENCE ACTIVE: {divergence['type']} — {divergence['warning']}"
        )

    available = True
    if smile is None:
        available = False   # partial — smile not ready yet

    return {
        "quadrant":          quad_info["quadrant"],
        "quadrant_name":     quad_info["name"],
        "quadrant_short":    quad_info["short"],
        "quadrant_color":    quad_info["color"],
        "badge_bg":          quad_info["badge_bg"],
        "action":            quad_info["action"],
        "explanation_lines": lines,
        "divergence":        divergence,
        "confidence_label":  conf_label,
        "confidence_color":  conf_color,
        "s34_score":         s34_score,
        "s34_direction":     s34_direction,
        "s34_band":          quad_info["s34_band"],
        "smile_scenario":    scenario_name,
        "smile_bucket":      smile_bucket,
        "smile_confidence":  smile_conf,
        "pcr":               pcr,
        "available":         available,
    }
