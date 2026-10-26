import streamlit as st
import plotly.express as px
from src.ui import resources,hero,database_path,study_phase
from src.storage import evaluation_rows
from src.theme import METHOD_COLORS, style_chart
from src.evaluate import session_metrics,aggregate_metrics
from src.recommend import ALGORITHM_VERSION,METHOD_NAMES

from src.ui import page_setup

page_setup()
engine,version=resources()
hero("EVIDENCE, BEFORE ASSUMPTIONS","What’s working?",
     "A transparent view of completed listening sessions. The question stays open until people have listened.")
phase=st.radio("Study phase",["pilot","final"],index=0 if study_phase()=="pilot" else 1,horizontal=True)
st.caption(f"Showing {phase} comparisons for dataset {version} · algorithm {ALGORITHM_VERSION}. Discovery feedback and unfinished sessions are excluded.")
rows=evaluation_rows(database_path(),phase,version,ALGORITHM_VERSION)
sessions=session_metrics(rows)
summary=aggregate_metrics(sessions)
count=int(rows.session_id.nunique()) if not rows.empty else 0
participants=int(rows.participant_id.nunique()) if not rows.empty else 0
cols=st.columns(4)
cols[0].metric("Completed sessions",count)
cols[1].metric("Anonymous participants",participants)
cols[2].metric("Unique songs rated",len(rows[["session_id","song_id"]].drop_duplicates()) if not rows.empty else 0)
cols[3].metric("Study phase",phase.title())
if summary.empty:
    st.markdown("---")
    st.subheader("The next discovery starts with a listener.")
    st.info("No completed sessions in this phase yet. Once participants submit the blind comparison, measured results will appear here.")
    st.page_link("pages/compare.py",label="Take part in the first comparison →")
else:
    chart=summary.copy()
    chart["Method"]=chart.method.map(METHOD_NAMES)
    chart["Positive ratings / assessed"]=chart.positive_rate_assessed*100
    st.subheader("Which method led to more likes?")
    fig=px.bar(chart,x="Method",y="Positive ratings / assessed",color="Method",
        color_discrete_map=METHOD_COLORS,
        hover_data=["liked","assessed","unassessed"])
    fig.update_layout(yaxis_range=[0,100],showlegend=False,height=320,margin=dict(l=0,r=0,t=10,b=0),
                      paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    style_chart(fig)
    st.plotly_chart(fig,width="stretch")
    st.caption("Positive-rating rate = likes ÷ assessed recommendations. Not sure and missing ratings are unassessed and excluded from this denominator.")
    display=summary.rename(columns={"method":"Method","sessions":"Lists","liked":"Likes","assessed":"Assessed",
        "unassessed":"Unassessed","positive_rate_assessed":"Likes / assessed","precision_at_10":"Mean Precision@10",
        "fully_assessed_lists_of_10":"Fully assessed lists of 10","distinct_artists_per_list":"Artists / list",
        "unknown_liked":"Unknown songs liked","generation_ms":"Generation (ms)","fallback_count":"Genre fillers"})
    display["Method"]=display["Method"].map(METHOD_NAMES)
    st.dataframe(display.drop(columns=["recommended"]),hide_index=True,width="stretch",
        column_config={"Likes / assessed":st.column_config.NumberColumn(format="%.3f"),
            "Mean Precision@10":st.column_config.NumberColumn(format="%.3f"),
            "Artists / list":st.column_config.NumberColumn(format="%.1f"),
            "Generation (ms)":st.column_config.NumberColumn(format="%.2f")})
    st.subheader("Compare within the same sessions")
    paired=sessions.pivot(index="session_id",columns="method",values="positive_rate_assessed").rename(columns=METHOD_NAMES)
    st.dataframe(paired,width="stretch")
    st.caption("Rows share the same participant, input songs, catalog and seed. A dash means that method had no assessed recommendations.")
    with st.expander("How results vary between participants"):
        grouped=sessions.groupby(["participant_id","method"])[["liked","assessed","unknown_liked"]].sum().reset_index()
        grouped["Likes / assessed"]=grouped.liked/grouped.assessed.replace(0,float("nan"))
        grouped["method"]=grouped.method.map(METHOD_NAMES)
        st.dataframe(grouped,hide_index=True,width="stretch")
    st.download_button("Download per-session metrics",sessions.to_csv(index=False).encode(),"songmatch-session-metrics.csv","text/csv")
    st.download_button("Download method summary",summary.to_csv(index=False).encode(),"songmatch-method-summary.csv","text/csv")
with st.expander("How to read these metrics",expanded=True):
    st.markdown("""
- **Completed sessions:** submitted blind comparisons in the selected phase and current dataset/algorithm version.
- **Positive-rating rate:** total likes divided by total assessed recommendations (Like or Dislike), weighted by assessed count.
- **Precision@10:** likes divided by 10, only for lists of exactly ten with all ten assessed. The table averages only those lists and reports their count.
- **Unassessed:** Not sure / couldn’t assess, or a missing rating. These never count as dislikes.
- **Artists per list:** distinct FMA artist identities per method list, averaged across sessions.
- **Unknown songs liked:** liked recommendations marked as previously unknown. Shared songs count once for each method that recommended them.
- **Generation time:** mean milliseconds to rank, filter, and select a list, including explanation-independent engine work; excludes startup, database operations and audio downloads.
- **Genre fillers:** recommendations from outside the selected genres when matching candidates could not fill the list under the artist cap.

This is an exploratory, paired study. A few volunteers do not establish statistical significance. Keep pilot and final sessions separate, freeze the algorithm before final data collection, and collect fresh ratings after changes.
""")
