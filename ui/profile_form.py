import streamlit as st

from core.schemas import Profile, ProfileSkill


def _init_state() -> None:
    if "skills" not in st.session_state:
        st.session_state.skills = [{"skill": "", "years": 0}]


def _render_skill_rows() -> None:
    to_remove: list[int] = []

    header = st.columns([3, 1, 0.5])
    header[0].caption("Skill")
    header[1].caption("Years")

    for i, row in enumerate(st.session_state.skills):
        c1, c2, c3 = st.columns([3, 1, 0.5])
        row["skill"] = c1.text_input(
            "skill", value=row["skill"], key=f"sk_{i}", label_visibility="collapsed"
        )
        row["years"] = c2.number_input(
            "yrs",
            min_value=0,
            max_value=60,
            value=row["years"],
            key=f"yr_{i}",
            label_visibility="collapsed",
        )
        if c3.button("✕", key=f"rm_{i}"):
            to_remove.append(i)

    if to_remove:
        for i in reversed(to_remove):
            st.session_state.skills.pop(i)
        st.rerun()

    if st.button("+ Add skill"):
        st.session_state.skills.append({"skill": "", "years": 0})
        st.rerun()


def render_profile_form() -> Profile | None:
    _init_state()

    with st.sidebar:
        st.subheader("Your skills")
        _render_skill_rows()
        st.divider()
        domain = st.text_input(
            "Domain or industry",
            key="domain",
            placeholder="e.g. fintech / trading infrastructure",
        )
        logistics = st.text_input(
            "Work logistics",
            key="logistics",
            placeholder="e.g. remote, EU timezone",
        )
        st.caption("Edits apply to next run.")

    filled = [r for r in st.session_state.skills if r["skill"].strip()]
    if not filled or not domain.strip() or not logistics.strip():
        return None

    return Profile(
        skills=[ProfileSkill(skill=r["skill"].strip(), years=r["years"]) for r in filled],
        domain=domain.strip(),
        logistics=logistics.strip(),
    )
