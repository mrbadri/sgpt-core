"""OpenAI-style reranker for strict OpenAI-compatible gateways.

Upstream ``OpenAIRerankerClient`` uses ``logit_bias`` plus ``logprobs`` / ``top_logprobs``
to score passages. Many gateways reject one or more of these parameters.

This implementation asks for a one-word **True** / **False** answer and scores from
plain ``message.content`` only — no ``logit_bias``, ``logprobs``, or ``top_logprobs``.
"""

from __future__ import annotations

import logging
from typing import Any

import openai

from graphiti_core.cross_encoder.openai_reranker_client import (
    DEFAULT_MODEL,
    OpenAIRerankerClient,
)
from graphiti_core.helpers import semaphore_gather
from graphiti_core.llm_client import RateLimitError
from graphiti_core.prompts import Message

logger = logging.getLogger(__name__)


def _boolean_score_from_text(content: str | None) -> float:
    """Map completion text to [0, 1]; prefers first token True/False."""
    if not content or not (raw := content.strip()):
        return 0.0
    lowered = raw.lower()
    first = lowered.split()[0] if lowered.split() else ""
    if first.startswith("true"):
        return 1.0
    if first.startswith("false"):
        return 0.0
    # Rare gateway quirks (punctuation, localized wrappers)
    if "true" in lowered and "false" not in lowered[: min(12, len(lowered))]:
        return 0.75
    return 0.0


class OpenAIRerankerNoLogitBias(OpenAIRerankerClient):
    async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
        openai_messages_list: Any = [
            [
                Message(
                    role="system",
                    content=(
                        "You are an expert tasked with determining whether the passage "
                        "is relevant to the query. Reply with exactly one word: True or False."
                    ),
                ),
                Message(
                    role="user",
                    content=f"""
                           Is PASSAGE relevant to QUERY? Answer True or False only.
                           <PASSAGE>
                           {passage}
                           </PASSAGE>
                           <QUERY>
                           {query}
                           </QUERY>
                           """,
                ),
            ]
            for passage in passages
        ]
        try:
            responses = await semaphore_gather(
                *[
                    self.client.chat.completions.create(
                        model=self.config.model or DEFAULT_MODEL,
                        messages=openai_messages,
                        temperature=0,
                        max_tokens=8,
                    )
                    for openai_messages in openai_messages_list
                ]
            )

            scores = [
                _boolean_score_from_text(r.choices[0].message.content) for r in responses
            ]
            results = [(passage, score) for passage, score in zip(passages, scores, strict=True)]
            results.sort(reverse=True, key=lambda x: x[1])
            return results
        except openai.RateLimitError as e:
            raise RateLimitError from e
        except Exception as e:
            logger.error("Error in generating LLM response: %s", e)
            raise
