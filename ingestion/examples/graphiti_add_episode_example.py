"""Add a single Graphiti episode to validate Neo4j, LLM, and embeddings.

Needs the same variables as ``ingestion.config.graphiti`` (for example ``GAPGPT_API_KEY``,
``NEO4J_URI``, ``NEO4J_USER``, ``NEO4J_PASSWORD``). Optional overrides: ``GEMINI_BASE_URL``,
``LLM_BASE_URL``, ``LLM_MODEL``.

From the repository root::

    uv run python ingestion/examples/graphiti_add_episode_example.py
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from graphiti_core.nodes import EpisodeType

from ingestion.config.graphiti import create_graphiti

GROUP_ID = "example-demo"


async def main() -> None:
    graphiti = create_graphiti()
    try:
        await graphiti.build_indices_and_constraints()
        result = await graphiti.add_episode(
            name="hello-world",
            episode_body=(
                "Acme Corp released Widget X in March 2024. "
                "The CTO is Dana Smith."
            ),
            source_description="manual smoke test",
            reference_time=datetime.now(UTC),
            source=EpisodeType.message,
            group_id=GROUP_ID,
        )
        print("Episode UUID:", result.episode.uuid)
        print("Entity nodes extracted:", len(result.nodes))
        print("Entity edges extracted:", len(result.edges))
    finally:
        await graphiti.close()


if __name__ == "__main__":
    asyncio.run(main())
