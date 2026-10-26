"""Three deterministic recommendation methods, independent of Streamlit."""
from collections import Counter
from dataclasses import dataclass, field
from time import perf_counter
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from .data import FEATURES, clean_catalog

ALGORITHM_VERSION = "1.0.0"
METHODS = ("random", "genre", "features")
METHOD_NAMES = {"random": "Random", "genre": "Genre match", "features": "Musical features"}

@dataclass(frozen=True)
class Recommendation:
    song_id: str
    rank: int
    score: float | None = None
    fallback: bool = False

@dataclass
class RecommendationList:
    method: str
    items: list[Recommendation] = field(default_factory=list)
    elapsed_ms: float = 0
    warning: str = ""

class Recommender:
    def __init__(self, catalog, count=10, artist_limit=2):
        if count < 1 or artist_limit < 1:
            raise ValueError("Recommendation count and artist limit must be positive.")
        self.catalog, self.cleaning_report = clean_catalog(catalog)
        self.count, self.artist_limit = count, artist_limit
        self.ids = self.catalog["song_id"].tolist()
        self.positions = {song_id: i for i, song_id in enumerate(self.ids)}
        self.scaler = MinMaxScaler()
        self.scaled = self.scaler.fit_transform(self.catalog[list(FEATURES)]) if self.ids else np.empty((0, len(FEATURES)))

    def validate_selection(self, selected):
        selected = list(dict.fromkeys(str(s) for s in selected))
        if not selected:
            raise ValueError("Choose 3–5 favorite songs to start.")
        if not 3 <= len(selected) <= 5:
            raise ValueError("Choose between 3 and 5 distinct songs.")
        unknown = set(selected) - set(self.positions)
        if unknown:
            raise ValueError("Selected songs are absent or invalid in this catalog: " + ", ".join(sorted(unknown)))
        return sorted(selected)

    def profile(self, selected):
        selected = self.validate_selection(selected)
        return self.scaled[[self.positions[s] for s in selected]].mean(axis=0)

    def recommend(self, selected, method="features", seed=42):
        started = perf_counter()
        if method not in METHODS:
            raise ValueError("Unknown recommendation method.")
        selected = self.validate_selection(selected)
        eligible = [i for i, song_id in enumerate(self.ids) if song_id not in selected]
        rng = np.random.default_rng(seed)
        scores, fallback_indices = {}, set()
        warning = ""
        if method == "features":
            profile = self.profile(selected)
            if np.linalg.norm(profile) <= np.finfo(float).eps:
                # Cosine is undefined for zero profiles. Keep deterministic ties, never NaN.
                scores = {i: 0.0 for i in eligible}
                warning = "The selected profile is zero after scaling; all similarities tie at zero."
            else:
                similarities = cosine_similarity(profile.reshape(1, -1), self.scaled)[0]
                scores = {i: float(similarities[i]) for i in eligible}
            order = sorted(eligible, key=lambda i: (-scores[i], self.ids[i]))
        elif method == "random":
            order = rng.permutation(eligible).tolist()
        else:
            genres = set(self.catalog.loc[self.catalog.song_id.isin(selected), "genre"])
            matches = [i for i in eligible if self.catalog.iloc[i]["genre"] in genres]
            matched_indices = set(matches)
            other = [i for i in eligible if i not in matched_indices]
            order = rng.permutation(matches).tolist() + rng.permutation(other).tolist()
            fallback_indices = set(other)
        counts, seen, items = Counter(), set(), []
        for i in order:
            row = self.catalog.iloc[i]
            if row.recording_key in seen or counts[row.artist_key] >= self.artist_limit:
                continue
            counts[row.artist_key] += 1
            seen.add(row.recording_key)
            items.append(Recommendation(self.ids[i], len(items)+1, scores.get(i), i in fallback_indices))
            if len(items) == self.count:
                break
        if len(items) < self.count:
            warning = (warning + " " + f"Only {len(items)} eligible songs remain under the artist limit.").strip()
        return RecommendationList(method, items, (perf_counter()-started)*1000, warning)

    def compare(self, selected, seed=42):
        return {method: self.recommend(selected, method, seed) for method in METHODS}

def blinded_order(lists, seed=42):
    ids = sorted({item.song_id for result in lists.values() for item in result.items})
    return np.random.default_rng(seed).permutation(ids).tolist()
