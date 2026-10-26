"""Explicit denominators and paired, per-session comparisons."""
import json
import numpy as np
import pandas as pd

def session_metrics(rows):
    result = []
    if rows.empty:
        return pd.DataFrame()
    for (session_id,method),group in rows.groupby(["session_id","method"],sort=True):
        # Unanswered or explicit Not sure both remain unassessed.
        likes = int(group.rating.eq("like").sum())
        assessed = int(group.rating.isin(["like","dislike"]).sum())
        count = len(group)
        unknown_likes = int((group.rating.eq("like") & group.knew_song.eq(0)).sum())
        metadata = json.loads(group.iloc[0].method_metadata).get(method,{})
        result.append({
            "session_id": session_id, "participant_id": group.iloc[0].participant_id,
            "method": method, "recommended": count, "liked": likes, "assessed": assessed,
            "unassessed": count-assessed,
            "positive_rate_assessed": likes/assessed if assessed else np.nan,
            "precision_at_10": likes/10 if count == 10 and assessed == 10 else np.nan,
            "distinct_artists": group.artist_key.nunique(),
            "unknown_liked": unknown_likes,
            "fallback_count": int(group.fallback.sum()),
            "generation_ms": metadata.get("elapsed_ms",np.nan),
        })
    return pd.DataFrame(result)

def aggregate_metrics(per_session):
    if per_session.empty:
        return pd.DataFrame()
    result = []
    for method,group in per_session.groupby("method",sort=True):
        assessed = int(group.assessed.sum())
        liked = int(group.liked.sum())
        result.append({
            "method": method, "sessions": len(group),
            "recommended": int(group.recommended.sum()), "liked": liked, "assessed": assessed,
            "unassessed": int(group.unassessed.sum()),
            "positive_rate_assessed": liked/assessed if assessed else np.nan,
            "precision_at_10": group.precision_at_10.mean(),
            "fully_assessed_lists_of_10": int(group.precision_at_10.notna().sum()),
            "distinct_artists_per_list": group.distinct_artists.mean(),
            "unknown_liked": int(group.unknown_liked.sum()),
            "generation_ms": group.generation_ms.mean(),
            "fallback_count": int(group.fallback_count.sum()),
        })
    return pd.DataFrame(result)
