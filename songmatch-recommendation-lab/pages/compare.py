import re
import streamlit as st
from src.ui import (resources,hero,section,selector,database_path,participant_code,
                    study_phase,feedback_form)
from src.storage import create_session
from src.recommend import METHOD_NAMES

from src.ui import page_setup

page_setup()
engine,version=resources()
hero("THE BLIND LISTENING EXPERIMENT","Let your ears decide.",
     "Three methods. The same favorites. Listen to a shuffled mix without method labels, then tell us what you think.")
if "compare_completed" in st.session_state:
    completed=st.session_state.compare_completed
    st.success("Session submitted. Thank you—your feedback now counts in the experiment.")
    st.caption("A song shared by several methods receives the same rating for each method.")
    st.subheader("The methods, revealed")
    for method,result in completed["lists"].items():
        with st.expander(METHOD_NAMES[method]):
            for item in result.items:
                row=engine.catalog.iloc[engine.positions[item.song_id]]
                st.write(f"{item.rank}. {row.title} — {row.artist}")
    st.page_link("pages/results.py",label="Explore experiment results →")
    if st.button("Start another session"):
        st.session_state.pop("compare_completed",None)
        st.rerun()
    st.stop()

active=st.session_state.get("compare_active")
if active is None:
    section("01 / SET UP YOUR LISTEN","Choose your starting songs")
    st.caption("Plan for about 15–25 minutes. Up to 30 unique songs may appear; overlap is shown only once. Ratings are anonymous and saved when you submit.")
    with st.expander("Your anonymous participant code"):
        st.caption("Keep this randomly generated code for a second session. Do not enter your name or email.")
        code=st.text_input("Participant code",value=participant_code(),max_chars=32)
        st.session_state.participant_code=code
    selected=selector(engine,"compare_selection")
    st.caption(f"Study phase: {study_phase()}. Development seed: 42. Your selected songs will be excluded from every method.")
    consent=st.checkbox("I understand that my anonymous selections and ratings will be stored for this research comparison.")
    valid_code=bool(re.fullmatch(r"[a-f0-9]{12,32}",st.session_state.participant_code))
    if not valid_code:
        st.warning("Use the generated code, or a previous 12–32 character code containing only 0–9 and a–f.")
    if st.button("Start blind comparison",type="primary",disabled=not (3<=len(selected)<=5 and consent and valid_code),key="compare_generate"):
        with st.spinner("Preparing your shuffled listening set…"):
            lists=engine.compare(selected,42)
            session,order=create_session(database_path(),st.session_state.participant_code,selected,engine,lists,version,phase=study_phase())
        st.session_state.compare_active={"session_id":session,"order":order,"selected":selected.copy(),"lists":lists,"dataset":version}
        st.rerun()
else:
    if active["dataset"] != version:
        st.error("The dataset changed during this session. Start a new comparison.")
        if st.button("Discard draft and start again"):
            st.session_state.pop("compare_active",None)
            st.rerun()
        st.stop()
    section("02 / LISTEN & RATE",f"Your shuffled set · {len(active['order'])} unique songs",
            "Method labels, ranks, similarity scores, and explanations stay hidden until submission.")
    st.caption("Your starting songs: "+", ".join(engine.catalog.iloc[engine.positions[s]].title for s in active["selected"]))
    if len(active["order"])==0:
        st.warning("The catalog could not provide recommendations. Start a new session with another selection.")
    feedback_form(engine,active,"compare")
    with st.expander("Leave this session"):
        st.caption("Unsubmitted sessions do not count in the results. A browser refresh may lose this draft's controls.")
        if st.button("Discard draft and start again"):
            st.session_state.pop("compare_active",None)
            st.rerun()
