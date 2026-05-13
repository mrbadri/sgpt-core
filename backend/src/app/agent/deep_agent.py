"""Deep Agents (LangGraph) with a Graphiti search tool and a minimal, safer tool surface."""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Any, cast

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends.protocol import BACKEND_TYPES
from deepagents.profiles.harness.harness_profiles import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    register_harness_profile,
)
from langchain.agents import AgentState
from langchain.agents.middleware.tool_call_limit import ToolCallLimitMiddleware
from langchain.agents.middleware.types import AgentMiddleware
from langchain.chat_models import BaseChatModel, init_chat_model
from langgraph.types import Checkpointer

from app.agent.graphiti_tool import build_graphiti_batch_search_tool, build_graphiti_search_tool
from app.agent.prompts import DEFAULT_SYSTEM_PROMPT
from app.agent.format_response import AgentResponse

_harness_profiles_registered = False


def _env_first_nonempty(*names: str) -> str | None:
    """Return the first trimmed, non-empty value among the given env var names."""

    for name in names:
        value = (os.getenv(name) or "").strip()
        if value:
            return value
    return None


def _ensure_graphiti_harness_profiles() -> None:
    """Strip high-risk default tools (shell, filesystem writes, subagents) for this app."""

    global _harness_profiles_registered
    if _harness_profiles_registered:
        return
    profile = HarnessProfile(
        excluded_tools=frozenset(
            {
                "execute",
                "write_file",
                "edit_file",
                "task",
                "ls",
                "read_file",
                "glob",
                "grep",
                "write_todos",
            }
        ),
        general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
    )
    for key in (
        "openai",
        "anthropic",
        "google_vertexai",
        "google_genai",
    ):
        register_harness_profile(key, profile)
    _harness_profiles_registered = True




def build_graphiti_deep_agent(
    *,
    model: BaseChatModel | None = None,
    system_prompt: str | None = None,
    max_episode_chars: int = 1500,
    max_tool_calls_per_run: int = 1,
    user_id: str | None = None,
    user_memories_dir: str | None = None,
    memory: list[str] | None = None,
    checkpointer: Checkpointer | None = None,
    backend: BACKEND_TYPES | None = None,
):
    """Return a compiled LangGraph deep agent with Graphiti search tools.

    **Long-term memory (Markdown)**

    - With the default ``StateBackend`` (no ``backend``), ``memory`` paths refer
      to keys in LangGraph ``files`` state — preload on ``invoke`` with a
      ``files`` dict, or the middleware skips missing keys.
    - For **one file per learner on disk**, pass ``user_id`` plus
      ``user_memories_dir`` or env ``USER_MEMORIES_DIR``. That sets
      ``FilesystemBackend(root_dir=..., virtual_mode=True)`` and ``memory=["user_<id>.md"]``
      (path **relative** to ``root_dir``, sandboxed under that directory). Example on disk:
      ``{USER_MEMORIES_DIR}/user_alice.md``.
    - Alternatively pass ``backend`` + ``memory`` yourself (e.g. custom store).

    If you pass ``user_id``, do not pass ``memory`` or ``backend`` — use one style only.

    **Short-term memory (checkpoints)**

    Pass a LangGraph ``checkpointer`` and reuse the same ``thread_id`` in
    ``config["configurable"]`` for the same chat session / learner.

    Summarization is already inside ``create_deep_agent``; do not add
    ``create_summarization_middleware`` again in ``middleware``.

    This app’s harness excludes ``edit_file`` / ``write_file``; update learner
    markdown from your API if the model cannot write memory itself.
    """

    _ensure_graphiti_harness_profiles()

    if model is not None:
        resolved_model = model
    else:
        agent_model = _env_first_nonempty("AGENT_CHAT_MODEL", "GRAPHITI_INDEX_LLM_MODEL")
        agent_api_key = _env_first_nonempty(
            "AGENT_CHAT_API_KEY",
            "GAPGPT_API_KEY",
            "GRAPHITI_INDEX_LLM_API_KEY",
        )
        agent_base_url = _env_first_nonempty(
            "AGENT_CHAT_BASE_URL",
            "GRAPHITI_INDEX_LLM_BASE_URL",
            "GEMINI_BASE_URL",
        )
        agent_temperature = float(os.getenv("AGENT_CHAT_TEMPERATURE", 0.1))
        agent_max_tokens = int(os.getenv("AGENT_CHAT_MAX_TOKENS", 4096))

        if not agent_model or not agent_api_key or not agent_base_url:
            raise ValueError(
                "Set AGENT_CHAT_MODEL / AGENT_CHAT_API_KEY / AGENT_CHAT_BASE_URL, or pass "
                "model=... explicitly. When unset, the agent falls back (in order) to "
                "GRAPHITI_INDEX_LLM_* and GAPGPT_API_KEY plus GEMINI_BASE_URL."
            )

        resolved_model = init_chat_model(
            model=agent_model,
            model_provider="openai",
            api_key=agent_api_key,
            base_url=agent_base_url,
            temperature=agent_temperature,
            max_tokens=agent_max_tokens,
        )

    tools = [
        build_graphiti_search_tool(max_episode_chars=max_episode_chars),
        build_graphiti_batch_search_tool(max_episode_chars=max_episode_chars),
    ]

    limiter = ToolCallLimitMiddleware(run_limit=max_tool_calls_per_run)
    extra_middleware: Sequence[AgentMiddleware[AgentState[Any], Any, Any]] = cast(
        Sequence[AgentMiddleware[AgentState[Any], Any, Any]],
        [limiter],
    )

    resolved_memory = memory
    resolved_backend = backend
    if user_id is not None:
        if memory is not None or backend is not None:
            raise ValueError("Use either user_id (+ user_memories_dir / USER_MEMORIES_DIR) or memory/backend, not both.")
        mem_root = (user_memories_dir or _env_first_nonempty("USER_MEMORIES_DIR") or "").strip()
        if not mem_root:
            raise ValueError(
                "user_id requires user_memories_dir=... or USER_MEMORIES_DIR pointing at the memories directory."
            )
        resolved_backend = FilesystemBackend(root_dir=mem_root, virtual_mode=True)
        resolved_memory = [f"user_{user_id}.md"]

    return create_deep_agent(
        model=resolved_model,
        tools=tools,
        system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
        middleware=extra_middleware,
        memory=resolved_memory,
        checkpointer=checkpointer,
        backend=resolved_backend,
        response_format=AgentResponse,
    )


agent = build_graphiti_deep_agent()
