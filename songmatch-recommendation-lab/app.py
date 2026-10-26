import streamlit as st

st.set_page_config(page_title="SongMatch · Recommendation Lab",page_icon="◉",layout="wide",initial_sidebar_state="expanded")
page = st.navigation([
    st.Page("pages/discover.py",title="Discover",icon=":material/explore:",default=True),
    st.Page("pages/compare.py",title="Compare methods",icon=":material/science:"),
    st.Page("pages/results.py",title="Results",icon=":material/bar_chart:"),
])
page.run()
