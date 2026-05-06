"""Falkor connection for Graphiti; no LLM/embedder deps (safe to import anywhere)."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from graphiti_core.driver.falkordb_driver import FalkorDriver

load_dotenv()

# Graph naming: clone driver uses ``database=group_id`` when it differs from default graph.
FALKOR_DATABASE = os.getenv("FALKOR_DATABASE", "exp_g11_bio_1404_4o_mini")
FALKOR_HOST = os.getenv("FALKOR_HOST", "45.90.74.242")
FALKOR_PORT = int(os.getenv("FALKOR_PORT", "7379"))


def create_falkor_driver() -> FalkorDriver:
    """Return a Falkor driver for the configured graph.

    Call this **outside** ``asyncio.run`` / any running loop so ``FalkorDriver`` does
    not spawn ``build_indices_and_constraints`` as a fire-and-forget task (that task
    can race ``close()`` and log connection errors).
    """
    return FalkorDriver(host=FALKOR_HOST, port=FALKOR_PORT, database=FALKOR_DATABASE)
