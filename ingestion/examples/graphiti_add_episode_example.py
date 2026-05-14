"""Add a single Graphiti episode to validate Neo4j, LLM, and embeddings.

Needs the same variables as ``ingestion.config.graphiti``: FalkorDB / Neo4j connection
vars and Graphiti indexing API keys: ``GRAPHITI_INDEX_LLM_*``,
``GRAPHITI_INDEX_EMBEDDING_*``, and optionally ``GRAPHITI_INDEX_RERANKER_*`` (see ``.env.example``).
Other ingestion helpers may use ``EMBEDDING_*`` separately.

From the repository root::

    uv sync   # installs this project editable (imports work without PYTHONPATH hacks)
    uv run python -m ingestion.examples.graphiti_add_episode_example
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from graphiti_core.nodes import EpisodeType

from ingestion.config.graphiti import create_graphiti

GROUP_ID = "exp_g11_bio_chapter_3_4o"


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
