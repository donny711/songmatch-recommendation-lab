# SongMatch experiment report

Status: **data collection pending**. No volunteer sessions have been run. Software tests and preview-download checks are not human evaluation evidence.

## Question

Does an average musical-feature profile produce more enjoyable and unfamiliar discoveries than random selection or genre matching?

## Frozen v1 configuration

Default dataset: songmatch-a7184e0d6086ddc1-popular (500 popular tracks). Full-library version: songmatch-a7184e0d6086ddc1-all (2,000 tracks). Algorithm: 1.0.0.

Choose and freeze one library scope for a final study. Do not pool scopes; earlier FMA-only sessions are preserved separately.
Inputs: 3–5 distinct liked songs. Outputs: 10 per method when possible. Maximum two per artist identity (FMA ID or normalized credited name for popular tracks). Five equally weighted features; min–max scaling; cosine similarity. Development seed 42. Same constraints apply to both baselines.

## Collection protocol

1. Recruit 5–10 volunteers; request one or two sessions each. Obtain their agreement to anonymous storage.
2. Run an initial pilot with SONGMATCH_PHASE=pilot. Ask participants to select songs they actually enjoy; use selection previews if they do not recognize tracks.
3. Participants hear a shuffled union of the three methods. Each unique song is rated once, with familiarity and listening confirmation. Method labels and explanations appear only after submission.
4. Popular songs have title/artist search links to YouTube and Apple Music. Participants must locate the correct recording and listen; FMA songs offer 30-second excerpts. Use Not sure if a song cannot be assessed. Do not encourage guessing.
5. Record usability problems and failure cases during the pilot. Make justified changes, then bump the algorithm version and retain the old catalog/version.
6. Freeze the final catalog and algorithm. Set SONGMATCH_PHASE=final and collect fresh sessions. Never reuse pilot ratings as new final evidence.
7. Back up SQLite, export final per-session and method metrics from Results, and complete the findings below.

Avoid coaching participants toward musical features. Preserve randomization and shared constraints. Retain the same anonymous participant code on repeat sessions; never collect names or email.

## Metrics

| Measure | Definition |
|---|---|
| Positive-rating rate | Likes / (likes + dislikes); aggregate weighted by assessed count |
| Precision@10 | Likes / 10, only when the list has ten songs and every song is assessed |
| Unassessed | Explicit Not sure or missing rating; shown separately, excluded from assessed denominator |
| Artist diversity | Distinct artist identities per method/session list |
| Unknown positive discoveries | Liked recommendations marked previously unfamiliar |
| Generation time | Time to generate each method list, excluding initialization, storage, rendering and listening |
| Genre fallback | Count of out-of-genre fillers required after artist filtering |

Report denominators and number of fully assessed lists. Inspect paired session rows before pooling participants. Repeated sessions from one person are not independent participants. Shared songs are legitimately attributed to each recommending method, so method outcomes are correlated. The small convenience sample supports descriptive findings, not a strong population claim.

## Actual results

Completed volunteer sessions: **0**. Participants: **0**.

| Method | Assessed | Likes | Unassessed | Positive rate | Precision@10 |
|---|---:|---:|---:|---|---|
| Random | 0 | 0 | 0 | Not available | Not available |
| Genre | 0 | 0 | 0 | Not available | Not available |
| Musical features | 0 | 0 | 0 | Not available | Not available |

There is no measured winner. No claim of recommendation quality is supported yet.

## Findings to complete from fresh final data

1. Which method received the most positive feedback? Pending.
2. Did this vary by participant or input songs? Pending.
3. Which methods introduced unfamiliar songs people liked? Pending.
4. Were results too concentrated in similar artists despite the cap? Pending.
5. Where did methods fail, and were previews/genre labels/features involved? Pending.
6. What change would the evidence justify next? Pending.

If genre or random wins, report that directly. Include concrete failure cases with song IDs, without retrospectively tuning against the same final ratings.

## Known design limitations

Broad genres, historical feature estimates and popularity, popularity-based selection bias, uneven FMA coverage, name-based recording deduplication and cross-source estimator differences. Single-profile averaging can lose multiple taste clusters. Cosine similarity can reward the direction of a vector despite large feature differences; explanations acknowledge this. Thirty seconds may not represent a whole song. Listening/familiarity are self-reported. Participant codes can be forgotten or reused by different people. Open anonymous participation is unsuitable for an unsupervised large study.
