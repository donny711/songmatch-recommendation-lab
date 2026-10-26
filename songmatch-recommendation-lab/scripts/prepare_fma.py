"""Fetch licensed metadata, inspect it, and create the fixed evaluation catalog."""
from pathlib import Path
import argparse
import hashlib
import json
import pandas as pd
from src.archive import read_member
from src.data import FEATURES, ROOT, clean_catalog, dataset_version

def prepare(raw, count=1500, seed=42):
    tracks = pd.read_csv(raw/"tracks.csv", header=[0,1], index_col=0, low_memory=False)
    echo = pd.read_csv(raw/"echonest.csv", header=[0,1,2], index_col=0)
    ids = tracks.index.intersection(echo.index)
    frame = pd.DataFrame(index=ids)
    for output, column in {
        "title": ("track","title"), "artist": ("artist","name"), "artist_id": ("artist","id"),
        "genre": ("track","genre_top"), "source_subset": ("set","subset"),
        "audio_license": ("track","license"),
    }.items():
        frame[output] = tracks.loc[ids, column]
    for feature in FEATURES:
        frame[feature] = echo.loc[ids, ("echonest","audio_features",feature)]
    frame["song_id"] = frame.index.astype(str)
    # All chosen tracks have a 30-second excerpt in an official small/medium archive.
    frame = frame[frame.source_subset.isin(["small","medium"])].copy()
    clean, report = clean_catalog(frame)
    if len(clean) < count:
        raise ValueError(f"Only {len(clean)} usable songs; cannot create requested {count}-song catalog.")
    sample = clean.sample(n=count, random_state=seed).sort_values("song_id", kind="stable")
    columns = ["song_id","title","artist","artist_id","genre",*FEATURES,"source_subset","audio_license"]
    path = ROOT/"data/fma_catalog.csv"
    sample[columns].to_csv(path, index=False, lineterminator="\n", float_format="%.10g")
    hashes = {name: hashlib.sha256((raw/name).read_bytes()).hexdigest() for name in ("tracks.csv","echonest.csv","genres.csv")}
    report.update({
        "tracks_source_rows": len(tracks), "echonest_source_rows": len(echo),
        "joined_rows": len(ids), "sample_rows": len(sample), "sample_seed": seed,
        "dataset_version": dataset_version(path), "source_sha256": hashes,
        "sample_genres": {str(k):int(v) for k,v in sample.genre.value_counts().items()},
        "sample_artists": int(sample.artist_key.nunique()),
        "feature_ranges": {f: [float(sample[f].min()),float(sample[f].max())] for f in FEATURES},
    })
    (ROOT/"data/fma_manifest.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    lines = [
        "# Data report", "",
        "## Source and redistribution", "",
        "FMA: A Dataset for Music Analysis, Defferrard, Benzi, Vandergheynst and Bresson (ISMIR 2017).",
        "Official source: https://github.com/mdeff/fma ; paper: https://arxiv.org/abs/1612.01840 .",
        "Metadata and supplied numerical features are released as CC BY 4.0:",
        "https://creativecommons.org/licenses/by/4.0/ . This permits redistribution with attribution and an indication of changes.",
        "The bundled catalog is a cleaned and sampled derivative, not audio. Code is separately MIT licensed.",
        "Audio retains each artist's original license, recorded in audio_license. Previews are fetched on demand from the official FMA archive; no audio is bundled.",
        "", "## Inspection and cleaning", "",
        f"Source tracks: {len(tracks):,}; Echo Nest rows: {len(echo):,}; joined IDs: {len(ids):,}.",
        f"Small/medium rows inspected: {report['input_rows']:,}; complete, deduplicated rows: {len(clean):,}.",
        f"Final fixed catalog: {len(sample):,} songs, {report['sample_artists']:,} distinct artist identities.",
        "Only small/medium tracks are used so that a 30-second listening excerpt exists in the official archives.",
        "Drop blank ID/title/artist/top-level genre; coerce features to numbers; drop missing/nonfinite values, tempo <= 0, and unit-range values outside [0,1]. No feature is imputed or invented.",
        f"Dropped invalid/incomplete rows: {report['invalid_or_incomplete_rows']}; duplicate IDs: {report['duplicate_ids']}; normalized artist/title duplicates: {report['duplicate_artist_title']}.",
        "Deduplication uses Unicode NFKC, case folding, and collapsed whitespace. Different spellings, live versions and remasters may remain; no audio fingerprinting is claimed.",
        "Artist limits use the FMA artist ID, with a normalized-name fallback.",
        "Genres use only FMA genre_top (one broad category per track); lowercase labels, no inferred or invented genres. Missing top-level labels are dropped; subgenres and multiple labels are deliberately excluded.",
        "Uniform sampling without replacement uses pandas random_state=42 after stable sorting by song ID. Genre frequencies are not balanced.",
        "", "### Missing cells before cleaning (small/medium join)", "",
        "| Column | Missing |", "|---|---:|",
    ]
    lines.extend(f"| {c} | {n} |" for c,n in report["missing_values"].items())
    lines += ["", "### Features", "", "| Feature | Interpretation | Valid source range | Observed catalog range |", "|---|---|---|---|"]
    definitions = {
        "tempo": ("Estimated tempo in beats per minute", ">0 BPM"),
        "energy": ("Estimated perceptual intensity/activity", "0–1"),
        "danceability": ("Estimated suitability for dancing", "0–1"),
        "valence": ("Estimated musical positivity, not a listener's emotion", "0–1"),
        "acousticness": ("Estimated acoustic character/confidence", "0–1"),
    }
    for feature in FEATURES:
        meaning, valid = definitions[feature]
        low, high = report["feature_ranges"][feature]
        lines.append(f"| {feature} | {meaning} | {valid} | {low:.5g}–{high:.5g} |")
    lines += ["", "These are historical Echo Nest estimates supplied with FMA, not measurements of listener preference. No API or Spotify account is used.",
              "Min–max scaling fits only this fixed catalog; all five dimensions have equal weight. Constant dimensions become zero.",
              "", "### Genre distribution", "", "| Genre | Songs |", "|---|---:|"]
    lines.extend(f"| {g} | {n} |" for g,n in report["sample_genres"].items())
    lines += ["", "## Reproduction and limitations", "",
              f"Dataset version: {report['dataset_version']}.",
              "Run python -m scripts.prepare_fma --raw data/raw. Exact source file SHA-256 hashes and all counts are in data/fma_manifest.json.",
              "The official archive members are checked by ZIP CRC; the derived CSV has a content-hash version. Source file hashes are recorded for future verification.",
              "Archive releases and fixed feature estimates are old. Genre ambiguity, musical feature bias and unfamiliar independent artists limit generalization.",
              "The catalog favors tracks with both top-level genre labels and Echo Nest coverage, and is not representative of all music.",
              "Remote previews require network access and upstream availability. If listening fails, use Not sure / couldn't assess; never guess a rating."]
    (ROOT/"reports").mkdir(exist_ok=True)
    (ROOT/"reports/fma_data_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw",type=Path,default=ROOT/"data/raw")
    parser.add_argument("--download",action="store_true")
    args=parser.parse_args()
    if args.download:
        args.raw.mkdir(parents=True,exist_ok=True)
        for name in ("tracks.csv","echonest.csv","genres.csv"):
            print("Fetching "+name,flush=True)
            (args.raw/name).write_bytes(read_member("fma_metadata","fma_metadata/"+name))
    prepare(args.raw)

if __name__ == "__main__":
    main()
