import json
import sqlite3
import pandas as pd
import pytest
from src.storage import create_session,submit_ratings,evaluation_rows,completed_count
from src.evaluate import session_metrics,aggregate_metrics
from src.recommend import Recommendation,RecommendationList,METHODS

def draft(tmp_path,engine,phase="pilot",mode="compare"):
    path=tmp_path/"feedback.db"
    shared={m:RecommendationList(m,[Recommendation("3",1),Recommendation("4",2)],1.5) for m in METHODS}
    session,order=create_session(path,"a"*12,["0","1","2"],engine,shared,"test-v1",mode=mode,phase=phase)
    return path,session,order

def feedback(order):
    return {song:{"rating":"like","knew_song":False,"listened":True} for song in order}

def test_one_rating_attributes_to_every_recommending_method(tmp_path,engine):
    path,session,order=draft(tmp_path,engine)
    submit_ratings(path,session,feedback(order))
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM ratings").fetchone()[0]==2
        assert db.execute("SELECT count(*) FROM recommendations").fetchone()[0]==6
    rows=evaluation_rows(path)
    metrics=aggregate_metrics(session_metrics(rows))
    assert len(metrics)==3
    assert metrics.liked.tolist()==[2,2,2]
    assert metrics.unknown_liked.tolist()==[2,2,2]
    assert metrics.precision_at_10.isna().all()

def test_unassessed_has_explicit_denominator(tmp_path,engine):
    path,session,order=draft(tmp_path,engine)
    ratings=feedback(order)
    ratings[order[0]]["rating"]="unassessed"
    submit_ratings(path,session,ratings)
    metric=aggregate_metrics(session_metrics(evaluation_rows(path)))
    assert (metric.unassessed==1).all()
    assert (metric.assessed==1).all()
    assert (metric.positive_rate_assessed==1).all()
    assert metric.precision_at_10.isna().all()

def test_no_assessed_ratings_returns_nan_not_zero(tmp_path,engine):
    path,session,order=draft(tmp_path,engine)
    ratings={s:{"rating":"unassessed","knew_song":False,"listened":False} for s in order}
    submit_ratings(path,session,ratings)
    metric=aggregate_metrics(session_metrics(evaluation_rows(path)))
    assert metric.positive_rate_assessed.isna().all()

def test_precision_only_for_fully_assessed_ten(tmp_path,engine):
    path=tmp_path/"feedback.db"
    results=engine.compare(["0","1","2"])
    session,order=create_session(path,"b"*12,["0","1","2"],engine,results,"test-v1")
    ratings=feedback(order)
    for song in order[::2]:
        ratings[song]["rating"]="dislike"
    submit_ratings(path,session,ratings)
    metric=session_metrics(evaluation_rows(path))
    assert (metric.precision_at_10==metric.liked/10).all()

def test_invalid_submission_is_atomic_and_retryable(tmp_path,engine):
    path,session,order=draft(tmp_path,engine)
    ratings=feedback(order)
    ratings[order[0]]["listened"]=False
    with pytest.raises(ValueError,match="Listen"):
        submit_ratings(path,session,ratings)
    assert completed_count(path)==0
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM ratings").fetchone()[0]==0
    submit_ratings(path,session,feedback(order))
    assert completed_count(path)==1
    with pytest.raises(ValueError,match="already"):
        submit_ratings(path,session,feedback(order))

def test_drafts_and_discovery_never_enter_experiment_results(tmp_path,engine):
    path,session,order=draft(tmp_path,engine)
    assert evaluation_rows(path).empty
    _,discover,order=draft(tmp_path,engine,mode="discover")
    submit_ratings(path,discover,feedback(order))
    assert evaluation_rows(path).empty

def test_pilot_and_final_and_versions_stay_separate(tmp_path,engine):
    path,session,order=draft(tmp_path,engine,phase="final")
    submit_ratings(path,session,feedback(order))
    assert evaluation_rows(path,"pilot").empty
    assert not evaluation_rows(path,"final",dataset="test-v1").empty
    assert evaluation_rows(path,"final",dataset="other").empty

def test_incomplete_and_extra_ratings_are_rejected(tmp_path,engine):
    path,session,order=draft(tmp_path,engine)
    with pytest.raises(ValueError,match="every"):
        submit_ratings(path,session,{})
    ratings=feedback(order)
    ratings["unrelated"]=ratings[order[0]]
    with pytest.raises(ValueError,match="every"):
        submit_ratings(path,session,ratings)
