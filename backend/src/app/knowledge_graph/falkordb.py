"""Falkor connection for Graphiti; optional query timeout for heavy RediSearch."""

from __future__ import annotations

import logging
import os
from typing import Any, cast

from falkordb.asyncio.graph import AsyncGraph
from graphiti_core.driver.falkordb_driver import FalkorDriver as _UpstreamFalkorDriver
from graphiti_core.utils.datetime_utils import convert_datetimes_to_strings

from app.config.graphiti import get_graphiti_settings

logger = logging.getLogger(__name__)

_DEFAULT_QUERY_TIMEOUT_MS = 300_000


def _query_timeout_ms_from_env() -> int | None:
    """Return timeout for ``graph.query`` (mirrors ingestion ``falkordb`` module)."""

    raw = os.getenv("FALKOR_QUERY_TIMEOUT_MS", "").strip()
    if not raw:
        return _DEFAULT_QUERY_TIMEOUT_MS
    try:
        v = int(raw, 10)
    except ValueError:
        logger.warning(
            "FALKOR_QUERY_TIMEOUT_MS=%r invalid; using default %sms",
            raw,
            _DEFAULT_QUERY_TIMEOUT_MS,
        )
        return _DEFAULT_QUERY_TIMEOUT_MS
    if v == 0:
        return None
    if v < 0:
        logger.warning(
            "FALKOR_QUERY_TIMEOUT_MS=%r invalid; using default %sms",
            raw,
            _DEFAULT_QUERY_TIMEOUT_MS,
        )
        return _DEFAULT_QUERY_TIMEOUT_MS
    return v


class FalkorDriver(_UpstreamFalkorDriver):
    """Falkor driver with per-query ``GRAPH.QUERY`` timeout."""

    def __init__(self, *, query_timeout_ms: int | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self._query_timeout_ms = query_timeout_ms

    async def execute_query(self, cypher_query_, **kwargs: Any):
        graph = cast(AsyncGraph, self._get_graph(self._database))
        params = cast(dict[str, object], convert_datetimes_to_strings(dict(kwargs)))
        timeout = self._query_timeout_ms
        try:
            # Async client: query is a coroutine; timeout is GRAPH.QUERY timeout in ms.
            result = await graph.query(cypher_query_, params, timeout=timeout)
        except Exception as e:
            if "already indexed" in str(e):
                logger.info("Index already exists: %s", e)
                return None
            logger.error("Error executing FalkorDB query: %s\n%s\n%s", e, cypher_query_, params)
            raise

        header = [h[1] for h in result.header]
        records = []
        for row in result.result_set:
            record = {}
            for i, field_name in enumerate(header):
                record[field_name] = row[i] if i < len(row) else None
            records.append(record)

        return records, header, None


def create_falkor_driver() -> FalkorDriver:
    """Return a Falkor driver for the configured graph."""

    s = get_graphiti_settings()
    return FalkorDriver(
        host=s.falkor_host,
        port=s.falkor_port,
        database=s.falkor_database,
        query_timeout_ms=_query_timeout_ms_from_env(),
    )
