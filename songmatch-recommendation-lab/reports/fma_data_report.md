# Historical FMA-only data report

## Source and redistribution

FMA: A Dataset for Music Analysis, Defferrard, Benzi, Vandergheynst and Bresson (ISMIR 2017).
Official source: https://github.com/mdeff/fma ; paper: https://arxiv.org/abs/1612.01840 .
Metadata and supplied numerical features are released as CC BY 4.0:
https://creativecommons.org/licenses/by/4.0/ . This permits redistribution with attribution and an indication of changes.
The bundled catalog is a cleaned and sampled derivative, not audio. Code is separately MIT licensed.
Audio retains each artist's original license, recorded in audio_license. Previews are fetched on demand from the official FMA archive; no audio is bundled.

## Inspection and cleaning

Source tracks: 106,574; Echo Nest rows: 13,129; joined IDs: 13,129.
Small/medium rows inspected: 5,281; complete, deduplicated rows: 5,242.
Final fixed catalog: 1,500 songs, 803 distinct artist identities.
Only small/medium tracks are used so that a 30-second listening excerpt exists in the official archives.
Drop blank ID/title/artist/top-level genre; coerce features to numbers; drop missing/nonfinite values, tempo <= 0, and unit-range values outside [0,1]. No feature is imputed or invented.
Dropped invalid/incomplete rows: 0; duplicate IDs: 0; normalized artist/title duplicates: 39.
Deduplication uses Unicode NFKC, case folding, and collapsed whitespace. Different spellings, live versions and remasters may remain; no audio fingerprinting is claimed.
Artist limits use the FMA artist ID, with a normalized-name fallback.
Genres use only FMA genre_top (one broad category per track); lowercase labels, no inferred or invented genres. Missing top-level labels are dropped; subgenres and multiple labels are deliberately excluded.
Uniform sampling without replacement uses pandas random_state=42 after stable sorting by song ID. Genre frequencies are not balanced.

### Missing cells before cleaning (small/medium join)

| Column | Missing |
|---|---:|
| song_id | 0 |
| title | 0 |
| artist | 0 |
| genre | 0 |
| tempo | 0 |
| energy | 0 |
| danceability | 0 |
| valence | 0 |
| acousticness | 0 |

### Features

| Feature | Interpretation | Valid source range | Observed catalog range |
|---|---|---|---|
| tempo | Estimated tempo in beats per minute | >0 BPM | 33.616–250.06 |
| energy | Estimated perceptual intensity/activity | 0–1 | 0.00195–0.99924 |
| danceability | Estimated suitability for dancing | 0–1 | 0.055596–0.96688 |
| valence | Estimated musical positivity, not a listener's emotion | 0–1 | 0.024188–0.99999 |
| acousticness | Estimated acoustic character/confidence | 0–1 | 9.575e-07–0.9958 |

These are historical Echo Nest estimates supplied with FMA, not measurements of listener preference. No API or Spotify account is used.
Min–max scaling fits only this fixed catalog; all five dimensions have equal weight. Constant dimensions become zero.

### Genre distribution

| Genre | Songs |
|---|---:|
| rock | 517 |
| electronic | 395 |
| hip-hop | 148 |
| folk | 129 |
| old-time / historic | 87 |
| pop | 72 |
| classical | 56 |
| jazz | 37 |
| international | 25 |
| instrumental | 19 |
| blues | 10 |
| experimental | 5 |

## Reproduction and limitations

Dataset version: fma-1500-3f0c74da405644d3.
Run python -m scripts.prepare_fma --raw data/raw. Exact source file SHA-256 hashes and all counts are in data/fma_manifest.json.
The official archive members are checked by ZIP CRC; the derived CSV has a content-hash version. Source file hashes are recorded for future verification.
Archive releases and fixed feature estimates are old. Genre ambiguity, musical feature bias and unfamiliar independent artists limit generalization.
The catalog favors tracks with both top-level genre labels and Echo Nest coverage, and is not representative of all music.
Remote previews require network access and upstream availability. If listening fails, use Not sure / couldn't assess; never guess a rating.
