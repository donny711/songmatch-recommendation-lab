import streamlit as st
from src.ui import (resources,hero,section,selector,track_header,preview,feedback_form,
    comparison_chart,database_path,participant_code,study_phase)
from src.recommend import METHOD_NAMES
from src.explain import explain
from src.storage import create_session

from src.ui import page_setup

page_setup()
engine,version=resources()
hero("MUSIC DISCOVERY, WITH A QUESTION MARK","Find your next<br><span class='accent'>on-repeat.</span>",
     "Pick a few songs you love. Explore what their musical DNA leads to—and help us find out what makes a good recommendation.",record=True)
cols=st.columns(3)
cols[0].metric("Songs to explore",f"{len(engine.ids):,}")
cols[1].metric("Musical characteristics","5")
cols[2].metric("Ways to discover","3")
st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
section("01 / YOUR STARTING POINT","What’s already on repeat?","Choose 3–5 favorites. Search recognizable hits, or switch libraries for independent discoveries.")
selected=selector(engine,"discover_selection")
left,right=st.columns([2,1],vertical_alignment="bottom")
with left:
    method=st.selectbox("Recommendation method",list(METHOD_NAMES),format_func=METHOD_NAMES.get,index=2)
with right:
    generate=st.button("Find my next songs",type="primary",width="stretch",
                       disabled=not 3<=len(selected)<=5,icon=":material/arrow_forward:",key="discover_generate")
if generate:
    with st.spinner("Finding your next listen…"):
        result=engine.recommend(selected,method,42)
        session,order=create_session(database_path(),participant_code(),selected,engine,{method:result},version,
                                     mode="discover",phase=study_phase())
    st.session_state.discover_active={"session_id":session,"order":[r.song_id for r in result.items],
        "selected":selected.copy(),"lists":{method:result},"dataset":version}
    st.session_state.pop("discover_completed",None)
if "discover_completed" in st.session_state:
    st.success("Feedback saved. Discovery feedback is kept separate from the blinded experiment.")
active=st.session_state.get("discover_active")
if active:
    if active["dataset"]!=version:
        st.warning("The catalog changed. Generate a fresh list.")
        st.stop()
    method,result=next(iter(active["lists"].items()))
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    section("02 / FOLLOW THE SOUND","Your next ten listens",f"{METHOD_NAMES[method]} · {result.elapsed_ms:.1f} ms · maximum two songs per artist")
    if sorted(selected)!=sorted(active["selected"]):
        st.warning("Your selection has changed. These results use your previous selection; click Find my next songs to update them.")
    if result.warning:
        st.info(result.warning)
    for index in range(0,len(result.items),2):
        for col,item in zip(st.columns(2),result.items[index:index+2]):
            row=engine.catalog.iloc[engine.positions[item.song_id]]
            with col:
                with st.container(border=True):
                    track_header(row,item.rank)
                    st.write(explain(engine,active["selected"],item,method))
                    preview(row,f"discover_card_{active['session_id']}")
    if active["order"]:
        with st.expander("See how the musical characteristics compare",expanded=True):
            comparison_chart(engine,active["selected"],active["order"])
        with st.expander("Listen and leave feedback"):
            feedback_form(engine,active,"discover")
else:
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    section("HOW IT WORKS","A recommendation is a hypothesis.")
    cols=st.columns(3)
    for col,title,body in zip(cols,["01 · Pick your favorites","02 · Follow the features","03 · Put it to the test"],[
        "A handful of songs gives us a starting point for your taste.",
        "We compare tempo, energy, danceability, valence, and acousticness.",
        "Try the blind comparison to see what works for your ears."]):
        with col:
            with st.container(border=True):
                st.markdown("**"+title+"**")
                st.caption(body)
    st.page_link("pages/compare.py",label="Curious which method works best? Try the experiment →")
st.markdown('<div class="footer">Built for curiosity. Popular-song metadata plus independent FMA music. No Spotify connection or account required.</div>',unsafe_allow_html=True)
