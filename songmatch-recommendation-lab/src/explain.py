"""Descriptions use measured scaled differences; cosine is never a probability."""
import numpy as np
from .data import FEATURES

def explain(engine, selected, recommendation, method):
    row = engine.catalog.iloc[engine.positions[recommendation.song_id]]
    if method == "random":
        return "Randomly sampled from the eligible catalog, with at most two songs per artist."
    if method == "genre":
        if recommendation.fallback:
            return "Filled from another genre after matching candidates ran out under the artist limit."
        return f"Shares the {row.genre} genre with one or more of your selected songs."
    profile = engine.profile(selected)
    if np.linalg.norm(profile) <= np.finfo(float).eps:
        return "Zero profile: cosine similarity is undefined, so candidates tie at zero."
    differences = np.abs(engine.scaled[engine.positions[recommendation.song_id]] - profile)
    closest = np.argsort(differences, kind="stable")[:2]
    a, b = (FEATURES[i] for i in closest)
    if differences[closest[1]] <= 0.15:
        return f"Similar {a} and {b} to your selected-song profile (within 15% of the catalog range)."
    return f"Closest profile dimensions: {a} and {b}; this track still differs substantially."

def profile_comparison(engine, selected, song_id):
    import pandas as pd
    return pd.DataFrame({
        "Feature": [f.title() for f in FEATURES],
        "Your profile": engine.profile(selected),
        "This track": engine.scaled[engine.positions[song_id]],
    }).set_index("Feature")
