from collections import Counter
import numpy as np
import pandas as pd
import pytest
from src.data import FEATURES, clean_catalog, load_catalog
from src.recommend import METHODS, Recommender, blinded_order
from src.explain import explain

@pytest.mark.parametrize("method",METHODS)
def test_excludes_selected_duplicates_and_respects_artist_cap(engine,method):
    selected = ["0","1","2"]
    items = engine.recommend(selected,method).items
    ids = [i.song_id for i in items]
    assert len(ids) == len(set(ids)) == 10
    assert not set(ids).intersection(selected)
    artists = [engine.catalog.iloc[engine.positions[i]].artist_key for i in ids]
    assert max(Counter(artists).values()) <= 2
    assert [i.rank for i in items] == list(range(1,11))

@pytest.mark.parametrize("method",METHODS)
def test_small_catalog_returns_fewer(catalog,method):
    engine = Recommender(catalog.iloc[:5])
    result = engine.recommend(["0","1","2"],method)
    assert len(result.items) == 2
    assert "Only 2" in result.warning

@pytest.mark.parametrize("selection",[[],["0"],["0","1"],["0","1","2","3","4","5"],["0","1","absent"]])
def test_invalid_inputs_fail_clearly(engine,selection):
    with pytest.raises(ValueError):
        engine.recommend(selection)

@pytest.mark.parametrize("method",["random","genre"])
def test_seed_reproducibility_and_selection_order(engine,method):
    a=engine.recommend(["0","1","2"],method,42).items
    b=engine.recommend(["2","0","1"],method,42).items
    assert a == b
    assert a != engine.recommend(["0","1","2"],method,43).items

def test_genre_fallback_records_only_fillers(catalog):
    catalog.loc[:2,"genre"]="rare"
    engine=Recommender(catalog)
    result=engine.recommend(["0","1","2"],"genre")
    assert len(result.items)==10
    assert all(i.fallback for i in result.items)
    assert "ran out" in explain(engine,["0","1","2"],result.items[0],"genre")

def test_genre_matches_are_ranked_before_fallback(catalog):
    catalog["genre"]="other"
    catalog.loc[:4,"genre"]="rare"
    engine=Recommender(catalog)
    result=engine.recommend(["0","1","2"],"genre")
    assert not any(i.fallback for i in result.items[:2])
    assert all(i.fallback for i in result.items[2:])

def test_deliberately_similar_track_outranks_different():
    rows=[]
    for i in range(5):
        values=[160,.9,.8,.7,.1] if i<4 else [60,.1,.1,.1,.9]
        rows.append(dict(song_id=str(i),title=str(i),artist=str(i),genre="rock",**dict(zip(FEATURES,values))))
    engine=Recommender(pd.DataFrame(rows))
    result=engine.recommend(["0","1","2"])
    assert result.items[0].song_id=="3"
    assert result.items[0].score > result.items[1].score

def test_zero_profile_and_zero_candidates_are_finite(catalog):
    for feature in FEATURES:
        catalog.loc[:2,feature] = 1 if feature=="tempo" else 0
    engine=Recommender(catalog)
    result=engine.recommend(["0","1","2"])
    assert "zero" in result.warning.lower()
    assert all(np.isfinite(r.score) and r.score==0 for r in result.items)
    assert "undefined" in explain(engine,["0","1","2"],result.items[0],"features")

def test_missing_invalid_and_duplicate_recordings_follow_policy(catalog):
    catalog.loc[3,"energy"]=np.nan
    catalog.loc[4,"title"]=None
    catalog.loc[5,"tempo"]=0
    catalog.loc[6,"acousticness"]=1.1
    duplicate=catalog.iloc[[7]].copy()
    duplicate["song_id"]="duplicate"
    duplicate["title"]="  TRACK   7 "
    clean,report=clean_catalog(pd.concat([catalog,duplicate],ignore_index=True))
    assert report["invalid_or_incomplete_rows"]==4
    assert report["duplicate_artist_title"]==1
    assert len(clean)==36
    assert not set(["3","4","5","6"]).intersection(clean.song_id)

def test_missing_feature_column_is_actionable(catalog):
    with pytest.raises(ValueError,match="Missing catalog columns"):
        Recommender(catalog.drop(columns=["energy"]))

def test_blind_order_is_unique_and_reproducible(engine):
    results=engine.compare(["0","1","2"])
    a=blinded_order(results,42)
    assert len(a)==len(set(a))
    assert a==blinded_order(results,42)
    assert set(a)=={r.song_id for batch in results.values() for r in batch.items}

def test_bundled_real_catalog_is_clean_and_sufficient():
    catalog=load_catalog()
    assert 500 <= len(catalog) <= 2000
    engine=Recommender(catalog)
    assert all(len(batch.items)==10 for batch in engine.compare(engine.ids[:3]).values())
