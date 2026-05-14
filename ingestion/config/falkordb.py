"""Falkor connection for Graphiti; no LLM/embedder deps (safe to import anywhere)."""

from __future__ import annotations

import logging
import os
from typing import Any

from config.repo_env import load_repo_dotenv
from graphiti_core.driver.falkordb_driver import FalkorDriver as _UpstreamFalkorDriver
from graphiti_core.utils.datetime_utils import convert_datetimes_to_strings

load_repo_dotenv()

logger = logging.getLogger(__name__)

# Graph naming: clone driver uses ``database=group_id`` when it differs from default graph.
FALKOR_DATABASE = os.getenv("FALKOR_DATABASE", "exp_g11_bio_1404_5_mini_stv6")
FALKOR_HOST = os.getenv("FALKOR_HOST", "45.90.74.242")
FALKOR_PORT = int(os.getenv("FALKOR_PORT", "7379"))


# Client-side ``GRAPH.QUERY … timeout`` (ms). Heavy RediSearch fulltext during ingest often exceeds Falkor defaults.
_DEFAULT_QUERY_TIMEOUT_MS = 300_000  # 5 minutes when env unset


def _query_timeout_ms_from_env() -> int | None:
    """Return timeout for ``graph.query``. Unset env → default; ``0`` → omit timeout (server default only)."""

    raw = os.getenv("FALKOR_QUERY_TIMEOUT_MS", "").strip()
    if not raw:
        return _DEFAULT_QUERY_TIMEOUT_MS
    try:
        v = int(raw, 10)
    except ValueError:
        logger.warning(
            "FALKOR_QUERY_TIMEOUT_MS=%r invalid; using default %sms", raw, _DEFAULT_QUERY_TIMEOUT_MS
        )
        return _DEFAULT_QUERY_TIMEOUT_MS
    if v == 0:
        return None
    if v < 0:
        logger.warning(
            "FALKOR_QUERY_TIMEOUT_MS=%r invalid; using default %sms", raw, _DEFAULT_QUERY_TIMEOUT_MS
        )
        return _DEFAULT_QUERY_TIMEOUT_MS
    return v


FALKOR_QUERY_TIMEOUT_MS = _query_timeout_ms_from_env()


class FalkorDriver(_UpstreamFalkorDriver):
    """Falkor driver with per-query ``GRAPH.QUERY`` timeout (see ``FALKOR_QUERY_TIMEOUT_MS``)."""

    def __init__(self, *, query_timeout_ms: int | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self._query_timeout_ms = query_timeout_ms

    async def execute_query(self, cypher_query_, **kwargs: Any):
        graph = self._get_graph(self._database)
        params = convert_datetimes_to_strings(dict(kwargs))
        timeout = self._query_timeout_ms
        try:
            if timeout is not None:
                result = await graph.query(cypher_query_, params, timeout=timeout)
            else:
                result = await graph.query(cypher_query_, params)
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
    """Return a Falkor driver for the configured graph.

    Call this **outside** ``asyncio.run`` / any running loop so ``FalkorDriver`` does
    not spawn ``build_indices_and_constraints`` as a fire-and-forget task (that task
    can race ``close()`` and log connection errors).
    """
    return FalkorDriver(
        host=FALKOR_HOST,
        port=FALKOR_PORT,
        database=FALKOR_DATABASE,
        query_timeout_ms=FALKOR_QUERY_TIMEOUT_MS,
    )
