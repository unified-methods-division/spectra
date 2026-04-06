import csv
import json
from collections.abc import Iterable
from datetime import datetime, timezone as dt_timezone
from pathlib import Path
from typing import Any

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import FeedbackItem, Source

CSV_CONTENT_FIELDS = ("content", "text", "message", "body", "review", "feedback")
CSV_AUTHOR_FIELDS = ("author", "user", "username", "name")
CSV_EXTERNAL_ID_FIELDS = ("external_id", "id", "review_id", "ticket_id")
CSV_RECEIVED_AT_FIELDS = ("received_at", "created_at", "timestamp", "date", "at")


def _read_rows(file_path: str, file_format: str) -> Iterable[dict[str, Any]]:
    with open(file_path, encoding="utf-8") as file_handle:
        if file_format == "jsonl":
            for line in file_handle:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)
            return

        reader = csv.DictReader(file_handle)
        for row in reader:
            yield row


def _pick_first_non_empty(record: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = record.get(key)
        if value is None:
            continue
        string_value = str(value).strip()
        if string_value:
            return string_value
    return None


def _parse_received_at(raw_value: str | None) -> datetime:
    if not raw_value:
        return timezone.now()

    parsed = parse_datetime(raw_value)
    if parsed is None:
        return timezone.now()

    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, dt_timezone.utc)
    return parsed


def _next_config_state(config: dict[str, Any] | None, **kwargs: Any) -> dict[str, Any]:
    next_config = dict(config or {})
    next_config.update(kwargs)
    return next_config


@shared_task(bind=True, name="ingestion.parse_uploaded_feedback_file")
def parse_uploaded_feedback_file(
    self, source_id: str, file_path: str, file_format: str
) -> dict[str, Any]:
    source = Source.objects.select_related("tenant").get(id=source_id)
    source.config = _next_config_state(
        source.config,
        ingestion_status="processing",
        ingestion_task_id=self.request.id,
        ingestion_started_at=timezone.now().isoformat(),
        ingestion_error=None,
    )
    source.save(update_fields=["config"])

    created_count = 0
    skipped_count = 0
    batch: list[FeedbackItem] = []
    batch_size = 500

    try:
        for row in _read_rows(file_path=file_path, file_format=file_format):
            content = _pick_first_non_empty(row, CSV_CONTENT_FIELDS)
            if not content:
                skipped_count += 1
                continue

            external_id = _pick_first_non_empty(row, CSV_EXTERNAL_ID_FIELDS)
            author = _pick_first_non_empty(row, CSV_AUTHOR_FIELDS)
            received_at_value = _pick_first_non_empty(row, CSV_RECEIVED_AT_FIELDS)
            received_at = _parse_received_at(received_at_value)

            batch.append(
                FeedbackItem(
                    tenant=source.tenant,
                    source=source,
                    external_id=external_id,
                    content=content,
                    author=author,
                    metadata=row,
                    received_at=received_at,
                )
            )

            if len(batch) >= batch_size:
                with transaction.atomic():
                    FeedbackItem.objects.bulk_create(batch, batch_size=batch_size)
                created_count += len(batch)
                batch.clear()

        if batch:
            with transaction.atomic():
                FeedbackItem.objects.bulk_create(batch, batch_size=batch_size)
            created_count += len(batch)

        source.last_synced_at = timezone.now()
        source.config = _next_config_state(
            source.config,
            ingestion_status="completed",
            ingestion_finished_at=timezone.now().isoformat(),
            ingestion_counts={"created": created_count, "skipped": skipped_count},
        )
        source.save(update_fields=["last_synced_at", "config"])

        return {
            "source_id": source_id,
            "file_format": file_format,
            "created_count": created_count,
            "skipped_count": skipped_count,
        }
    except Exception as exc:
        source.config = _next_config_state(
            source.config,
            ingestion_status="failed",
            ingestion_finished_at=timezone.now().isoformat(),
            ingestion_error=str(exc),
        )
        source.save(update_fields=["config"])
        raise
    finally:
        try:
            Path(file_path).unlink(missing_ok=True)
        except OSError:
            pass
