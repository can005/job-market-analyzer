import streamlit as st

from core.schemas import AgentResult


def _stale_suffix(stale: bool) -> str:
    return " :orange-badge[stale]" if stale else ""


def _band_badge(band: str) -> str:
    color = "green" if band == "strong" else "orange"
    return f":{color}-badge[{band}]"


def _render_findings(findings: list[dict] | None, stale: bool) -> None:
    if findings is None:
        return
    st.subheader(f"Market findings{_stale_suffix(stale)}")
    if not findings:
        st.caption("No market findings.")
        return
    for f in findings:
        st.markdown(f"> {f['statement']}")
        st.caption(f["evidence"])


def _posting_title(raw_text: str, max_chars: int = 120) -> str:
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        title = " | ".join(parts[:2]) if len(parts) >= 2 else line
        return title if len(title) <= max_chars else title[: max_chars - 1] + "…"
    return "(no title)"


def _render_role_row(i: int, role: dict) -> None:
    hn_id = role["hn_id"]
    title = _posting_title(role["raw_text"])
    dims = (
        f"skills {role['skills_match']} · "
        f"seniority {role['seniority_match']:.1f} · "
        f"domain {role['domain_match']} · "
        f"logistics {role['logistics_match']}"
    )
    with st.container(border=True):
        st.markdown(f"**{i}. {title}**")
        st.caption(f"HN id: {hn_id}")
        st.markdown(f"{_band_badge(role['label'])} &nbsp; **{role['total']}**")
        st.caption(dims)
        if st.button("View", key=f"view_{hn_id}", use_container_width=True):
            st.session_state.selected_role = hn_id


def _render_detail_pane(scored: list[dict]) -> None:
    selected = st.session_state.get("selected_role")
    if selected is None:
        st.caption("Select a posting to view its full text.")
        return
    match = next((r for r in scored if r["hn_id"] == selected), None)
    if match is None:
        st.caption("Selected posting is no longer in the results.")
        return
    st.markdown(f"**{_posting_title(match['raw_text'])}**")
    st.caption(f"HN id: {match['hn_id']} · Band: {match['label']} · Total: {match['total']}")
    st.markdown(match["raw_text"])


def _render_roles_split(scored: list[dict] | None, stale: bool) -> None:
    if scored is None:
        return
    st.subheader(f"Roles — best fit first{_stale_suffix(stale)}")
    if not scored:
        st.caption("No matching roles found.")
        return
    left, right = st.columns([2, 3], gap="medium")
    with left:
        for i, role in enumerate(scored, start=1):
            _render_role_row(i, role)
    with right:
        with st.container(border=True):
            _render_detail_pane(scored)


def _render_trace(run_url: str | None) -> None:
    if not run_url:
        return
    st.caption(f"[view trace ↗]({run_url})")


def render_results(result: AgentResult, *, stale: bool = False) -> None:
    _render_findings(result.market_findings, stale)
    _render_roles_split(result.scored, stale)
    _render_trace(result.run_url)
