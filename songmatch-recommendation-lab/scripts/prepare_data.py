"""Build a fixed mixed catalog from licensed popular-song metadata and FMA."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile
import pandas as pd
from src.data import FEATURES, ROOT, clean_catalog, dataset_version, normalize

POPULAR_REF = "iamsumat/spotify-top-2000s-mega-dataset"
POPULAR_VERSION = 5
POPULAR_URL = "https://www.kaggle.com/datasets/" + POPULAR_REF
POPULAR_DOWNLOAD = "https://www.kaggle.com/api/v1/datasets/download/" + POPULAR_REF + "?datasetVersionNumber=5"
POPULAR_SHA256 = "0ee00d80e061775461de6f1642b59e7b9293c5f8899c5575b745a9050e5c3888"

def broad_genre(value):
    genre = normalize(value)
    # Conservative, documented token groups; retain unfamiliar labels verbatim.
    if "hip hop" in genre or "rap" in genre:
        return "hip-hop"
    if any(token in genre for token in ("rock", "metal", "punk")):
        return "rock"
    if "pop" in genre or genre == "boy band":
        return "pop"
    if any(token in genre for token in ("electro", "dance", "house", "trance", "ambient")) or genre in ("edm", "big beat", "big room", "gabba", "happy hardcore"):
        return "electronic"
    if "folk" in genre or "singer-songwriter" in genre:
        return "folk"
    for label in ("jazz", "blues", "country", "reggae", "soul", "funk"):
        if label in genre:
            return label
    return genre

def download_popular(path):
    with urllib.request.urlopen(POPULAR_DOWNLOAD, timeout=60) as response:
        data = response.read()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        content = archive.read("Spotify-2000.csv")
    if hashlib.sha256(content).hexdigest() != POPULAR_SHA256:
        raise ValueError("Popular dataset differs from the inspected version 5 CSV.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)

def prepare_popular(raw, count=500, artist_cap=12):
    expected = ["Index","Title","Artist","Top Genre","Year","Beats Per Minute (BPM)",
                "Energy","Danceability","Valence","Acousticness","Popularity"]
    missing = sorted(set(expected)-set(raw.columns))
    if missing:
        raise ValueError("Missing popular-song columns: " + ", ".join(missing))
    frame = pd.DataFrame(index=raw.index)
    frame["song_id"] = raw["Index"].map(lambda value: f"popular:{int(value)}" if pd.notna(value) else "")
    frame["title"], frame["artist"] = raw["Title"], raw["Artist"]
    frame["artist_id"] = ""
    frame["genre_raw"] = raw["Top Genre"]
    frame["genre"] = raw["Top Genre"].fillna("").map(broad_genre)
    frame["tempo"] = pd.to_numeric(raw["Beats Per Minute (BPM)"], errors="coerce")
    for output, source in (("energy","Energy"),("danceability","Danceability"),("valence","Valence"),("acousticness","Acousticness")):
        frame[output] = pd.to_numeric(raw[source], errors="coerce") / 100
    frame["popularity"] = pd.to_numeric(raw["Popularity"],errors="coerce")
    frame["year"] = raw["Year"]
    frame["catalog_source"] = "popular"
    frame["source_subset"] = ""
    frame["audio_license"] = "Audio rights belong to the recording's rights holders; no audio is bundled."
    cleaned, report = clean_catalog(frame)
    # Historical popularity only selects this fixed corpus; it is never a ranking feature.
    ranked = cleaned.sort_values(["popularity","song_id"],ascending=[False,True],kind="stable",na_position="last")
    anchor_artists = ("Taylor Swift", "Dua Lipa")
    anchors = ranked[ranked.artist.isin(anchor_artists)].drop_duplicates("artist_key")
    ranked = pd.concat([anchors,ranked[~ranked.song_id.isin(anchors.song_id)]],ignore_index=True)
    diverse = ranked[ranked.groupby("artist_key").cumcount() < artist_cap]
    selected = diverse.head(count).copy()
    if len(selected) < count:
        raise ValueError(f"Only {len(selected)} popular songs available under the catalog artist limit.")
    report.update({
        "source_missing_values": {column:int(raw[column].isna().sum()) for column in expected},
        "selected_rows": len(selected), "catalog_artist_cap": artist_cap, "anchor_artists": anchors.artist.tolist(),
        "selected_artists": int(selected.artist_key.nunique()),
        "popularity_range": [float(selected.popularity.min()),float(selected.popularity.max())],
        "selected_genres": {str(k):int(v) for k,v in selected.genre.value_counts().items()},
    })
    return selected, report

def prepare(fma_path, popular_path, count=500):
    content = popular_path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != POPULAR_SHA256:
        raise ValueError("Use the documented version 5 popular CSV; its SHA-256 does not match.")
    popular, popular_report = prepare_popular(pd.read_csv(popular_path),count=count)
    fma = pd.read_csv(fma_path,dtype={"song_id":str,"artist_id":str})
    fma["catalog_source"] = "fma"
    fma["genre_raw"] = fma["genre"]
    fma["popularity"] = 0
    fma["year"] = pd.NA
    combined, report = clean_catalog(pd.concat([fma,popular],ignore_index=True))
    columns = ["song_id","title","artist","artist_id","genre",*FEATURES,"catalog_source",
               "genre_raw","popularity","year","source_subset","audio_license"]
    path = ROOT/"data/catalog.csv"
    combined[columns].to_csv(path,index=False,lineterminator="\n",float_format="%.10g")
    report.update({
        "dataset_version": dataset_version(path),
        "scope_versions": {scope:dataset_version(path,scope=scope) for scope in ("popular","all")},
        "source_counts": {str(k):int(v) for k,v in combined.catalog_source.value_counts().items()},
        "artists": int(combined.artist_key.nunique()),
        "popular": popular_report,
        "sources": {
            "popular": {"publisher":"Sumit (iamsumat)","url":POPULAR_URL,"version":POPULAR_VERSION,
                        "license":"CC0: Public Domain (publisher declaration)",
                        "license_url":"https://creativecommons.org/publicdomain/zero/1.0/",
                        "raw_sha256":digest,"raw_filename":"Spotify-2000.csv"},
            "fma": {"url":"https://github.com/mdeff/fma","license":"CC BY 4.0",
                    "base_sha256":hashlib.sha256(fma_path.read_bytes()).hexdigest()},
        },
        "feature_ranges": {f:[float(combined[f].min()),float(combined[f].max())] for f in FEATURES},
    })
    (ROOT/"data/manifest.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    definitions = {
        "tempo": ("Estimated beats per minute", ">0 BPM"),
        "energy": ("Estimated intensity/activity", "0–1"),
        "danceability": ("Estimated suitability for dancing", "0–1"),
        "valence": ("Estimated musical positivity", "0–1"),
        "acousticness": ("Estimated acoustic character/confidence", "0–1"),
    }
    lines = [
        "# Data report", "",
        f"The full library contains **{len(combined):,} songs**: {len(popular):,} recognizable popular tracks plus {len(fma):,} independent FMA tracks.",
        "The app defaults to Popular hits (500 tracks); Full library includes both sources. All three methods use the same chosen library.",
        "", "## Popular-song source and redistribution", "",
        f"Sumit (iamsumat), Spotify – All Time Top 2000s Mega Dataset, version {POPULAR_VERSION}: {POPULAR_URL}",
        "The publisher labels this CSV CC0: Public Domain. License declaration checked through the official Kaggle dataset metadata API.",
        "CC0: https://creativecommons.org/publicdomain/zero/1.0/ . This concerns the published tabular dataset; it does not grant rights to recordings, artwork or lyrics.",
        "Only song metadata and supplied numerical estimates are bundled. No popular-song audio, lyrics or artwork is copied.",
        f"Raw CSV SHA-256: {digest}. The importer pins version 5 and checks this hash.",
        "The source describes recordings released from 1956–2019. Popularity is a historical snapshot, not a current chart or live popularity measure.",
        "", "## Inspection and cleaning", "",
        f"Popular source rows: {popular_report['input_rows']:,}; complete unique rows: {popular_report['usable_rows']:,}; selected: {len(popular):,}.",
        f"Invalid/incomplete rows dropped: {popular_report['invalid_or_incomplete_rows']}; duplicate IDs: {popular_report['duplicate_ids']}; duplicate artist/title recordings: {popular_report['duplicate_artist_title']}.",
        "Features come directly from the CSV. Tempo is BPM; Energy, Danceability, Valence and Acousticness are on 0–100 scales and are divided by 100 to match FMA's unit scale. No feature is fabricated or imputed.",
        "Blank metadata, nonfinite features, nonpositive tempo, or unit features outside [0,1] are dropped. Deduplicate IDs, then Unicode-NFKC/case-folded/whitespace-normalized artist/title pairs.",
        "The source Index column is namespaced as popular:<Index>. These are local dataset IDs, not Spotify recording IDs.",
        "Reserve one highest-popularity track each for Taylor Swift and Dua Lipa, then fill by historical popularity with at most 12 songs per normalized credited artist, taking 500 total. Ties use stable song ID order. This is catalog construction; recommendation lists still cap artists at two.",
        "FMA artists use source IDs; popular tracks use normalized credited artist names. Collaborations and differently spelled artist credits may remain separate.",
        "", "### Missing source values", "", "| Column | Missing |", "|---|---:|",
    ]
    lines.extend(f"| {column} | {n} |" for column,n in popular_report["source_missing_values"].items())
    lines += [
        "", "## Genre policy", "",
        "Original genre labels are retained in genre_raw. Genre matching uses a documented coarse grouping:",
        "- hip hop/rap → hip-hop; rock/metal/punk → rock; pop/boy band → pop.",
        "- electro/dance/house/trance/ambient and explicit EDM tags → electronic.",
        "- folk/singer-songwriter → folk; otherwise jazz/blues/country/reggae/soul/funk tokens map to that label.",
        "- Rules run in that order; other labels remain unchanged. These are approximate groupings, not new measurements.",
        "FMA retains its existing broad genre labels. Cross-source genre definitions and feature estimators are not perfectly comparable.",
        "", "## FMA source", "",
        "Defferrard, Benzi, Vandergheynst and Bresson, FMA: A Dataset for Music Analysis, ISMIR 2017.",
        "Source: https://github.com/mdeff/fma ; metadata/features CC BY 4.0: https://creativecommons.org/licenses/by/4.0/ .",
        "The unchanged 1,500-song base catalog is bundled as data/fma_catalog.csv. See reports/fma_data_report.md and data/fma_manifest.json for the original inspection, ranges and source-file hashes.",
        "", "## Numerical features", "", "| Feature | Meaning | Valid range | Full library observed |", "|---|---|---|---|",
    ]
    for feature in FEATURES:
        meaning, valid = definitions[feature]
        low, high = report["feature_ranges"][feature]
        lines.append(f"| {feature} | {meaning} | {valid} | {low:.6g}–{high:.6g} |")
    lines += [
        "", "All five features have equal weight; min–max scaling fits only the selected library. Popularity never enters the similarity vector.",
        "", "## Listening and experiment versions", "",
        "Popular tracks offer YouTube and Apple Music search links derived from their title/artist. These are search links, not verified direct recordings or a Spotify integration.",
        "Participants must find the correct recording and listen before rating unfamiliar tracks; if unavailable, use Not sure. FMA continues to offer its original 30-second excerpts with artist license attribution.",
        "Each session records a content-hash version plus library scope. Results never pool Popular hits and Full library sessions, or sessions from the previous FMA-only dataset.",
        "Existing feedback is preserved in SQLite; no old IDs or ratings are rewritten.",
        "", "## Limitations and reproduction", "",
        "Popularity-biased selection favors familiar older Western hits and may reduce novelty; this is not a representative or current mainstream catalog.",
        "Feature estimates, broad genres and duplicate detection are imperfect. Remasters/live versions and artist-name aliases may remain.",
        "Run python -m scripts.prepare_data --download, or use --popular-csv with the verified version 5 raw CSV. Rebuilding the optional FMA base from original metadata uses python -m scripts.prepare_fma --download.",
    ]
    (ROOT/"reports/data_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"songs":len(combined),"sources":report["source_counts"],"popular_artists":popular_report["selected_artists"],
                      "popular_cleaning":popular_report,"versions":report["scope_versions"]},indent=2))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--popular-csv",type=Path,default=ROOT/"data/raw/popular_songs.csv")
    parser.add_argument("--fma-csv",type=Path,default=ROOT/"data/fma_catalog.csv")
    parser.add_argument("--download",action="store_true")
    args = parser.parse_args()
    if args.download:
        download_popular(args.popular_csv)
    prepare(args.fma_csv,args.popular_csv)

if __name__ == "__main__":
    main()
