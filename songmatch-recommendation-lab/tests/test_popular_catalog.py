from urllib.parse import urlparse,parse_qs
import pandas as pd
import pytest
from scripts.prepare_data import prepare_popular,broad_genre
from src.data import load_catalog,catalog_for_scope,dataset_version
from src.listening import listening_links
from src.recommend import Recommender,METHODS

def test_popular_source_features_are_converted_not_invented():
    raw=pd.DataFrame([
        {"Index":1,"Title":"First","Artist":"Example","Top Genre":"dance pop","Year":2014,
         "Beats Per Minute (BPM)":120,"Energy":80,"Danceability":70,"Valence":30,"Acousticness":5,"Popularity":90},
        {"Index":2,"Title":"Second","Artist":"Other","Top Genre":"album rock","Year":1990,
         "Beats Per Minute (BPM)":99,"Energy":25,"Danceability":15,"Valence":60,"Acousticness":90,"Popularity":80},
    ])
    songs,report=prepare_popular(raw,count=2)
    song=songs.loc[songs.song_id.eq("popular:1")].iloc[0]
    assert song.tempo==120
    assert song.energy==.8
    assert song.danceability==.7
    assert song.valence==.3
    assert song.acousticness==.05
    assert song.genre=="pop"
    assert song.genre_raw=="dance pop"

def test_popular_source_drops_invalid_values():
    raw=pd.DataFrame([
        {"Index":1,"Title":"Good","Artist":"Example","Top Genre":"pop","Year":2014,
         "Beats Per Minute (BPM)":120,"Energy":80,"Danceability":70,"Valence":30,"Acousticness":5,"Popularity":90},
        {"Index":2,"Title":"Bad","Artist":"Other","Top Genre":"pop","Year":2014,
         "Beats Per Minute (BPM)":120,"Energy":120,"Danceability":70,"Valence":30,"Acousticness":5,"Popularity":90},
    ])
    songs,report=prepare_popular(raw,count=1)
    assert songs.song_id.tolist()==["popular:1"]
    assert report["invalid_or_incomplete_rows"]==1

def test_recognizable_tracks_are_in_bundled_catalog():
    popular=catalog_for_scope(load_catalog(),"popular")
    assert len(popular)==500
    expected=[("Taylor Swift","Shake It Off"),("Billie Eilish","bad guy"),("Ed Sheeran","Shape of You"),("Eminem","Without Me")]
    for artist,title in expected:
        assert ((popular.artist==artist)&(popular.title==title)).any(),(artist,title)
    assert popular.artist_key.value_counts().max()<=12

@pytest.mark.parametrize("method",METHODS)
def test_popular_scope_recommendations_only_use_popular_songs(method):
    popular=catalog_for_scope(load_catalog(),"popular")
    engine=Recommender(popular)
    selected=engine.ids[:3]
    result=engine.recommend(selected,method)
    assert len(result.items)==10
    assert all(item.song_id.startswith("popular:") for item in result.items)
    assert not set(selected).intersection(item.song_id for item in result.items)

def test_scope_has_distinct_reproducible_version():
    assert dataset_version(scope="popular")!=dataset_version(scope="all")
    assert dataset_version(scope="popular")==dataset_version(scope="popular")
    assert len(catalog_for_scope(load_catalog(),"all"))==2000

def test_listening_links_are_searches_with_encoded_actual_metadata():
    links=listening_links("A & B #1","Artist + guest")
    assert set(links)=={"YouTube","Apple Music"}
    youtube=urlparse(links["YouTube"])
    assert youtube.netloc=="www.youtube.com"
    assert parse_qs(youtube.query)["search_query"]==["A & B #1 Artist + guest official audio"]
    assert not youtube.fragment

def test_documented_genre_groups_keep_unknown_labels():
    assert broad_genre("alternative hip hop")=="hip-hop"
    assert broad_genre("album rock")=="rock"
    assert broad_genre("dance pop")=="pop"
    assert broad_genre("electro house")=="electronic"
    assert broad_genre("adult standards")=="adult standards"
