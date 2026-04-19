from __future__ import annotations

from typing import Any

import numpy as np
from django.utils import timezone
from pydantic import BaseModel
from pydantic_ai import Agent
from sklearn.cluster import HDBSCAN

from analysis.embedder import embed_texts
from ingestion.models import FeedbackItem
from themes.models import Theme

MIN_CLUSTER_SIZE = 5
MAX_REPRESENTATIVES = 5
MERGE_THRESHOLD = 0.85
DEFAULT_MODEL = "openai:gpt-4.1-nano"


class ThemeSummary(BaseModel):
    name: str
    slug: str
    description: str


_summarizer: Agent[None, ThemeSummary] = Agent(
    output_type=ThemeSummary,
    instructions=(
        "You are given representative feedback items from a cluster. "
        "Return:\n"
        "- name: single-word or two-word topic (billing, onboarding, csv-export)\n"
        "- slug: lowercase-hyphenated version of name\n"
        "- description: one-liner, no filler words, what this topic covers\n\n"
        "Example descriptions:\n"
        "- 'Payment processing and subscription charges'\n"
        "- 'First-time user setup and account creation'\n"
        "- 'Data export and download functionality'"
    ),
)


def summarize_cluster(
    contents: list[str], *, model: str | None = None
) -> ThemeSummary:
    prompt = "Representative feedback items:\n\n" + "\n---\n".join(contents)
    result = _summarizer.run_sync(prompt, model=model or DEFAULT_MODEL)
    return result.output


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _attach_theme_slug_to_items(item_ids: list, slug: str) -> None:
    """Ensure each item's `themes` JSON includes this slug (explorer filters on it)."""
    if not item_ids:
        return
    to_update: list[FeedbackItem] = []
    for item in FeedbackItem.objects.filter(id__in=item_ids).only("id", "themes"):
        current = list(item.themes) if item.themes else []
        if slug not in current:
            item.themes = [*current, slug]
            to_update.append(item)
    if to_update:
        FeedbackItem.objects.bulk_update(to_update, ["themes"])


def _pick_representatives(
    embeddings: np.ndarray,
    contents: list[str],
    max_n: int = MAX_REPRESENTATIVES,
) -> list[str]:
    centroid = embeddings.mean(axis=0)
    sims = np.array([_cosine_similarity(centroid, e) for e in embeddings])
    top_indices = sims.argsort()[::-1][:max_n]
    return [contents[i] for i in top_indices]


def discover_themes(tenant_id: str) -> dict[str, Any]:
    items = list(
        FeedbackItem.objects.filter(
            tenant_id=tenant_id,
            embedding__isnull=False,
        ).values_list("id", "content", "embedding")
    )

    if len(items) < MIN_CLUSTER_SIZE:
        return {"themes_created": 0, "themes_merged": 0, "noise_items": 0}

    ids = [row[0] for row in items]
    contents = [row[1] for row in items]
    embeddings = np.array([list(row[2]) for row in items])

    labels = HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=3,
    ).fit_predict(embeddings)

    noise_mask = labels == -1
    noise_count = int(noise_mask.sum())

    cluster_labels = set(labels[~noise_mask])
    if not cluster_labels:
        return {"themes_created": 0, "themes_merged": 0, "noise_items": noise_count}

    themes_created = 0
    themes_merged = 0

    new_theme_names: list[str] = []
    cluster_data: list[dict] = []

    for label in sorted(cluster_labels):
        mask = labels == label
        cluster_embeddings = embeddings[mask]
        cluster_contents = [contents[i] for i, m in enumerate(mask) if m]
        cluster_count = int(mask.sum())

        reps = _pick_representatives(cluster_embeddings, cluster_contents)
        summary = summarize_cluster(reps)

        item_ids = [ids[i] for i in range(len(ids)) if mask[i]]
        cluster_data.append({
            "summary": summary,
            "count": cluster_count,
            "item_ids": item_ids,
        })
        new_theme_names.append(summary.name)

    new_name_embeddings = embed_texts(new_theme_names)

    existing_themes = list(Theme.objects.filter(tenant_id=tenant_id))
    existing_name_vecs: list[tuple[Theme, np.ndarray]] | None = None
    if existing_themes:
        existing_name_strs = [t.name for t in existing_themes]
        existing_vecs = embed_texts(existing_name_strs)
        existing_name_vecs = [
            (t, np.array(v)) for t, v in zip(existing_themes, existing_vecs)
        ]

    now = timezone.now()

    for cd, new_vec in zip(cluster_data, new_name_embeddings):
        summary = cd["summary"]
        count = cd["count"]
        item_ids = cd["item_ids"]
        new_vec_arr = np.array(new_vec)

        best_match: Theme | None = None
        best_sim = 0.0

        if existing_name_vecs:
            for theme, evec in existing_name_vecs:
                sim = _cosine_similarity(new_vec_arr, evec)
                if sim > best_sim:
                    best_sim = sim
                    best_match = theme

        if best_match and best_sim >= MERGE_THRESHOLD:
            best_match.item_count += count
            best_match.save(update_fields=["item_count"])
            _attach_theme_slug_to_items(item_ids, best_match.slug)
            themes_merged += 1
        else:
            Theme.objects.create(
                tenant_id=tenant_id,
                slug=summary.slug,
                name=summary.name,
                description=summary.description,
                source=Theme.ThemeSource.DISCOVERED,
                first_seen_at=now,
                item_count=count,
            )
            _attach_theme_slug_to_items(item_ids, summary.slug)
            themes_created += 1

    return {
        "themes_created": themes_created,
        "themes_merged": themes_merged,
        "noise_items": noise_count,
    }
