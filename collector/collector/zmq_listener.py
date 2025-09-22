"""ZMQ listener utilities."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

try:  # pragma: no cover
    import zmq  # type: ignore[import-not-found, import-untyped]
except ImportError:  # pragma: no cover
    zmq = None  # type: ignore[assignment]


@dataclass
class ZMQMetric:
    endpoint: str
    topic: bytes
    last_seen: float = field(default_factory=time.time)
    message_count: int = 0


class ZMQListener:
    """Simple threaded ZMQ subscriber that tracks message liveness."""

    def __init__(
        self,
        endpoints: Dict[str, str],
        callback: Optional[Callable[[str, bytes], None]] = None,
    ) -> None:
        if zmq is None:
            raise RuntimeError("pyzmq is required for ZMQListener")
        self.context = zmq.Context.instance()
        self.endpoints = endpoints
        self.callback = callback
        self.metrics: Dict[str, ZMQMetric] = {}
        self._threads: list[threading.Thread] = []
        self._stop = threading.Event()

    def start(self) -> None:
        for topic, endpoint in self.endpoints.items():
            metric = ZMQMetric(endpoint=endpoint, topic=topic.encode())
            self.metrics[topic] = metric
            thread = threading.Thread(target=self._worker, args=(topic, endpoint), daemon=True)
            thread.start()
            self._threads.append(thread)

    def stop(self) -> None:
        self._stop.set()
        for thread in self._threads:
            thread.join(timeout=1)
        self.context.term()

    def _worker(self, topic: str, endpoint: str) -> None:
        if zmq is None:
            raise RuntimeError("pyzmq is required for ZMQListener")
        socket = self.context.socket(zmq.SUB)
        socket.setsockopt(zmq.SUBSCRIBE, topic.encode())
        socket.connect(endpoint)
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        metric = self.metrics[topic]
        while not self._stop.is_set():
            events = dict(poller.poll(timeout=1000))
            if socket in events and events[socket] == zmq.POLLIN:
                message = socket.recv()
                metric.last_seen = time.time()
                metric.message_count += 1
                if self.callback:
                    self.callback(topic, message)
        socket.close(linger=0)

    def status(self) -> Dict[str, Dict[str, float | str]]:
        return {
            topic: {
                "endpoint": metric.endpoint,
                "seconds_since": max(0.0, time.time() - metric.last_seen),
                "messages": float(metric.message_count),
            }
            for topic, metric in self.metrics.items()
        }
