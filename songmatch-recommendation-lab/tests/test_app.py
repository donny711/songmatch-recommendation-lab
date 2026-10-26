"""Exercise real Streamlit pages and submission without a browser or network."""
from streamlit.testing.v1 import AppTest
from src.data import ROOT,load_catalog,catalog_for_scope
from src.storage import evaluation_rows

def start_app(monkeypatch,tmp_path):
    monkeypatch.setenv("SONGMATCH_DB_PATH",str(tmp_path/"app.db"))
    monkeypatch.setenv("SONGMATCH_PHASE","pilot")
    return AppTest.from_file(str(ROOT/"app.py"),default_timeout=30).run()

def test_discover_generates_real_results(monkeypatch,tmp_path):
    app=start_app(monkeypatch,tmp_path)
    assert not app.exception
    ids=catalog_for_scope(load_catalog(),"popular").song_id.tolist()[:3]
    app.multiselect[0].set_value(ids).run()
    app.button(key="discover_generate").click().run()
    assert not app.exception
    assert len(app.session_state["discover_active"]["order"])==10
    assert all(song.startswith("popular:") for song in app.session_state["discover_active"]["order"])
    assert not any(button.label=="Load 30-second preview" for button in app.button)
    assert len(app.get("plotly_chart"))==1

def test_blind_comparison_submit_and_results(monkeypatch,tmp_path):
    app=start_app(monkeypatch,tmp_path)
    app.switch_page("pages/compare.py").run()
    assert not app.exception
    ids=catalog_for_scope(load_catalog(),"popular").song_id.tolist()[:3]
    app.multiselect[0].set_value(ids)
    app.checkbox[0].check()
    app.run()
    app.button(key="compare_generate").click().run()
    assert not app.exception
    active=app.session_state["compare_active"]
    assert len(active["order"])==len(set(active["order"]))
    assert not any("The methods, revealed" in x.value for x in app.subheader)
    for radio in app.radio:
        if radio.label=="Your feedback":
            radio.set_value("Not sure / couldn’t assess")
        elif radio.label=="Did you already know this song?":
            radio.set_value("No")
    app.run()
    app.button(key="compare_submit").click().run()
    assert not app.exception
    assert any("Session submitted" in x.value for x in app.success)
    assert not evaluation_rows(tmp_path/"app.db").empty
    app.switch_page("pages/results.py").run()
    assert not app.exception
    assert app.metric[0].value=="1"
    assert len(app.get("plotly_chart"))==1

def test_empty_results_are_honest(monkeypatch,tmp_path):
    app=start_app(monkeypatch,tmp_path)
    app.switch_page("pages/results.py").run()
    assert not app.exception
    assert app.metric[0].value=="0"
    assert any("No completed sessions" in x.value for x in app.info)


def test_switching_library_updates_pool_and_resets_selection(monkeypatch,tmp_path):
    app=start_app(monkeypatch,tmp_path)
    assert app.metric[0].value=="500"
    ids=catalog_for_scope(load_catalog(),"popular").song_id.tolist()[:3]
    app.multiselect[0].set_value(ids).run()
    app.sidebar.selectbox(key="library_scope").set_value("all").run()
    assert not app.exception
    assert app.metric[0].value=="2,000"
    assert app.multiselect[0].value==[]
