"""Atomic anonymous sessions; one rating per session/song, many method attributions."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
from uuid import uuid4
from .data import ROOT, FEATURES
from .recommend import ALGORITHM_VERSION, METHODS, blinded_order
from .explain import explain

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
 session_id TEXT PRIMARY KEY, participant_id TEXT NOT NULL,
 selected_songs TEXT NOT NULL, created_at TEXT NOT NULL, completed_at TEXT,
 dataset_version TEXT NOT NULL, algorithm_version TEXT NOT NULL,
 random_seed INTEGER NOT NULL, mode TEXT NOT NULL CHECK(mode IN ('compare','discover')),
 phase TEXT NOT NULL CHECK(phase IN ('pilot','final')),
 config TEXT NOT NULL, display_order TEXT NOT NULL, method_metadata TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recommendations (
 session_id TEXT NOT NULL REFERENCES sessions(session_id), method TEXT NOT NULL,
 song_id TEXT NOT NULL, rank INTEGER NOT NULL CHECK(rank>0), similarity_score REAL,
 fallback INTEGER NOT NULL CHECK(fallback IN (0,1)),
 title TEXT NOT NULL, artist TEXT NOT NULL, artist_key TEXT NOT NULL, genre TEXT NOT NULL,
 explanation TEXT NOT NULL,
 PRIMARY KEY(session_id,method,song_id), UNIQUE(session_id,method,rank)
);
CREATE TABLE IF NOT EXISTS ratings (
 session_id TEXT NOT NULL REFERENCES sessions(session_id), song_id TEXT NOT NULL,
 rating TEXT NOT NULL CHECK(rating IN ('like','dislike','unassessed')),
 knew_song INTEGER NOT NULL CHECK(knew_song IN (0,1)),
 listened INTEGER NOT NULL CHECK(listened IN (0,1)),
 PRIMARY KEY(session_id,song_id)
);
CREATE INDEX IF NOT EXISTS rec_session_song ON recommendations(session_id,song_id);
"""

@contextmanager
def connection(path):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    db = sqlite3.connect(path,timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    try:
        with db:
            yield db
    finally:
        db.close()

def initialize(path):
    with connection(path) as db:
        db.executescript(SCHEMA)

def create_session(path, participant_id, selected, engine, lists, dataset_version,
                   seed=42, mode="compare", phase="pilot"):
    if not re.fullmatch(r"[a-f0-9]{12,32}",participant_id):
        raise ValueError("Participant code must contain 12–32 lowercase hexadecimal characters.")
    selected = engine.validate_selection(selected)
    if mode not in ("compare","discover") or phase not in ("pilot","final"):
        raise ValueError("Invalid experiment mode or phase.")
    if mode == "compare" and set(lists) != set(METHODS):
        raise ValueError("A comparison must include all three methods.")
    for method,result in lists.items():
        if method not in METHODS or result.method != method:
            raise ValueError("Mismatched method.")
        ids = [r.song_id for r in result.items]
        if len(ids) != len(set(ids)) or set(ids).intersection(selected):
            raise ValueError("Duplicate or selected songs in recommendations.")
    initialize(path)
    session_id = uuid4().hex
    order = blinded_order(lists, seed)
    config = {"count": engine.count, "artist_limit": engine.artist_limit, "features": list(FEATURES),
              "weights": "equal", "scaling": "minmax", "similarity": "cosine"}
    metadata = {method: {"elapsed_ms": result.elapsed_ms, "warning": result.warning,
                        "fallback_count": sum(r.fallback for r in result.items)} for method,result in lists.items()}
    with connection(path) as db:
        db.execute("INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(
            session_id,participant_id,json.dumps(selected),datetime.now(timezone.utc).isoformat(),None,
            dataset_version,ALGORITHM_VERSION,int(seed),mode,phase,json.dumps(config),json.dumps(order),json.dumps(metadata)))
        for method,result in lists.items():
            for item in result.items:
                song = engine.catalog.iloc[engine.positions[item.song_id]]
                db.execute("INSERT INTO recommendations VALUES (?,?,?,?,?,?,?,?,?,?,?)",(
                    session_id,method,item.song_id,item.rank,item.score,int(item.fallback),
                    song.title,song.artist,song.artist_key,song.genre,explain(engine,selected,item,method)))
    return session_id,order

def submit_ratings(path, session_id, ratings):
    """Validate the full unique-song set and commit once. Invalid input writes nothing."""
    with connection(path) as db:
        session = db.execute("SELECT completed_at FROM sessions WHERE session_id=?",(session_id,)).fetchone()
        if session is None:
            raise ValueError("Unknown session.")
        if session["completed_at"]:
            raise ValueError("This session has already been submitted.")
        eligible = {r[0] for r in db.execute("SELECT DISTINCT song_id FROM recommendations WHERE session_id=?",(session_id,))}
        if not eligible:
            raise ValueError("An empty recommendation session cannot be completed.")
        if set(ratings) != eligible:
            raise ValueError("Rate every displayed song once; use Not sure when you cannot assess it.")
        for song_id,response in ratings.items():
            if response.get("rating") not in ("like","dislike","unassessed"):
                raise ValueError("Choose Like, Dislike, or Not sure for every song.")
            if type(response.get("knew_song")) is not bool or type(response.get("listened")) is not bool:
                raise ValueError("Answer the familiarity and listening questions.")
            if not response["knew_song"] and response["rating"] != "unassessed" and not response["listened"]:
                raise ValueError("Listen before rating an unfamiliar song, or choose Not sure.")
        for song_id,response in ratings.items():
            db.execute("INSERT INTO ratings VALUES (?,?,?,?,?)",(
                session_id,song_id,response["rating"],int(response["knew_song"]),int(response["listened"])))
        db.execute("UPDATE sessions SET completed_at=? WHERE session_id=?",
                   (datetime.now(timezone.utc).isoformat(),session_id))

def evaluation_rows(path, phase="pilot", dataset=None, algorithm=None):
    import pandas as pd
    initialize(path)
    query = """
      SELECT s.session_id,s.participant_id,s.dataset_version,s.algorithm_version,s.method_metadata,
             r.method,r.song_id,r.rank,r.artist_key,r.fallback,
             t.rating,t.knew_song,t.listened
      FROM sessions s JOIN recommendations r USING(session_id)
      LEFT JOIN ratings t ON t.session_id=r.session_id AND t.song_id=r.song_id
      WHERE s.completed_at IS NOT NULL AND s.mode='compare' AND s.phase=?
    """
    params = [phase]
    if dataset:
        query += " AND s.dataset_version=?"
        params.append(dataset)
    if algorithm:
        query += " AND s.algorithm_version=?"
        params.append(algorithm)
    with connection(path) as db:
        return pd.read_sql_query(query,db,params=params)

def completed_count(path):
    initialize(path)
    with connection(path) as db:
        return db.execute("SELECT COUNT(*) FROM sessions WHERE completed_at IS NOT NULL AND mode='compare'").fetchone()[0]
