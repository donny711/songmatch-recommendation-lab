"""Catalog validation shared by the importer, engine, CLI, and web app."""
from pathlib import Path
import hashlib
import re
import unicodedata
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ("tempo", "energy", "danceability", "valence", "acousticness")
CATALOG_PATH = ROOT / "data" / "catalog.csv"

def normalize(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value))).strip().casefold()

def clean_catalog(frame):
    required = ["song_id", "title", "artist", "genre", *FEATURES]
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError("Missing catalog columns: " + ", ".join(missing))
    df = frame.copy()
    report = {"input_rows": len(df), "missing_values": {c: int(df[c].isna().sum()) for c in required}}
    for column in ("song_id", "title", "artist", "genre"):
        df[column] = df[column].fillna("").astype(str).str.strip()
    df["genre"] = df["genre"].map(normalize)
    for column in FEATURES:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    valid = np.isfinite(df[list(FEATURES)].to_numpy(dtype=float)).all(axis=1)
    valid &= (df["tempo"] > 0).to_numpy()
    for column in FEATURES[1:]:
        valid &= df[column].between(0, 1).to_numpy()
    for column in ("song_id", "title", "artist", "genre"):
        valid &= df[column].ne("").to_numpy()
    report["invalid_or_incomplete_rows"] = int((~valid).sum())
    df = df.loc[valid].sort_values("song_id", kind="stable")
    before = len(df)
    df = df.drop_duplicates("song_id")
    report["duplicate_ids"] = before - len(df)
    df["recording_key"] = df["artist"].map(normalize) + " / " + df["title"].map(normalize)
    before = len(df)
    df = df.drop_duplicates("recording_key")
    report["duplicate_artist_title"] = before - len(df)
    if "artist_id" in df:
        identities = df["artist_id"].fillna("").astype(str).str.strip()
        df["artist_key"] = np.where(identities.ne(""), "id:" + identities, "name:" + df["artist"].map(normalize))
    else:
        df["artist_key"] = "name:" + df["artist"].map(normalize)
    df = df.reset_index(drop=True)
    report["usable_rows"] = len(df)
    report["genres"] = {str(k): int(v) for k, v in df["genre"].value_counts().items()}
    return df, report

def load_catalog(path=CATALOG_PATH):
    frame = pd.read_csv(path, dtype={"song_id": str, "artist_id": str})
    clean, report = clean_catalog(frame)
    if report["usable_rows"] != report["input_rows"]:
        raise ValueError("Catalog is not clean. Run python -m scripts.prepare_data.")
    if clean.empty:
        raise ValueError("Catalog contains no usable songs.")
    return clean

def catalog_for_scope(catalog, scope="popular"):
    if scope not in ("popular", "all"):
        raise ValueError("Unknown library scope.")
    if scope == "popular":
        if "catalog_source" not in catalog:
            raise ValueError("Popular-song source labels are missing. Rebuild the catalog.")
        return catalog.loc[catalog.catalog_source.eq("popular")].copy().reset_index(drop=True)
    return catalog.copy()

def dataset_version(path=CATALOG_PATH, scope="all"):
    if scope not in ("popular", "all"):
        raise ValueError("Unknown library scope.")
    return "songmatch-" + hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16] + "-" + scope
