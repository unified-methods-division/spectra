"""Theme normalization via embedding similarity.

Snaps AI-returned theme slugs to existing themes when cosine similarity >= threshold.
Prevents duplicate themes like billing-issue vs billing-issues vs billing.
"""

import numpy as np

from analysis.embedder import embed_texts

MERGE_THRESHOLD = 0.85


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def normalize_themes(
    ai_themes: list[str],
    existing_slugs: list[str],
    threshold: float = MERGE_THRESHOLD,
) -> list[str]:
    """Snap AI-returned themes to existing slugs if similarity >= threshold."""
    if not existing_slugs or not ai_themes:
        return ai_themes

    ai_embeddings = embed_texts(ai_themes)
    existing_embeddings = embed_texts(existing_slugs)

    normalized = []
    for i, slug in enumerate(ai_themes):
        ai_vec = np.array(ai_embeddings[i])
        best_match = slug
        best_sim = 0.0

        for j, existing in enumerate(existing_slugs):
            sim = _cosine_similarity(ai_vec, np.array(existing_embeddings[j]))
            if sim > best_sim:
                best_sim = sim
                best_match = existing

        normalized.append(best_match if best_sim >= threshold else slug)

    return normalized
