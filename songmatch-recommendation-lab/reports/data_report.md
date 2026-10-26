# Data report

The full library contains **2,000 songs**: 500 recognizable popular tracks plus 1,500 independent FMA tracks.
The app defaults to Popular hits (500 tracks); Full library includes both sources. All three methods use the same chosen library.

## Popular-song source and redistribution

Sumit (iamsumat), Spotify – All Time Top 2000s Mega Dataset, version 5: https://www.kaggle.com/datasets/iamsumat/spotify-top-2000s-mega-dataset
The publisher labels this CSV CC0: Public Domain. License declaration checked through the official Kaggle dataset metadata API.
CC0: https://creativecommons.org/publicdomain/zero/1.0/ . This concerns the published tabular dataset; it does not grant rights to recordings, artwork or lyrics.
Only song metadata and supplied numerical estimates are bundled. No popular-song audio, lyrics or artwork is copied.
Raw CSV SHA-256: 0ee00d80e061775461de6f1642b59e7b9293c5f8899c5575b745a9050e5c3888. The importer pins version 5 and checks this hash.
The source describes recordings released from 1956–2019. Popularity is a historical snapshot, not a current chart or live popularity measure.

## Inspection and cleaning

Popular source rows: 1,994; complete unique rows: 1,994; selected: 500.
Invalid/incomplete rows dropped: 0; duplicate IDs: 0; duplicate artist/title recordings: 0.
Features come directly from the CSV. Tempo is BPM; Energy, Danceability, Valence and Acousticness are on 0–100 scales and are divided by 100 to match FMA's unit scale. No feature is fabricated or imputed.
Blank metadata, nonfinite features, nonpositive tempo, or unit features outside [0,1] are dropped. Deduplicate IDs, then Unicode-NFKC/case-folded/whitespace-normalized artist/title pairs.
The source Index column is namespaced as popular:<Index>. These are local dataset IDs, not Spotify recording IDs.
Reserve one highest-popularity track each for Taylor Swift and Dua Lipa, then fill by historical popularity with at most 12 songs per normalized credited artist, taking 500 total. Ties use stable song ID order. This is catalog construction; recommendation lists still cap artists at two.
FMA artists use source IDs; popular tracks use normalized credited artist names. Collaborations and differently spelled artist credits may remain separate.

### Missing source values

| Column | Missing |
|---|---:|
| Index | 0 |
| Title | 0 |
| Artist | 0 |
| Top Genre | 0 |
| Year | 0 |
| Beats Per Minute (BPM) | 0 |
| Energy | 0 |
| Danceability | 0 |
| Valence | 0 |
| Acousticness | 0 |
| Popularity | 0 |

## Genre policy

Original genre labels are retained in genre_raw. Genre matching uses a documented coarse grouping:
- hip hop/rap → hip-hop; rock/metal/punk → rock; pop/boy band → pop.
- electro/dance/house/trance/ambient and explicit EDM tags → electronic.
- folk/singer-songwriter → folk; otherwise jazz/blues/country/reggae/soul/funk tokens map to that label.
- Rules run in that order; other labels remain unchanged. These are approximate groupings, not new measurements.
FMA retains its existing broad genre labels. Cross-source genre definitions and feature estimators are not perfectly comparable.

## FMA source

Defferrard, Benzi, Vandergheynst and Bresson, FMA: A Dataset for Music Analysis, ISMIR 2017.
Source: https://github.com/mdeff/fma ; metadata/features CC BY 4.0: https://creativecommons.org/licenses/by/4.0/ .
The unchanged 1,500-song base catalog is bundled as data/fma_catalog.csv. See reports/fma_data_report.md and data/fma_manifest.json for the original inspection, ranges and source-file hashes.

## Numerical features

| Feature | Meaning | Valid range | Full library observed |
|---|---|---|---|
| tempo | Estimated beats per minute | >0 BPM | 33.616–250.059 |
| energy | Estimated intensity/activity | 0–1 | 0.00195001–0.999236 |
| danceability | Estimated suitability for dancing | 0–1 | 0.0555955–0.966883 |
| valence | Estimated musical positivity | 0–1 | 0.0241883–0.99999 |
| acousticness | Estimated acoustic character/confidence | 0–1 | 0–0.995796 |

All five features have equal weight; min–max scaling fits only the selected library. Popularity never enters the similarity vector.

## Listening and experiment versions

Popular tracks offer YouTube and Apple Music search links derived from their title/artist. These are search links, not verified direct recordings or a Spotify integration.
Participants must find the correct recording and listen before rating unfamiliar tracks; if unavailable, use Not sure. FMA continues to offer its original 30-second excerpts with artist license attribution.
Each session records a content-hash version plus library scope. Results never pool Popular hits and Full library sessions, or sessions from the previous FMA-only dataset.
Existing feedback is preserved in SQLite; no old IDs or ratings are rewritten.

## Limitations and reproduction

Popularity-biased selection favors familiar older Western hits and may reduce novelty; this is not a representative or current mainstream catalog.
Feature estimates, broad genres and duplicate detection are imperfect. Remasters/live versions and artist-name aliases may remain.
Run python -m scripts.prepare_data --download, or use --popular-csv with the verified version 5 raw CSV. Rebuilding the optional FMA base from original metadata uses python -m scripts.prepare_fma --download.
