# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from enum import StrEnum
from multiprocessing.synchronize import Condition, Event

from sqlalchemy.orm import Session

from app.db.session_hooks import run_after_commit

from .base import BaseEventBus


class EventType(StrEnum):
    SOURCE_CHANGED = "SOURCE_CHANGED"
    SINK_CHANGED = "SINK_CHANGED"
    MODEL_CHANGED = "MODEL_CHANGED"
    PIPELINE_DATASET_COLLECTION_POLICIES_CHANGED = "PIPELINE_DATASET_COLLECTION_POLICIES_CHANGED"
    PIPELINE_STATUS_CHANGED = "PIPELINE_STATUS_CHANGED"
    INFERENCE_DEVICE_CHANGED = "INFERENCE_DEVICE_CHANGED"


class EventBus(BaseEventBus[EventType]):
    def __init__(
        self,
        source_changed_condition: Condition | None = None,
        sink_changed_condition: Condition | None = None,
        model_reload_event: Event | None = None,
    ) -> None:
        super().__init__()
        self._source_changed_condition = source_changed_condition
        self._sink_changed_condition = sink_changed_condition
        self._model_reload_event = model_reload_event

    @property
    def source_changed_condition(self) -> Condition | None:
        return self._source_changed_condition

    @property
    def sink_changed_condition(self) -> Condition | None:
        return self._sink_changed_condition

    @property
    def model_reload_event(self) -> Event | None:
        return self._model_reload_event

    @staticmethod
    def _notify_all(condition: Condition | None) -> None:
        if not condition:
            return
        with condition:
            condition.notify_all()

    @staticmethod
    def _should_notify_source(event_type: EventType) -> bool:
        return event_type in (EventType.SOURCE_CHANGED, EventType.PIPELINE_STATUS_CHANGED)

    @staticmethod
    def _should_notify_sink(event_type: EventType) -> bool:
        return event_type in (EventType.SINK_CHANGED, EventType.PIPELINE_STATUS_CHANGED)

    @staticmethod
    def _should_notify_model(event_type: EventType) -> bool:
        return event_type in (EventType.MODEL_CHANGED, EventType.PIPELINE_STATUS_CHANGED)

    @staticmethod
    def _should_notify_device(event_type: EventType) -> bool:
        return event_type == EventType.INFERENCE_DEVICE_CHANGED

    def emit_event(self, event_type: EventType) -> None:
        super().emit_event(event_type)

        if self._should_notify_source(event_type):
            self._notify_all(self._source_changed_condition)

        if self._should_notify_sink(event_type):
            self._notify_all(self._sink_changed_condition)

        if (
            self._should_notify_model(event_type) or self._should_notify_device(event_type)
        ) and self._model_reload_event:
            self._model_reload_event.set()

    def emit_event_after_commit(self, db_session: Session, event_type: EventType) -> None:
        """Emit ``event_type`` only after ``db_session`` successfully commits.

        Prefer this over :meth:`emit_event` when the emission is triggered by a database write whose
        result consumers must observe. Consumers (possibly in other processes, e.g. the
        ``StreamLoader``) react by re-reading the affected entity from the database; emitting before
        the write is durably committed would let that reload race the commit and read stale data
        (e.g. the previous ``video_path`` of a source). If the transaction is rolled back instead,
        the event is never emitted.
        """
        run_after_commit(db_session, lambda: self.emit_event(event_type))
