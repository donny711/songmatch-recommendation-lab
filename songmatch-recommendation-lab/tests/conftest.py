import pandas as pd
import pytest
from src.recommend import Recommender

@pytest.fixture
def catalog():
    return pd.DataFrame([
        {"song_id": str(i), "title": f"Track {i}", "artist": f"Artist {i//3}",
         "genre": "rock" if i%3 else "jazz", "tempo": 60+i*3,
         "energy": (i%10)/10, "danceability": ((i*3)%11)/11,
         "valence": ((i*7)%13)/13, "acousticness": ((i*5)%17)/17}
        for i in range(40)
    ])

@pytest.fixture
def engine(catalog):
    return Recommender(catalog)
