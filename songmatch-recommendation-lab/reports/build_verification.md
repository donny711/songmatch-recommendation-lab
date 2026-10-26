# Build verification

- Python 3.14.3.
- 42 pytest checks passed after adding the popular catalog, including four Streamlit AppTest workflows.
- Default library: 500 popular songs from 265 artists. Full library: 2,000 songs (500 popular + 1,500 FMA).
- Popular source: iamsumat/spotify-top-2000s-mega-dataset, version 5. Publisher license declaration checked through the official Kaggle metadata API: CC0: Public Domain.
- Raw popular CSV pinned by SHA-256, recorded in data/manifest.json. Four source features were converted from 0–100 to 0–1 without inventing values.
- Verified recognizable tracks include Taylor Swift / Shake It Off, Billie Eilish / bad guy, Ed Sheeran / Shape of You and Eminem / Without Me.
- Standalone engine generated ten popular recommendations for each method from popular:593, popular:787 and popular:688, seed 42.
- Tests cover library switching, recommendation scope isolation, source feature conversion and encoded external listening links, in addition to the original ranking/storage/evaluation safeguards.
- Previous FMA metadata inspection and source hashes preserved in data/fma_manifest.json and reports/fma_data_report.md.
- A real FMA 30-second excerpt was checked during the initial build. Popular tracks use external YouTube/Apple Music searches; no audio is copied or bundled.
- Existing SQLite study feedback is retained. Dataset content hash plus scope isolates Popular hits, Full library and earlier FMA-only experiments.
- Streamlit server refreshed at http://127.0.0.1:8501.
- No native browser screenshots: the initial browser app access approval timed out. Visual layout remains unverified through native browser automation.
- No volunteer evaluation was performed by the assistant. Tests use isolated temporary databases.
- GitHub Actions supplied; no push or remote CI execution. Persistent-volume Docker deployment supplied; not built or publicly deployed here.

Current scope versions:
- popular: songmatch-a7184e0d6086ddc1-popular
- all: songmatch-a7184e0d6086ddc1-all
