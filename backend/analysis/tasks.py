import logging
from typing import Any

from celery import chain, shared_task
from themes.tasks import discover_themes_for_source
from django.db import transaction
from django.utils import timezone

from ingestion.models import FeedbackItem, RoutingConfig, Source
from themes.models import Theme

from .classifier import classify_item
from .embedder import embed_texts

logger = logging.getLogger(__name__)

DEFAULT_CONFIDENCE_THRESHOLD = 0.85


def _next_config_state(config: dict[str, Any] | None, **kwargs: Any) -> dict[str, Any]:
    next_config = dict(config or {})
    next_config.update(kwargs)
    return next_config


@shared_task(bind=True, name="analysis.classify_feedback_batch")
def classify_feedback_batch(
    self, source_id: str, batch_size: int = 50
) -> dict[str, Any]:
    source = Source.objects.select_related("tenant").get(id=source_id)
    source.config = _next_config_state(
        source.config,
        classification_status="processing",
        classification_task_id=self.request.id,
        classification_started_at=timezone.now().isoformat(),
        classification_error=None,
    )
    source.save(update_fields=["config"])

    # Load tenant taxonomy (explicit filter — no request context in Celery)
    theme_slugs = list(
        Theme.objects.filter(tenant=source.tenant).values_list("slug", flat=True)
    )

    # Load routing config or defaults
    try:
        routing = RoutingConfig.objects.get(source=source)
        threshold = routing.confidence_threshold
        low_action = routing.items_below_threshold_action
    except RoutingConfig.DoesNotExist:
        threshold = DEFAULT_CONFIDENCE_THRESHOLD
        low_action = RoutingConfig.LowConfidenceAction.FLAG

    # Pick up unprocessed items (partial index: idx_feedback_unprocessed)
    items = list(
        FeedbackItem.objects.filter(
            source_id=source_id, processed_at__isnull=True
        )[:batch_size]
    )

    classified_items = []
    failed_count = 0
    discovered_slugs = set()

    for item in items:
        try:
            analysis = classify_item(item.content, theme_slugs)
        except Exception:
            logger.exception("Classification failed for item %s", item.id)
            failed_count += 1
            continue

        item.sentiment = analysis.sentiment
        item.sentiment_confidence = analysis.sentiment_confidence
        item.urgency = analysis.urgency
        item.themes = analysis.themes
        item.ai_summary = analysis.ai_summary
        item.processed_at = timezone.now()

        # Confidence routing
        if analysis.sentiment_confidence < threshold:
            if low_action == RoutingConfig.LowConfidenceAction.FLAG:
                item.metadata = item.metadata or {}
                item.metadata["needs_review"] = True
            elif low_action == RoutingConfig.LowConfidenceAction.SKIP_AI:
                # Undo — leave unprocessed
                item.sentiment = None
                item.sentiment_confidence = None
                item.urgency = None
                item.themes = None
                item.ai_summary = None
                item.processed_at = None
                continue

        classified_items.append(item)

        # Track new theme slugs
        for slug in analysis.themes:
            if slug not in theme_slugs:
                discovered_slugs.add(slug)

    try:
        with transaction.atomic():
            if classified_items:
                FeedbackItem.objects.bulk_update(
                    classified_items,
                    fields=[
                        "sentiment",
                        "sentiment_confidence",
                        "urgency",
                        "themes",
                        "ai_summary",
                        "processed_at",
                        "metadata",
                    ],
                )

            # Upsert discovered themes
            for slug in discovered_slugs:
                Theme.objects.update_or_create(
                    tenant=source.tenant,
                    slug=slug,
                    defaults={
                        "name": slug.replace("-", " ").title(),
                        "source": Theme.ThemeSource.DISCOVERED,
                        "first_seen_at": timezone.now(),
                    },
                )

        source.config = _next_config_state(
            source.config,
            classification_status="completed",
            classification_finished_at=timezone.now().isoformat(),
            classification_counts={
                "classified": len(classified_items),
                "failed": failed_count,
                "discovered_themes": list(discovered_slugs),
            },
        )
        source.save(update_fields=["config"])

        return {
            "source_id": source_id,
            "classified": len(classified_items),
            "failed": failed_count,
            "discovered_themes": list(discovered_slugs),
        }
    except Exception as exc:
        source.config = _next_config_state(
            source.config,
            classification_status="failed",
            classification_finished_at=timezone.now().isoformat(),
            classification_error=str(exc),
        )
        source.save(update_fields=["config"])
        raise


EMBED_CHUNK_SIZE = 100


@shared_task(bind=True, name="analysis.embed_feedback_batch")
def embed_feedback_batch(
    self, source_id: str, batch_size: int = 500
) -> dict[str, Any]:
    source = Source.objects.select_related("tenant").get(id=source_id)
    source.config = _next_config_state(
        source.config,
        embedding_status="processing",
        embedding_task_id=self.request.id,
        embedding_started_at=timezone.now().isoformat(),
        embedding_error=None,
    )
    source.save(update_fields=["config"])

    # Only embed classified items that don't have embeddings yet
    items = list(
        FeedbackItem.objects.filter(
            source_id=source_id,
            processed_at__isnull=False,
            embedding__isnull=True,
        )[:batch_size]
    )

    embedded_count = 0
    failed_count = 0

    # Process in chunks — one API call per chunk (API-level batching)
    for i in range(0, len(items), EMBED_CHUNK_SIZE):
        chunk = items[i : i + EMBED_CHUNK_SIZE]
        try:
            vectors = embed_texts([item.content for item in chunk])
            for item, vector in zip(chunk, vectors):
                item.embedding = vector
            embedded_count += len(chunk)
        except Exception:
            logger.exception(
                "Embedding failed for chunk %d-%d of source %s",
                i,
                i + len(chunk),
                source_id,
            )
            failed_count += len(chunk)

    try:
        with transaction.atomic():
            # Only update items that got embeddings
            items_with_embeddings = [item for item in items if item.embedding]
            if items_with_embeddings:
                FeedbackItem.objects.bulk_update(
                    items_with_embeddings, fields=["embedding"]
                )

        source.config = _next_config_state(
            source.config,
            embedding_status="completed",
            embedding_finished_at=timezone.now().isoformat(),
            embedding_counts={
                "embedded": embedded_count,
                "failed": failed_count,
            },
        )
        source.save(update_fields=["config"])

        return {
            "source_id": source_id,
            "embedded": embedded_count,
            "failed": failed_count,
        }
    except Exception as exc:
        source.config = _next_config_state(
            source.config,
            embedding_status="failed",
            embedding_finished_at=timezone.now().isoformat(),
            embedding_error=str(exc),
        )
        source.save(update_fields=["config"])
        raise


@shared_task(name="analysis.process_source")
def process_source(source_id: str) -> None:
    """classify → embed → theme discovery (tenant-wide)."""
    pipeline = chain(
        classify_feedback_batch.si(source_id),
        embed_feedback_batch.si(source_id),
        discover_themes_for_source.si(source_id),
    )
    pipeline.apply_async()
