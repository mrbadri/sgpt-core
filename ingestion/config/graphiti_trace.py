"""Optional logging tracer for graphiti_core (nested spans: ``add_episode``, ``llm.generate``, …).

Enable with ``INGEST_GRAPHITI_TRACE=1``. Each LLM round-trip appears as a child span with duration;
set ``INGEST_GRAPHITI_TRACE_VERBOSE=1`` to attach full span attributes on exit.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from graphiti_core.tracer import Tracer, TracerSpan


class LoggingTracerSpan(TracerSpan):
    def __init__(self) -> None:
        self.attrs: dict[str, Any] = {}

    def add_attributes(self, attributes: dict[str, Any]) -> None:
        for k, v in attributes.items():
            if v is not None:
                self.attrs[k] = v

    def set_status(self, status: str, description: str | None = None) -> None:
        self.attrs["span.status"] = status
        if description:
            self.attrs["span.status_desc"] = description

    def record_exception(self, exception: Exception) -> None:
        self.attrs["span.exception"] = type(exception).__name__


_ATTR_KEYS_COMPACT = (
    "prompt.name",
    "max_tokens",
    "model.size",
    "llm.provider",
    "cache.hit",
    "episode.uuid",
    "group_id",
    "node.count",
    "edge.count",
    "edge.invalidated_count",
    "previous_episodes.count",
    "duration_ms",
    "span.status",
    "span.status_desc",
    "span.exception",
)


def _format_attrs(attrs: dict[str, Any], *, verbose: bool) -> str:
    if not attrs:
        return ""
    if verbose:
        safe = {k: v for k, v in sorted(attrs.items()) if not str(k).startswith("_")}
    else:
        safe = {k: attrs[k] for k in _ATTR_KEYS_COMPACT if k in attrs}
    if not safe:
        return ""
    return " | " + ", ".join(f"{k}={safe[k]!r}" for k in sorted(safe))


class LoggingTracer(Tracer):
    """INFO logs: ``+`` / ``-`` lines with indentation for nesting and seconds on exit."""

    def __init__(self, logger: logging.Logger, *, verbose_attrs: bool = False) -> None:
        self._log = logger
        self._verbose_attrs = verbose_attrs
        self._depth = 0

    @contextmanager
    def start_span(self, name: str) -> Generator[LoggingTracerSpan, None, None]:
        indent = "  " * self._depth
        t0 = time.perf_counter()
        span = LoggingTracerSpan()
        self._log.info("%s+ graphiti:%s", indent, name)
        self._depth += 1
        try:
            yield span
        finally:
            self._depth -= 1
            indent = "  " * self._depth
            dt = time.perf_counter() - t0
            always_attrs = self._verbose_attrs or name in (
                "llm.generate",
                "add_episode",
                "add_episode_bulk",
            )
            suffix = _format_attrs(span.attrs, verbose=self._verbose_attrs) if always_attrs else ""
            self._log.info("%s- graphiti:%s %.3fs%s", indent, name, dt, suffix)
