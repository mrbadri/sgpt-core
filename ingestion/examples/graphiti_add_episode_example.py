"""Add a single Graphiti episode to validate Neo4j, LLM, and embeddings.

Needs the same variables as ``ingestion.config.graphiti``: ``NEO4J_URI``, ``NEO4J_USER``,
``NEO4J_PASSWORD``. For API access set ``GAPGPT_API_KEY`` and/or ``LLM_API_KEY`` and
``EMBEDDING_API_KEY``. Embedding defaults come from ``ingestion.lib.embedding`` (``.env``
keys ``EMBEDDING_*``, ``GEMINI_BASE_URL``, ``LLM_*``).

From the repository root::

    uv sync   # installs this project editable (imports work without PYTHONPATH hacks)
    uv run python -m ingestion.examples.graphiti_add_episode_example
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

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
