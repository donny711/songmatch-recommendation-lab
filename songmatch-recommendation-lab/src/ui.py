"""Shared presentation and feedback controls. No recommendation logic lives here."""
import html
import os
from pathlib import Path
from uuid import uuid4
import plotly.graph_objects as go
import streamlit as st
from .data import ROOT, load_catalog, dataset_version, catalog_for_scope
from .recommend import Recommender, ALGORITHM_VERSION, METHOD_NAMES
from .archive import load_preview
from .storage import submit_ratings
from .theme import PURPLE, FUCHSIA, style_chart
from .listening import listening_links

def database_path():
    return Path(os.environ.get("SONGMATCH_DB_PATH",str(ROOT/"data/feedback.db")))

def study_phase():
    phase = os.environ.get("SONGMATCH_PHASE","pilot")
    return phase if phase in ("pilot","final") else "pilot"

@st.cache_resource
def _resources(version, scope):
    return Recommender(catalog_for_scope(load_catalog(),scope))

def resources():
    try:
        scope=st.session_state.get("library_scope","popular")
        version=dataset_version(scope=scope)
        engine=_resources(version,scope)
        valid=set(engine.ids)
        for key in ("discover_selection","compare_selection"):
            if key in st.session_state and not set(st.session_state[key]) <= valid:
                st.session_state[key]=[song for song in st.session_state[key] if song in valid]
        return engine,version
    except (FileNotFoundError,ValueError) as error:
        st.error(f"Catalog unavailable: {error}")
        st.code("python -m scripts.prepare_data --download")
        st.stop()

def apply_style():
    css = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
    st.markdown("<style>" + css + "</style>", unsafe_allow_html=True)


def page_setup():
    apply_style()
    sidebar()

def _library_changed():
    for key in ("discover_selection","compare_selection","discover_active","discover_completed","compare_completed"):
        st.session_state.pop(key,None)

def sidebar():
    with st.sidebar:
        st.markdown('<div class="brand">songmatch<span>°</span></div><div class="side-sub">RECOMMENDATION LAB</div>',unsafe_allow_html=True)
        st.markdown("---")
        st.caption("A small experiment in finding your next favorite song.")
        st.selectbox("Library",["popular","all"],
            format_func={"popular":"Popular hits","all":"Full library · hits + independent"}.get,
            key="library_scope",on_change=_library_changed,
            disabled="compare_active" in st.session_state,
            help="The same library is used for selection and all three recommendation methods. Switching resets discovery selections; finish or discard an active comparison first.")
        st.caption("Familiar favorites from Taylor Swift, Adele, Eminem, Queen and more. Switch to the full library for independent discoveries too.")
        st.markdown("---")
        st.markdown("**The research question**")
        st.caption("Do musical characteristics lead to better discoveries than genre matching or chance?")
        st.markdown(f'<span class="tag">{study_phase().upper()} STUDY</span>',unsafe_allow_html=True)
        st.caption("3–5 favorites · 10 recommendations\n\nEqual features · 2 tracks per artist")
        st.markdown("---")
        st.caption("Independent from the SongMatch mobile app. No account needed.")

def hero(eyebrow,title,description,record=False):
    st.markdown(f'<div class="eyebrow">{html.escape(eyebrow)}</div>',unsafe_allow_html=True)
    if record:
        st.markdown(f'<div class="hero"><div><h1>{title}</h1><p>{html.escape(description)}</p></div><div class="record-wrap" aria-hidden="true"><div class="record"></div></div></div>',unsafe_allow_html=True)
    else:
        st.title(title)
        st.write(description)

def section(number,title,caption=None):
    st.markdown(f'<div class="step">{number}</div>',unsafe_allow_html=True)
    st.subheader(title)
    if caption:
        st.caption(caption)

def selector(engine,key):
    labels={r.song_id:f"{r.title} — {r.artist} · {r.genre}" for r in engine.catalog.itertuples()}
    display=engine.catalog.sort_values(["popularity","title"],ascending=[False,True],kind="stable")
    selected=st.multiselect("Search songs or artists",options=display.song_id.tolist(),format_func=labels.get,
        max_selections=5,key=key,placeholder="Start typing a song title or artist…",
        help=f"Choose 3–5 songs you like from this {len(engine.ids):,}-song library. Try Taylor Swift, Adele, Ed Sheeran, Eminem or Queen.")
    st.caption(f"{len(selected)} of 3–5 favorites selected · Search by song, artist, or genre")
    if selected:
        cols=st.columns(min(len(selected),3))
        for i,song_id in enumerate(selected):
            row=engine.catalog.iloc[engine.positions[song_id]]
            with cols[i%len(cols)]:
                with st.container(border=True):
                    track_header(row)
                    with st.expander("Listen to this selection"):
                        preview(row,f"{key}_selected")
    return selected

def track_header(row,number=None):
    badge=f"{number:02d}" if number is not None else "♪"
    st.markdown(f'<div class="track-head"><div class="disc">{badge}</div><div><div class="track-title">{html.escape(str(row.title))}</div><div class="track-artist">{html.escape(str(row.artist))}</div></div></div><span class="tag">{html.escape(str(row.genre).upper())}</span>',unsafe_allow_html=True)

@st.cache_data(show_spinner=False,max_entries=64)
def _preview(song_id,subset):
    return load_preview(song_id,subset)

def preview(row,namespace):
    if row.get("catalog_source") == "popular":
        links=listening_links(str(row.title),str(row.artist))
        cols=st.columns(2)
        for col,(label,url) in zip(cols,links.items()):
            with col:
                st.link_button("Find on "+label,url,key=f"listen_{namespace}_{row.song_id}_{label}",width="stretch")
        st.caption("Find the correct recording, listen, then return to rate it. If you cannot assess it, choose Not sure.")
        return
    key=f"audio_{namespace}_{row.song_id}"
    if key in st.session_state:
        st.audio(st.session_state[key],format="audio/mpeg")
    elif st.button("Load 30-second preview",key=key+"_button",icon=":material/play_circle:"):
        try:
            with st.spinner("Getting the original FMA excerpt…"):
                data=_preview(str(row.song_id),str(row.source_subset))
            st.session_state[key]=data
            st.audio(data,format="audio/mpeg")
        except (OSError,ValueError,KeyError) as error:
            st.warning("Preview unavailable. Please choose Not sure if you cannot listen.")
    st.caption(f"FMA excerpt · {row.audio_license}")

def participant_code():
    if "participant_code" not in st.session_state:
        st.session_state.participant_code=uuid4().hex[:12]
    return st.session_state.participant_code

RATING_LABELS={"Like":"like","Dislike":"dislike","Not sure / couldn’t assess":"unassessed"}

def feedback_form(engine,active,namespace):
    order=active["order"]
    session_id=active["session_id"]
    if not order:
        st.info("There are no eligible recommendations. Choose another selection.")
        return
    st.info("Listen before rating unfamiliar songs. Each song appears once, even if several methods chose it. Use Not sure whenever you cannot assess a song.")
    responses={}
    chosen=0
    for i,song_id in enumerate(order):
        row=engine.catalog.iloc[engine.positions[song_id]]
        with st.container(border=True):
            track_header(row,i+1)
            preview(row,f"{namespace}_{session_id}")
            prefix=f"{session_id}_{song_id}"
            cols=st.columns([1.6,1])
            with cols[0]:
                rating=st.radio("Your feedback",list(RATING_LABELS),index=None,horizontal=True,key=prefix+"_rating")
            with cols[1]:
                knew=st.radio("Did you already know this song?",["Yes","No"],index=None,horizontal=True,key=prefix+"_known")
            listened=st.checkbox("I listened to this track before rating it",key=prefix+"_listened")
            chosen += int(rating is not None and knew is not None)
            responses[song_id]={"rating":RATING_LABELS.get(rating),"knew_song":None if knew is None else knew=="Yes","listened":listened}
    st.progress(chosen/len(order),text=f"{chosen} of {len(order)} songs have feedback and familiarity answers")
    ready=chosen==len(order)
    if st.button("Submit session",type="primary",key=namespace+"_submit",disabled=not ready,icon=":material/check:"):
        try:
            submit_ratings(database_path(),session_id,responses)
            st.session_state[namespace+"_completed"]=active
            st.session_state.pop(namespace+"_active",None)
            st.rerun()
        except ValueError as error:
            st.error(str(error))

def comparison_chart(engine,selected,ids):
    from .explain import profile_comparison
    labels={s:f"{engine.catalog.iloc[engine.positions[s]].title} — {engine.catalog.iloc[engine.positions[s]].artist}" for s in ids}
    song=st.selectbox("Track to inspect",ids,format_func=labels.get)
    data=profile_comparison(engine,selected,song)
    fig=go.Figure()
    for label,color in (("Your profile",PURPLE),("This track",FUCHSIA)):
        fig.add_trace(go.Bar(name=label,x=data.index,y=data[label],marker_color=color))
    fig.update_layout(height=285,barmode="group",margin=dict(l=0,r=0,t=10,b=0),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h",y=1.15),yaxis=dict(range=[0,1],title="Scaled feature value",gridcolor="rgba(167,139,250,0.14)"))
    style_chart(fig)
    st.plotly_chart(fig,width="stretch")
    st.caption("Min–max scaled within the catalog. Your profile is the average of your selected songs. Similarity is a geometric score, not a probability that you will like a song.")
