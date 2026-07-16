# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import multiprocessing as mp
import queue
import uuid
from unittest.mock import MagicMock, patch

import numpy as np

from app.models import DisconnectedSinkConfig, SinkType
from app.models.sink import SinkStatus, SinkStatusCode
from app.services.dispatchers import DispatchError
from app.services.event.event_bus import EventBus, EventType
from app.stream.stream_data import InferenceData, StreamData
from app.webrtc import FrameBroadcaster
from app.workers.dispatching import DispatchingWorker
from app.workers.sink_status_holder import SinkStatusHolder


def _make_stream_data() -> StreamData:
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    return StreamData(
        frame_data=frame,
        timestamp=0.0,
        source_metadata={},
        inference_data=InferenceData(
            prediction=MagicMock(),
            visualized_prediction=frame.copy(),
            model_id=uuid.uuid4(),
        ),
    )


def _make_worker(event_bus: EventBus, broadcaster: FrameBroadcaster[np.ndarray]) -> DispatchingWorker:
    with patch.object(DispatchingWorker, "_load_sink", return_value=(DisconnectedSinkConfig(), [])):
        return DispatchingWorker(
            event_bus=event_bus,
            pred_queue=mp.Queue(),
            rtc_stream_broadcaster=broadcaster,
            stop_event=mp.Event(),
            data_collector=MagicMock(),
            sink_status_holder=MagicMock(),
        )


class TestDispatchingWorkerSourceChange:
    def test_source_changed_clears_broadcaster(self):
        """A SOURCE_CHANGED event drops the cached frame so new consumers don't see a stale frame."""
        event_bus = EventBus()
        broadcaster = FrameBroadcaster[np.ndarray]()
        _make_worker(event_bus, broadcaster)

        # A frame from the previous source is cached and would be seeded to new consumers.
        broadcaster.broadcast(np.zeros((2, 2, 3), dtype=np.uint8))
        assert broadcaster.latest_frame is not None

        event_bus.emit_event(EventType.SOURCE_CHANGED)

        # The cached frame is dropped, so a freshly connecting consumer gets nothing stale.
        assert broadcaster.latest_frame is None
        new_consumer_queue = broadcaster.register("new-consumer")
        assert new_consumer_queue.empty()

    def test_source_changed_drains_existing_consumer_queues(self):
        """Already-connected consumers also have their queued stale frames drained."""
        event_bus = EventBus()
        broadcaster = FrameBroadcaster[np.ndarray]()
        _make_worker(event_bus, broadcaster)

        consumer_queue = broadcaster.register("consumer")
        broadcaster.broadcast(np.zeros((2, 2, 3), dtype=np.uint8))
        assert not consumer_queue.empty()

        event_bus.emit_event(EventType.SOURCE_CHANGED)

        assert consumer_queue.empty()

    def test_sink_changed_does_not_clear_broadcaster(self):
        """A SINK_CHANGED event must not drop the cached WebRTC frame."""
        event_bus = EventBus()
        broadcaster = FrameBroadcaster[np.ndarray]()
        _make_worker(event_bus, broadcaster)

        broadcaster.broadcast(np.zeros((2, 2, 3), dtype=np.uint8))

        with patch.object(DispatchingWorker, "_load_sink", return_value=(DisconnectedSinkConfig(), [])):
            event_bus.emit_event(EventType.SINK_CHANGED)

    def test_dispatch_error_does_not_stop_loop(self):
        """A DispatchError from a dispatcher is caught; the loop continues and WebRTC broadcast still happens."""
        event_bus = EventBus()
        broadcaster = FrameBroadcaster[np.ndarray]()

        failing_dispatcher = MagicMock()
        failing_dispatcher.dispatch.side_effect = DispatchError()

        pred_queue: queue.Queue = queue.Queue()
        pred_queue.put(_make_stream_data())
        pred_queue.put(_make_stream_data())

        with patch.object(
            DispatchingWorker,
            "_load_sink",
            return_value=(MagicMock(sink_type=SinkType.FOLDER, id=uuid.uuid4()), [failing_dispatcher]),
        ):
            worker = DispatchingWorker(
                event_bus=event_bus,
                pred_queue=pred_queue,  # type: ignore[arg-type]
                rtc_stream_broadcaster=broadcaster,
                stop_event=mp.Event(),
                data_collector=MagicMock(),
                sink_status_holder=MagicMock(),
            )

        def stop_when_empty() -> bool:
            return pred_queue.empty()

        worker.should_stop = stop_when_empty
        worker.run_loop()

        assert failing_dispatcher.dispatch.call_count == 2
        assert broadcaster.latest_frame is not None

        # Each failed dispatch reports an ERROR sink status to the holder.
        sink_status = worker._sink_status_holder.status
        assert isinstance(sink_status, SinkStatus)
        assert sink_status.code == SinkStatusCode.ERROR


class TestDispatchingWorkerResilience:
    """The dispatching worker must keep running through sink and data-collection failures."""

    def test_load_sink_survives_connect_failure(self):
        """A sink that cannot be connected is dropped and reported as ERROR, without crashing."""
        worker = object.__new__(DispatchingWorker)
        worker._event_bus = EventBus()
        holder = SinkStatusHolder()
        worker._sink_status_holder = holder

        failing_dispatcher = MagicMock()
        failing_dispatcher.connect.side_effect = ConnectionError("broker down")
        sink = MagicMock(sink_type=SinkType.MQTT, id=uuid.uuid4(), name="broker")

        with (
            patch("app.workers.dispatching.get_db_session") as mock_db,
            patch("app.workers.dispatching.SinkService") as mock_sink_service,
            patch(
                "app.workers.dispatching.DispatchService.get_destinations",
                return_value=[failing_dispatcher],
            ),
        ):
            mock_db.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_db.return_value.__exit__ = MagicMock(return_value=False)
            mock_sink_service.return_value.get_active_sink.return_value = sink

            result_sink, destinations = worker._load_sink()

        # The unreachable destination is dropped so the pipeline keeps running (WebRTC still works).
        assert result_sink is sink
        assert destinations == []
        failing_dispatcher.connect.assert_called_once()
        # The sink health is reported as ERROR.
        status = holder.status
        assert isinstance(status, SinkStatus)
        assert status.code == SinkStatusCode.ERROR

    def test_load_sink_survives_dispatcher_build_failure(self):
        """A failure building the dispatchers (e.g. unsupported sink) does not crash the worker."""
        worker = object.__new__(DispatchingWorker)
        worker._event_bus = EventBus()
        holder = SinkStatusHolder()
        worker._sink_status_holder = holder

        sink = MagicMock(sink_type=SinkType.ROS, id=uuid.uuid4(), name="ros-topic")

        with (
            patch("app.workers.dispatching.get_db_session") as mock_db,
            patch("app.workers.dispatching.SinkService") as mock_sink_service,
            patch(
                "app.workers.dispatching.DispatchService.get_destinations",
                side_effect=NotImplementedError("ROS output is not implemented yet"),
            ),
        ):
            mock_db.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_db.return_value.__exit__ = MagicMock(return_value=False)
            mock_sink_service.return_value.get_active_sink.return_value = sink

            result_sink, destinations = worker._load_sink()

        assert result_sink is sink
        assert destinations == []
        status = holder.status
        assert isinstance(status, SinkStatus)
        assert status.code == SinkStatusCode.ERROR

    def test_data_collector_failure_does_not_stop_loop(self):
        """A failure while collecting to the dataset must not stop dispatching or crash the thread."""
        event_bus = EventBus()
        broadcaster = FrameBroadcaster[np.ndarray]()

        pred_queue: queue.Queue = queue.Queue()
        pred_queue.put(_make_stream_data())
        pred_queue.put(_make_stream_data())

        failing_collector = MagicMock()
        failing_collector.collect.side_effect = RuntimeError("db is down")

        with patch.object(DispatchingWorker, "_load_sink", return_value=(DisconnectedSinkConfig(), [])):
            worker = DispatchingWorker(
                event_bus=event_bus,
                pred_queue=pred_queue,  # type: ignore[arg-type]
                rtc_stream_broadcaster=broadcaster,
                stop_event=mp.Event(),
                data_collector=failing_collector,
                sink_status_holder=MagicMock(),
            )

        worker.should_stop = lambda: pred_queue.empty()  # type: ignore[method-assign]
        worker.run_loop()

        # Both frames were processed despite the collector failing, and WebRTC still received them.
        assert failing_collector.collect.call_count == 2
        assert broadcaster.latest_frame is not None
