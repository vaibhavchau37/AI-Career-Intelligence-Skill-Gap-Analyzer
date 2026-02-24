"""
Tracking & History  (Streamlit UI)

User Profile Saving : persists real scores from the live pipeline
Skill Growth Graph  : line chart built from saved snapshots

Call render_tracking_tab() from app.py inside the Tracking tab context.
All data shown here originates from the user's actual analysis runs —
no demo, sample, or dummy data is used anywhere in this module.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

try:
    from src.database.history_manager import (
        get_or_create_profile,
        get_all_profiles,
        delete_profile,
        save_score_snapshot,
        get_snapshots_for_profile,
        get_distinct_roles,
        delete_snapshot,
        clear_snapshots_for_profile,
        get_before_after,
        upsert_skill_status,
        get_skill_statuses,
    )
    _DB_OK = True
except Exception as _db_err:
    _DB_OK = False
    _DB_ERR = str(_db_err)


# ── tiny helpers ──────────────────────────────────────────────────────────────

def _fmt_dt(s: str) -> str:
    try:
        return datetime.fromisoformat(s).strftime("%d %b %Y  %H:%M")
    except Exception:
        return s


def _score_color(v: float) -> str:
    return "#28a745" if v >= 75 else "#ffc107" if v >= 50 else "#dc3545"


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


# ── public entry point ────────────────────────────────────────────────────────

def render_tracking_tab(
    analysis_results: Dict[str, Any],
    selected_role: Optional[str],
) -> None:
    """Render the Tracking & History tab."""
    if not _DB_OK:
        st.error(f"History database failed to load: {_DB_ERR}")
        return

    st.markdown("## 📈 Tracking & History")
    st.caption(
        "Every number shown here comes from your real analysis runs. "
        "Save a snapshot after completing Readiness Score to start tracking."
    )

    sub1, sub2 = st.tabs(["💾 Save & Profile", "📊 Skill Growth Graph"])

    with sub1:
        _step71(analysis_results, selected_role)
    with sub2:
        _step72()


# ─────────────────────────────────────────────────────────────────────────────

def _step71(analysis_results: Dict[str, Any], selected_role: Optional[str]) -> None:
    st.markdown("### 💾 Save Score Snapshot")
    st.caption("Your username is just a local label stored in `database.db` on this machine.")

    col_u, col_n = st.columns([1, 2])
    with col_u:
        username = st.text_input(
            "Username *",
            value=st.session_state.get("ph7_username", ""),
            placeholder="e.g. john_2025",
            key="ph7_username_input",
        )
    with col_n:
        full_name = st.text_input(
            "Full Name (optional)",
            value=st.session_state.get("ph7_fullname", ""),
            placeholder="e.g. John Doe",
            key="ph7_fullname_input",
        )

    if not username.strip():
        st.info("Enter a username above to enable saving.")
        return

    st.session_state["ph7_username"] = username.strip()
    st.session_state["ph7_fullname"] = full_name.strip()

    try:
        profile_id = get_or_create_profile(username.strip(), full_name.strip())
        st.session_state["ph7_profile_id"] = profile_id
    except Exception as e:
        st.error(f"Could not resolve profile: {e}")
        return

    st.success(f"Profile active → **{username.strip()}**")
    st.divider()

    # ── snapshot from live results ─────────────────────────────────────────────
    st.markdown("#### 📸 Save Current Analysis Result")

    score_results = analysis_results.get("readiness_score")
    skill_gaps    = analysis_results.get("skill_gaps", {})

    if not score_results:
        st.warning(
            "No readiness score available yet.  "
            "Complete **⭐ Readiness Score** (Tab 4) first, then return here to save."
        )
    else:
        overall   = _safe_float(score_results.get("overall_score"))
        breakdown = score_results.get("breakdown", {})
        sk_sc     = _safe_float(breakdown.get("skills"))
        exp_sc    = _safe_float(breakdown.get("experience"))
        proj_sc   = _safe_float(breakdown.get("projects"))

        matched = skill_gaps.get("matching_skills", [])
        missing = skill_gaps.get("missing_skills",  [])
        role    = selected_role or "Unknown Role"
        color   = _score_color(overall)

        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg,#1f77b4,#6610f2);
                        border-radius:12px;padding:20px;color:white;margin-bottom:12px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <div style="opacity:.8;font-size:.9rem;">Target Role</div>
                  <div style="font-size:1.3rem;font-weight:700;">{role}</div>
                </div>
                <div style="text-align:right;">
                  <div style="font-size:2.6rem;font-weight:700;color:{color};">
                    {overall:.1f}<span style="font-size:1rem;">/100</span>
                  </div>
                  <div style="opacity:.8;font-size:.85rem;">Overall Readiness Score</div>
                </div>
              </div>
              <hr style="border-color:rgba(255,255,255,.3);margin:10px 0;">
              <div style="display:flex;gap:24px;font-size:.9rem;flex-wrap:wrap;">
                <span>🧠 Skills: <b>{sk_sc:.1f}</b></span>
                <span>💼 Experience: <b>{exp_sc:.1f}</b></span>
                <span>🚀 Projects: <b>{proj_sc:.1f}</b></span>
                <span>✅ Matched: <b>{len(matched)}</b></span>
                <span>❌ Missing: <b>{len(missing)}</b></span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        notes = st.text_input(
            "Optional note for this snapshot",
            placeholder="e.g. After completing Docker course",
            key="ph7_notes",
        )

        if st.button("💾 Save Snapshot", type="primary", key="btn_ph7_save"):
            try:
                sid = save_score_snapshot(
                    profile_id=profile_id,
                    target_role=role,
                    overall_score=overall,
                    skills_score=sk_sc,
                    experience_score=exp_sc,
                    projects_score=proj_sc,
                    matched_skills=matched,
                    missing_skills=missing,
                    notes=notes,
                )
                # Persist skill acquisition data
                for s in matched:
                    upsert_skill_status(profile_id, s, "acquired")
                for s in missing:
                    upsert_skill_status(profile_id, s, "missing")
                st.success(
                    f"✅ Snapshot #{sid} saved — "
                    f"{datetime.now().strftime('%d %b %Y %H:%M:%S')}"
                )
                st.balloons()
            except Exception as e:
                st.error(f"Save failed: {e}")

    st.divider()
    _history_section(profile_id)


def _history_section(profile_id: int) -> None:
    st.markdown("#### 🕐 Saved History")

    roles = get_distinct_roles(profile_id)
    if not roles:
        st.info("No snapshots saved yet. Complete an analysis and save a snapshot above.")
        return

    role_filter = st.selectbox(
        "Filter by role",
        options=["All roles"] + roles,
        key="ph7_role_filter",
    )

    snaps = (
        get_snapshots_for_profile(profile_id)
        if role_filter == "All roles"
        else get_snapshots_for_profile(profile_id, target_role=role_filter)
    )

    if not snaps:
        st.info("No snapshots match the selected filter.")
        return

    # Before vs After card
    if role_filter != "All roles" and len(snaps) >= 2:
        ba = get_before_after(profile_id, role_filter)
        delta = ba["delta"]
        first_s  = ba["first"]
        latest_s = ba["latest"]

        st.markdown("##### 📊 Before vs After")
        c1, c2, c3 = st.columns(3)
        c1.metric("First Score",  f"{first_s['overall_score']:.1f}/100",
                  help=f"Saved: {_fmt_dt(first_s['saved_at'])}")
        c2.metric("Latest Score", f"{latest_s['overall_score']:.1f}/100",
                  help=f"Saved: {_fmt_dt(latest_s['saved_at'])}")
        c3.metric("Improvement",  f"{'+' if delta>=0 else ''}{delta:.1f} pts")

        # Newly acquired skills
        first_missing  = set(first_s.get("missing_skills") or [])
        latest_matched = set(latest_s.get("matched_skills") or [])
        gained = sorted(first_missing & latest_matched)
        if gained:
            st.success(
                f"🎉 **{len(gained)} skill(s) acquired** since first snapshot: "
                + ", ".join(f"`{s}`" for s in gained[:12])
                + ("…" if len(gained) > 12 else "")
            )
        st.divider()

    st.markdown(f"**{len(snaps)} snapshot(s)** (newest first)")

    for snap in reversed(snaps):
        with st.expander(
            f"#{snap['id']}  ·  {snap['target_role']}  ·  "
            f"**{snap['overall_score']:.1f}/100**  ·  {_fmt_dt(snap['saved_at'])}"
        ):
            ca, cb, cc = st.columns(3)
            ca.metric("Skills",     f"{snap['skills_score']:.1f}")
            cb.metric("Experience", f"{snap['experience_score']:.1f}")
            cc.metric("Projects",   f"{snap['projects_score']:.1f}")

            cx, cy = st.columns(2)
            cx.metric("Matched Skills", snap["matched_count"])
            cy.metric("Missing Skills", snap["missing_count"])

            if snap.get("notes"):
                st.caption(f"📝 {snap['notes']}")

            if snap.get("matched_skills"):
                st.markdown(
                    "**Matched:** "
                    + " ".join(
                        f'<span style="background:#d4edda;border-radius:4px;'
                        f'padding:2px 6px;font-size:.85rem;">{s}</span>'
                        for s in (snap["matched_skills"] or [])[:15]
                    ),
                    unsafe_allow_html=True,
                )
            if snap.get("missing_skills"):
                st.markdown(
                    "**Missing:** "
                    + " ".join(
                        f'<span style="background:#f8d7da;border-radius:4px;'
                        f'padding:2px 6px;font-size:.85rem;">{s}</span>'
                        for s in (snap["missing_skills"] or [])[:15]
                    ),
                    unsafe_allow_html=True,
                )

            if st.button(f"🗑️ Delete #{snap['id']}", key=f"del_{snap['id']}"):
                delete_snapshot(snap["id"])
                st.rerun()

    st.divider()
    if st.button("🗑️ Clear ALL snapshots for this profile", key="ph7_clear_all"):
        n = clear_snapshots_for_profile(profile_id)
        st.warning(f"Deleted {n} snapshot(s).")
        st.rerun()


# ───────────────────────────────────────────────────────────────────────────────

def _step72() -> None:
    st.markdown("### 📈 Skill Growth Graph")
    st.caption(
        "Line chart of your overall readiness score over time. "
        "Data points appear only after you save real snapshots."
    )

    profiles = get_all_profiles()
    if not profiles:
        st.info(
            "No profiles found. Complete an analysis, then save a snapshot in "
            "**Save & Profile** to start tracking."
        )
        return

    options = {p["username"]: p["id"] for p in profiles}
    sel_user = st.selectbox("Profile", list(options.keys()), key="ph7_graph_user")
    pid = options[sel_user]

    roles = get_distinct_roles(pid)
    if not roles:
        st.info("No snapshots saved for this profile yet.")
        return

    sel_roles: List[str] = st.multiselect(
        "Roles to display on chart",
        options=roles,
        default=roles,
        key="ph7_graph_roles",
    )
    if not sel_roles:
        st.info("Select at least one role.")
        return

    _draw_chart(pid, sel_user, sel_roles)
    st.divider()
    _skill_status_panel(pid)


def _draw_chart(pid: int, username: str, sel_roles: List[str]) -> None:
    try:
        import plotly.graph_objects as go

        palette = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
            "#9467bd", "#8c564b", "#e377c2", "#bcbd22",
        ]
        fig = go.Figure()
        has_data = False

        for i, role in enumerate(sel_roles):
            snaps = get_snapshots_for_profile(pid, target_role=role)
            if not snaps:
                continue
            has_data = True
            xs    = [_fmt_dt(s["saved_at"])    for s in snaps]
            ys    = [s["overall_score"]         for s in snaps]
            notes = [s.get("notes") or ""       for s in snaps]
            ids   = [s["id"]                    for s in snaps]
            col   = palette[i % len(palette)]

            fig.add_trace(go.Scatter(
                x=xs, y=ys,
                mode="lines+markers",
                name=role[:45],
                line=dict(color=col, width=3),
                marker=dict(size=10, color=col, line=dict(width=2, color="white")),
                customdata=list(zip(ids, notes)),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Score: <b>%{y:.1f}/100</b><br>"
                    "Date: %{x}<br>"
                    "Note: %{customdata[1]}<br>"
                    "Snapshot #%{customdata[0]}"
                    "<extra></extra>"
                ),
            ))

        if not has_data:
            st.info("No snapshot data for the selected roles yet.")
            return

        fig.update_layout(
            title=dict(text=f"🚀 Skill Growth — {username}", font=dict(size=18)),
            xaxis=dict(title="Saved At", tickangle=-35),
            yaxis=dict(title="Overall Readiness Score (/100)", range=[0, 105]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            plot_bgcolor="#fafafa",
            paper_bgcolor="white",
            height=480,
            shapes=[
                dict(type="line", y0=75, y1=75, x0=0, x1=1, xref="paper",
                     line=dict(color="#28a745", width=1, dash="dot")),
                dict(type="line", y0=50, y1=50, x0=0, x1=1, xref="paper",
                     line=dict(color="#ffc107", width=1, dash="dot")),
            ],
            annotations=[
                dict(x=1, y=75, xref="paper", yref="y", text="75 – Good",
                     showarrow=False, font=dict(size=11, color="#28a745"), xanchor="right"),
                dict(x=1, y=50, xref="paper", yref="y", text="50 – Average",
                     showarrow=False, font=dict(size=11, color="#ffc107"), xanchor="right"),
            ],
        )
        # Force the standard json engine to avoid orjson circular-import issues
        try:
            import plotly.io as _pio
            _pio.json.config.default_engine = "json"
        except Exception:
            pass
        st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        # Fallback: st.line_chart (no plotly needed)
        try:
            import pandas as pd
        except ImportError:
            st.warning("Install plotly and pandas for charts: `pip install plotly pandas`")
            return

        frames = []
        for role in sel_roles:
            for s in get_snapshots_for_profile(pid, target_role=role):
                frames.append({"saved_at": _fmt_dt(s["saved_at"]), role: s["overall_score"]})
        if not frames:
            st.info("No data to display.")
            return
        import pandas as pd
        df = pd.DataFrame(frames).set_index("saved_at")
        st.line_chart(df)


def _skill_status_panel(pid: int) -> None:
    st.markdown("#### 🎯 Skill Acquisition Progress")

    statuses = get_skill_statuses(pid)
    if not statuses:
        st.info("Skill data will appear here after you save a snapshot.")
        return

    acquired = sum(1 for v in statuses.values() if v == "acquired")
    learning = sum(1 for v in statuses.values() if v == "learning")
    missing  = sum(1 for v in statuses.values() if v == "missing")
    total    = len(statuses)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tracked", total)
    c2.metric("✅ Acquired",    acquired)
    c3.metric("📚 Learning",   learning)
    c4.metric("❌ Missing",    missing)

    if total:
        pct = acquired / total * 100
        st.markdown(
            f"""
            <div style="margin:10px 0 4px;">
              <div style="display:flex;justify-content:space-between;font-size:.85rem;">
                <span>Skill Acquisition Progress</span>
                <span><b>{pct:.1f}%</b> acquired</span>
              </div>
              <div style="background:#e9ecef;border-radius:8px;height:18px;overflow:hidden;margin-top:4px;">
                <div style="background:#28a745;height:100%;width:{pct}%;border-radius:8px;"></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("✏️ Update a skill's status manually"):
        names = sorted(statuses.keys())
        skill = st.selectbox("Skill", names, key="ph7_skill_sel")
        cur   = statuses.get(skill, "missing")
        nw    = st.radio(
            "Status",
            ["missing", "learning", "acquired"],
            index=["missing", "learning", "acquired"].index(cur),
            horizontal=True,
            key="ph7_skill_radio",
        )
        if st.button("Update", key="ph7_skill_update"):
            upsert_skill_status(pid, skill, nw)
            st.success(f"Updated `{skill}` → **{nw}**")
            st.rerun()
