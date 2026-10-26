# Song library

catalog.csv contains 2,000 real tracks with five supplied numerical musical features:
- 500 popular songs from 265 artists. Source: Sumit (iamsumat), Spotify – All Time Top 2000s Mega Dataset, version 5. Publisher's dataset license: CC0: Public Domain.
  https://www.kaggle.com/datasets/iamsumat/spotify-top-2000s-mega-dataset
  https://creativecommons.org/publicdomain/zero/1.0/
- 1,500 independent FMA tracks. Attribution: Defferrard, Benzi, Vandergheynst and Bresson, FMA: A Dataset for Music Analysis, ISMIR 2017. Metadata/features: CC BY 4.0.
  https://github.com/mdeff/fma
  https://creativecommons.org/licenses/by/4.0/

Popular hits is the default app library; Full library includes both sources. All methods use the same chosen scope. Dataset versions combine a content hash with that scope so old experiments remain separate.

Features: tempo in BPM; energy, danceability, valence, acousticness on 0–1 scales. Popular source values on 0–100 scales are divided by 100. No feature is imputed or invented. genre_raw preserves the original tag; genre contains documented broad grouping.

Popular IDs are namespaced source row identifiers (popular:<Index>), not Spotify track IDs. Popularity is historical and only used to select/order the catalog, never for similarity.

Rebuild: python -m scripts.prepare_data --download
Offline: python -m scripts.prepare_data --popular-csv /path/to/Spotify-2000.csv

The original FMA base is preserved in fma_catalog.csv; original inspection hashes are in fma_manifest.json. Rebuild that base separately with python -m scripts.prepare_fma --download.

See ../reports/data_report.md and manifest.json for licensing declarations, exact counts, cleaning, feature ranges and source SHA-256 hashes.

No popular-song audio, artwork or lyrics is bundled. Listening uses external title/artist searches. FMA excerpts are fetched on demand with the artist's license shown in the app. Raw downloads, audio caches and feedback databases are not included in repository packages.
