"""
_patch_app.py  —  Surgical patch: app-4.py → app_v5.py

Three precise insertions, zero deletions:
  1. Import line  — add `from combined_bias_engine import generate_combined_decision`
  2. Early smile call — after _s34_breakdown is assigned, call classify_iv_smile_scenario early
  3. Combined bias panel — insert render function + call after the existing S3/4 badge markdown block
"""

import pathlib, textwrap, sys

SRC = pathlib.Path("/sessions/vigilant-adoring-tesla/mnt/uploads/4faf244f-ae06-466d-99b2-cb95a7402e5d-1781664923977_app-4.py")
DST = pathlib.Path("/sessions/vigilant-adoring-tesla/mnt/outputs/app_v5.py")

text = SRC.read_text(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 1 — Add import after the last stdlib/third-party import block
# We anchor on the existing `import time` line.
# ─────────────────────────────────────────────────────────────────────────────
IMPORT_ANCHOR = "import os, json, time, warnings, threading\n"
IMPORT_INSERT = (
    "import os, json, time, warnings, threading\n"
    "from combined_bias_engine import generate_combined_decision  # Chapter 17 & 18\n"
)
assert IMPORT_ANCHOR in text, f"PATCH 1 anchor not found; searched for: {repr(IMPORT_ANCHOR)}"
text = text.replace(IMPORT_ANCHOR, IMPORT_INSERT, 1)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 2 — Early IV smile call right after _s34_breakdown is assigned
# Anchor: the line that assigns `_s34_breakdown`
# ─────────────────────────────────────────────────────────────────────────────
SMILE_ANCHOR = "_s34_breakdown = _s34_bias.get(\"signal_breakdown\", {})\n"
SMILE_INSERT = (
    "_s34_breakdown = _s34_bias.get(\"signal_breakdown\", {})\n"
    "\n"
    "# ── Early IV smile call for the Combined Bias panel (Chapter 17 & 18) ────\n"
    "# Uses df_band already loaded above; relies on smile session history if available.\n"
    "_early_smile_hist = st.session_state.get(\"iv_smile_history\", [])\n"
    "_early_df_band    = pd.DataFrame(payload[\"df_band\"]) if payload.get(\"df_band\") else None\n"
    "_early_smile      = classify_iv_smile_scenario(\n"
    "    _early_df_band, m, spot, _early_smile_hist\n"
    ") if _early_df_band is not None else None\n"
    "_combined_decision = generate_combined_decision(_s34_bias, _early_smile, m)\n"
    "# ── end early IV smile call ───────────────────────────────────────────────\n"
)
assert SMILE_ANCHOR in text, "PATCH 2 anchor not found"
text = text.replace(SMILE_ANCHOR, SMILE_INSERT, 1)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 3 — Inject combined bias panel + render function
# We anchor on the start of the Section 3&4 bias chart block so we insert
# BEFORE the chart (immediately after the existing S3/4 badge markdown call).
#
# Anchor: the distinctive line that starts the "if len(_bh_data) >= 2:" chart block
# ─────────────────────────────────────────────────────────────────────────────
PANEL_ANCHOR = "if len(_bh_data) >= 2:\n"

# We only want to replace the FIRST occurrence (which is the bias chart block)
assert text.count(PANEL_ANCHOR) >= 1, "PATCH 3 anchor not found"

PANEL_CODE = r'''
# ═════════════════════════════════════════════════════════════════════════════
# 🎯 COMBINED MARKET BIAS DECISION  (Chapter 17 & 18)
# Surgical addition — do not modify any code below this block
# ═════════════════════════════════════════════════════════════════════════════
def _render_combined_bias_panel(cd: dict) -> None:
    """
    Renders the top-of-dashboard Combined Bias Decision panel.
    cd = output of generate_combined_decision()
    """
    q        = cd["quadrant"]
    qcolor   = cd["quadrant_color"]
    qbg      = cd["badge_bg"]
    qshort   = cd["quadrant_short"]
    action   = cd["action"]
    conf_l   = cd["confidence_label"]
    conf_c   = cd["confidence_color"]
    lines    = cd["explanation_lines"]
    div      = cd["divergence"]
    s34_sc   = cd["s34_score"]
    s34_dir  = cd["s34_direction"]
    smile_sc = cd["smile_scenario"]
    pcr_val  = cd["pcr"]

    # Confidence chip colour variant
    conf_alpha = "33"   # semi-transparent background

    # Divergence section (only if active)
    div_html = ""
    if div:
        div_html = f"""
        <div style="
            background:{div['badge_bg']};
            border:1.5px solid {div['color']};
            border-radius:8px;
            padding:8px 14px;
            margin-top:10px;
        ">
          <span style="font-size:12px;font-weight:800;color:{div['color']};">
            ⚠ {div['type']}
          </span>
          <div style="font-size:11.5px;color:#374151;margin-top:4px;">
            {div['warning']}
          </div>
          <div style="font-size:11px;color:#6B7280;margin-top:3px;">
            {div['detail']}
          </div>
        </div>"""

    # Explanation lines HTML
    lines_html = "".join(
        f'<div style="font-size:11.5px;color:#374151;padding:2px 0;line-height:1.5;">'
        f'&#9656; {ln}</div>'
        for ln in lines
    )

    # Colour bar strip at left edge (mimics the manual's colour-coded quadrant strips)
    colour_bar = f"""<div style="
        position:absolute;left:0;top:0;bottom:0;width:5px;
        background:{qcolor};border-radius:10px 0 0 10px;
    "></div>"""

    st.markdown(f"""
<div style="
    background:{qbg};
    border:1.5px solid {qcolor};
    border-radius:10px;
    padding:12px 18px 12px 22px;
    margin-bottom:12px;
    position:relative;
">
  {colour_bar}
  <!-- Row 1: title + badges -->
  <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px;">
    <span style="font-size:15px;font-weight:900;color:#1A1A2E;">
      🎯 Combined Bias Decision
    </span>
    <span style="
        background:{qcolor};color:#fff;
        border-radius:6px;padding:3px 12px;
        font-size:13px;font-weight:800;letter-spacing:0.5px;
    ">{qshort}</span>
    <span style="
        background:{conf_c}{conf_alpha};color:{conf_c};
        border:1px solid {conf_c};
        border-radius:6px;padding:2px 9px;
        font-size:11px;font-weight:700;
    ">Confidence: {conf_l}</span>
  </div>
  <!-- Row 2: action line -->
  <div style="
      font-size:12.5px;font-weight:700;color:{qcolor};
      margin-bottom:8px;letter-spacing:0.2px;
  ">{action}</div>
  <!-- Row 3: explanation lines -->
  {lines_html}
  <!-- Row 4: mini metrics strip -->
  <div style="
      display:flex;gap:18px;flex-wrap:wrap;
      margin-top:8px;padding-top:8px;
      border-top:1px solid #E5E7EB;
      font-size:11px;color:#6B7280;
  ">
    <span>S3/4 Score: <strong style="color:{qcolor};">{s34_sc:+.0f}</strong> ({s34_dir})</span>
    <span>IV Smile: <strong style="color:#374151;">{smile_sc}</strong></span>
    <span>PCR: <strong style="color:#374151;">{pcr_val:.2f}</strong></span>
    <span style="margin-left:auto;font-size:10px;color:#9CA3AF;">
      Chapters 17 &amp; 18 · Combined Bias Engine
    </span>
  </div>
  {div_html}
</div>
""", unsafe_allow_html=True)

# ── Call the panel ────────────────────────────────────────────────────────────
_render_combined_bias_panel(_combined_decision)
# ═════════════════════════════════════════════════════════════════════════════
# END COMBINED MARKET BIAS DECISION PANEL
# ═════════════════════════════════════════════════════════════════════════════

'''

text = text.replace(PANEL_ANCHOR, PANEL_CODE + PANEL_ANCHOR, 1)

DST.write_text(text, encoding="utf-8")
print(f"SUCCESS: wrote {DST}  ({len(text.splitlines())} lines)")
