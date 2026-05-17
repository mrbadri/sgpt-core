# Deep Agent Redesign — Cost-Optimized, Async Expert Sub-Agents, Tone Control

> **Goal:** Lowest cost · Split prompt system · Expert async sub-agents · Per-feature response format · Faster response · Tone of voice selection

---

## 1. Problems in Current Architecture

| Problem | Impact |
|---------|--------|
| Single monolithic `DEFAULT_SYSTEM_PROMPT` (all rules in every call) | Max token usage, no caching benefit |
| `max_tool_calls_per_run=1` hard-coded globally | Blocks parallel sub-topic searches |
| Single agent handles all request types (teaching, exam, welcome, simple) | No specialization, always pays full system prompt cost |
| No tone selection — one fixed `TONE_AND_STYLE` block | Can't personalize per user preference |
| `header` field generated but never rendered | Wasted output tokens every response |
| Memory prepended as raw text on every message | Grows unbounded, never summarized |
| No model tier routing (cheap model for simple, expensive for teaching) | Always pays premium model price |

---

## 2. New Architecture Overview

```mermaid
flowchart TB
    subgraph Input["Input Layer"]
        User["User Message"]
        Profile["User Profile\n(tone, level, plan)"]
        Memory["Memory Block\n(summarized markdown)"]
    end

    subgraph Router["Router Agent (cheap model)"]
        Classify["Intent Classifier\n• teaching\n• exam\n• simple\n• welcome\n• off-topic"]
        ToneSelect["Tone Resolver\n• formal / semi-formal\n• casual / slang\n• user preference override"]
        PromptBuilder["Prompt Builder\n(assembles only needed blocks)"]
    end

    subgraph Experts["Expert Sub-Agents (async parallel)"]
        TeachAgent["🎓 Teaching Agent\n(full prompt + KG)"]
        ExamAgent["📝 Exam Agent\n(exam-only prompt + KG)"]
        SimpleAgent["💬 Simple Agent\n(minimal prompt, no KG)"]
        WelcomeAgent["👋 Welcome Agent\n(onboarding prompt)"]
    end

    subgraph KG["Knowledge Graph"]
        KGSearch["search_knowledge_graph\n(single query)"]
        KGBatch["search_knowledge_graph_batch\n(parallel queries)"]
    end

    subgraph Response["Response Formatter"]
        FormatTeach["TeachingResponse format"]
        FormatExam["ExamResponse format"]
        FormatSimple["SimpleResponse format"]
        FormatWelcome["WelcomeResponse format"]
        Render["Bale Renderer\n(markdown + buttons)"]
    end

    User --> Router
    Profile --> ToneSelect
    Memory --> PromptBuilder
    Classify --> PromptBuilder
    ToneSelect --> PromptBuilder
    PromptBuilder --> TeachAgent
    PromptBuilder --> ExamAgent
    PromptBuilder --> SimpleAgent
    PromptBuilder --> WelcomeAgent
    TeachAgent --> KGBatch
    ExamAgent --> KGBatch
    SimpleAgent -.->|"only if needed"| KGSearch
    TeachAgent --> FormatTeach
    ExamAgent --> FormatExam
    SimpleAgent --> FormatSimple
    WelcomeAgent --> FormatWelcome
    FormatTeach --> Render
    FormatExam --> Render
    FormatSimple --> Render
    FormatWelcome --> Render
```

---

## 3. Split Prompt System

Instead of one huge concatenated prompt, each agent gets only the blocks it needs.

```mermaid
graph LR
    subgraph Shared["Shared (cached)"]
        ID["BOT_IDENTITY"]
        MD["BALE_MARKDOWN_RULES"]
        KGI["KG_INSTRUCTIONS"]
        Scope["TEACHING_SCOPE"]
    end

    subgraph PerAgent["Per-Agent (injected once)"]
        ToneBlock["TONE_BLOCK\n(resolved per user)"]
        FormatBlock["RESPONSE_FORMAT\n(per response_type only)"]
    end

    subgraph PerRequest["Per-Request (dynamic)"]
        MemBlock["MEMORY_BLOCK\n(summarized, ≤300 tokens)"]
        CtxBlock["CONTEXT_BLOCK\n(exam result, pending Q)"]
    end

    Shared --> TeachingAgent
    Shared --> ExamAgent
    Shared --> SimpleAgent
    PerAgent --> TeachingAgent
    PerAgent --> ExamAgent
    PerAgent --> SimpleAgent
    PerRequest --> TeachingAgent
    PerRequest --> ExamAgent
    PerRequest --> SimpleAgent
```

### Prompt Block Sizes (target)

| Block | Tokens (approx) | Cached? |
|-------|-----------------|---------|
| `BOT_IDENTITY` | ~40 | ✅ yes |
| `BALE_MARKDOWN_RULES` | ~50 | ✅ yes |
| `TEACHING_SCOPE` | ~20 | ✅ yes |
| `KG_INSTRUCTIONS` | ~50 | ✅ yes |
| `TONE_BLOCK` (one variant) | ~80 | ✅ per tone variant |
| `RESPONSE_FORMAT` (per type) | ~60 | ✅ per type |
| `MEMORY_BLOCK` | ~200 | ❌ dynamic |
| `CONTEXT_BLOCK` | ~50 | ❌ dynamic |

**Current:** all blocks concatenated every call → ~500 tokens always in context  
**New:** shared blocks cached via LLM prefix cache; only dynamic blocks paid per call

---

## 4. Tone of Voice System

Users can choose or the system auto-detects their tone on first message.

```mermaid
stateDiagram-v2
    [*] --> AutoDetect: first message
    AutoDetect --> Formal: formal writing detected
    AutoDetect --> SemiFormal: neutral detected
    AutoDetect --> Casual: slang/informal detected
    Formal --> UserOverride: user says "راحت‌تر باش"
    Casual --> UserOverride: user says "رسمی‌تر صحبت کن"
    UserOverride --> Saved: written to user memory
    Saved --> [*]: persists all sessions
```

### Tone Blocks

```python
TONE_BLOCKS = {
    "formal":       "رسمی، محترمانه، فاصله‌دار — مثل استاد دانشگاه",
    "semi_formal":  "دوستانه + حرفه‌ای — لحن ترکیبی",
    "casual":       "گرم، اسلنگ‌اوکی، مثل دوست صمیمی",
    "enthusiastic": "پرانرژی، تشویقی، واکنش‌پذیر",
}
```

Stored in user profile — not re-detected every call after first session.

---

## 5. Expert Async Sub-Agents

```mermaid
sequenceDiagram
    participant B as BaleAgentBridge
    participant R as Router Agent
    participant T as Teaching Agent
    participant K as Knowledge Graph
    participant F as Formatter

    B->>R: user message + profile
    Note over R: cheap model (haiku/mini)<br/>classify intent in ~200ms
    R-->>B: intent=teaching, tone=casual, topics=["میتوز","DNA"]
    B->>T: async launch with focused prompt
    T->>K: search_knowledge_graph_batch(["میتوز","DNA"])
    Note over K: parallel graph queries
    K-->>T: facts + chunks
    T-->>F: TeachingResponse (structured)
    F-->>B: rendered markdown + buttons
```

### Sub-Agent Configuration

| Agent | Model | `max_tool_calls` | KG Access | System Prompt Blocks |
|-------|-------|-------------------|-----------|----------------------|
| Router | haiku / gpt-4o-mini | 0 | ❌ | identity + classify rules |
| Teaching | full model | 3 | ✅ batch | identity + tone + teaching format + KG + scope |
| Exam | full model | 2 | ✅ batch | identity + tone + exam format + KG + scope |
| Simple | haiku / gpt-4o-mini | 0–1 | conditional | identity + tone + simple format |
| Welcome | full model | 0 | ❌ | identity + tone + welcome format |

---

## 6. Per-Feature Response Formats

Split `AgentResponse` into focused Pydantic models — no null-heavy single model.

```mermaid
classDiagram
    class TeachingResponse {
        +response_type: "teaching"
        +header: str
        +main_content: str
        +key_points: list[str]
        +fun_fact: str
        +next_questions: list[str]
    }
    class ExamResponse {
        +response_type: "exam"
        +header: str
        +intro: str
        +questions: list[ExamQuestion]
    }
    class SimpleResponse {
        +response_type: "simple"
        +main_content: str
        +next_questions: list[str] | None
    }
    class WelcomeResponse {
        +response_type: "welcome"
        +header: str
        +main_content: str
        +personality_note: str
        +starter_questions: list[str]
    }
    class ExamQuestion {
        +question: str
        +options: list[str]
        +correct_answer: str
        +explanation: str
    }
    ExamResponse --> ExamQuestion
```

Each agent's `response_format=` only includes fields it actually uses → fewer output tokens, no null fields, better structured output accuracy.

---

## 7. Cost Reduction Strategy

```mermaid
graph TD
    A["User Message"] --> B{Router classify}
    B -->|simple question| C["Simple Agent\ncheap model\nno KG\n~0.001¢"]
    B -->|teaching request| D["Teaching Agent\nfull model + KG\n~0.01¢"]
    B -->|exam request| E["Exam Agent\nfull model + KG\n~0.01¢"]
    B -->|off-topic| F["Rejection\ncheap model\n~0.0005¢"]

    style C fill:#90EE90
    style F fill:#90EE90
    style D fill:#FFD700
    style E fill:#FFD700
```

### Token Budget per Call

| Scenario | Current | New | Saving |
|----------|---------|-----|--------|
| Simple chat ("ممنون") | ~500 sys + ~200 out | ~150 sys + ~100 out | **~60%** |
| Teaching request | ~500 sys + ~400 out | ~350 sys (cached) + ~350 out | **~20%** |
| Exam (10 questions) | ~500 sys + ~800 out | ~300 sys (cached) + ~700 out | **~25%** |
| Off-topic rejection | ~500 sys + ~100 out | ~150 sys + ~80 out | **~70%** |

---

## 8. Faster Response Strategy

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bridge
    participant R as Router
    participant A as Expert Agent
    participant K as KG

    U->>B: message
    B->>U: "در حال بررسی..." (immediate)
    B->>R: classify (async, cheap, fast)
    R-->>B: intent + tone
    B->>U: "در حال جستجو..." (update)
    B->>A: launch agent
    A->>K: batch search (parallel)
    K-->>A: results
    A-->>B: structured response
    B->>U: full answer + buttons
```

**Optimizations:**
1. Router is cheap/fast → intent known in ~200ms
2. KG batch search runs parallel sub-queries
3. `on_thinking` callback fires immediately on first LLM token (already exists)
4. Simple responses skip KG entirely → no wait
5. Prompt cache hit on shared blocks → reduced TTFT

---

## 9. Memory Architecture

```mermaid
flowchart LR
    subgraph ShortTerm["Short-Term (per session)"]
        Check["LangGraph Checkpointer\nthread_id = user-{id}"]
    end

    subgraph LongTerm["Long-Term (cross-session)"]
        Raw["user_{id}.md\nraw memory file"]
        Summary["user_{id}_summary.md\n≤300 tokens summarized"]
    end

    subgraph Update["Memory Update (async, after response)"]
        Trigger["after teaching response"]
        Summarizer["Summarizer Agent\n(haiku, cheap)"]
    end

    Check --> Agent
    Summary --> Agent
    Raw --> Summarizer
    Trigger --> Summarizer
    Summarizer --> Summary
```

Instead of prepending the full raw memory file, prepend only the summarized version (≤300 tokens). Summarization runs async after response delivery — never blocks the user.

---

## 10. New Directory Structure

```
backend/src/app/agent/
├── router/
│   ├── intent_classifier.py      # cheap model, returns intent + tone
│   └── prompt_builder.py         # assembles blocks per intent
├── experts/
│   ├── teaching_agent.py         # teaching specialist
│   ├── exam_agent.py             # exam specialist
│   ├── simple_agent.py           # simple/quick replies
│   └── welcome_agent.py          # onboarding
├── prompts/
│   ├── shared.py                 # BOT_IDENTITY, BALE_MARKDOWN, KG, SCOPE
│   ├── tones.py                  # TONE_BLOCKS dict (4 variants)
│   └── formats.py                # per-type format instructions
├── response_models/
│   ├── teaching.py               # TeachingResponse
│   ├── exam.py                   # ExamResponse + ExamQuestion
│   ├── simple.py                 # SimpleResponse
│   └── welcome.py                # WelcomeResponse
├── memory/
│   ├── loader.py                 # load + summarize memory
│   └── writer.py                 # async memory update
├── graphiti_tool.py              # unchanged
└── langfuse.py                   # unchanged
```

---

## 11. Bridge Changes (`agent_bridge.py`)

```mermaid
flowchart TB
    Old["Current: single agent\nbuild_graphiti_deep_agent()"]
    New["New: router + dispatch"]

    New --> R["1. router.classify(message, profile)"]
    R --> P["2. prompt_builder.build(intent, tone, memory_summary)"]
    P --> D{"dispatch"}
    D --> TA["teaching_agent.invoke_async()"]
    D --> EA["exam_agent.invoke_async()"]
    D --> SA["simple_agent.invoke_async()"]
    D --> WA["welcome_agent.invoke_async()"]
```

```python
# New bridge invoke flow (sketch)
async def invoke_reply(self, user_id, message, callbacks):
    profile = await get_user_profile(user_id)
    memory = await load_memory_summary(user_id)          # ≤300 tokens
    intent = await self.router.classify(message, profile) # cheap model
    prompt = self.prompt_builder.build(intent, memory)
    agent = self.agents[intent.type]                      # pre-built, cached
    response = await agent.ainvoke(prompt, callbacks=callbacks)
    asyncio.create_task(update_memory(user_id, response)) # async, non-blocking
    return response
```

---

## 12. Tone Selection — User Flow

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bot

    U->>B: "میشه رسمی‌تر باهام صحبت کنی؟"
    B->>B: detect tone_change_request
    B->>B: update profile.tone = "formal"
    B->>B: save to user memory
    B->>U: "البته! از این به بعد رسمی‌تر صحبت می‌کنم."
    Note over B: all future prompts use TONE_BLOCKS["formal"]
```

**Tone trigger phrases:**
- `"رسمی‌تر باش"` / `"رسمی صحبت کن"` → `formal`
- `"راحت‌تر باش"` / `"دوستانه‌تر"` → `casual`
- `"انرژیک‌تر"` / `"با انگیزه‌تر"` → `enthusiastic`

---

## 13. Implementation Priority

```mermaid
gantt
    title Redesign Phases
    dateFormat  YYYY-MM-DD
    section Phase 1 - Cost Quick Wins
    Split prompt blocks        :p1a, 2026-05-17, 3d
    Simple agent cheap model   :p1b, 2026-05-20, 2d
    Router intent classifier   :p1c, 2026-05-22, 3d

    section Phase 2 - Expert Agents
    Split response models      :p2a, 2026-05-25, 2d
    Teaching expert agent      :p2b, 2026-05-27, 2d
    Exam expert agent          :p2c, 2026-05-29, 2d

    section Phase 3 - Tone and Memory
    Tone blocks and user profile :p3a, 2026-05-31, 2d
    Memory summarizer            :p3b, 2026-06-02, 2d
    Tone change detection        :p3c, 2026-06-04, 1d

    section Phase 4 - Polish
    Langfuse cost tracking     :p4a, 2026-06-05, 1d
    AB test prompt variants    :p4b, 2026-06-06, 2d
```

---

## 14. Key DeepAgents Advanced Features to Use

| Feature | Where to Apply |
|---------|----------------|
| **Prompt prefix caching** | All shared prompt blocks in expert agents |
| **`response_format=` per agent** | One focused Pydantic model per expert (no null fields) |
| **`ToolCallLimitMiddleware`** per agent | Teaching=3, Exam=2, Simple=1, Router=0 |
| **`FilesystemBackend`** | Memory summary files with `virtual_mode=True` |
| **Async `ainvoke`** | Router → dispatch → expert all async |
| **`astream_events` v2** | Keep existing streaming for UI callbacks |
| **`HarnessProfile` exclusions** | Keep current safe tool exclusions |
| **Separate checkpointer per agent type** | `thread_id` per agent type to avoid state bleed |

---

## 15. Summary — Current vs New

| Dimension | Current | New |
|-----------|---------|-----|
| Prompt system | 1 monolithic prompt | 6 composable blocks, only needed blocks sent |
| Agent count | 1 agent for all types | 1 router + 4 expert agents |
| Model routing | always full model | cheap model for router + simple; full for teaching/exam |
| Tone | fixed `TONE_AND_STYLE` block | 4 tone variants, user-selectable, persisted |
| Response model | 1 `AgentResponse` with many null fields | 4 focused models, zero null fields |
| KG calls per run | max 1 (middleware) | max 3 (teaching), 1 batch = many parallel queries |
| Memory | full raw file prepended | summarized ≤300 token block, async update |
| Cost (simple msg) | pays full model + full prompt | cheap model + minimal prompt (~60% cheaper) |
| Speed (simple msg) | full agent pipeline | router + simple agent, no KG (~50% faster) |

---

## 16. Skills — Useful in This Design

**Yes — Skills are a strong fit.** Instead of packing everything into one giant system prompt, each capability becomes a `SKILL.md` file. The agent reads only the frontmatter at startup (progressive disclosure), and only loads the full skill when the intent matches — saving tokens on every unrelated request.

### Skills to Create

| Skill | Trigger | What it adds |
|-------|---------|--------------|
| `biology-teaching` | user asks for a lesson | teaching format rules, KG search instructions, key_points structure |
| `exam-generator` | user asks for a test/quiz | exam format rules, ExamQuestion schema, difficulty guidance |
| `tone-manager` | user asks to change tone | tone variant descriptions, how to detect and apply each tone |
| `memory-recall` | user references past sessions | how to read and use summarized memory block |
| `onboarding` | `/start`, first message | welcome format, personality detection from profile photo |

```
backend/src/app/agent/
└── skills/
    ├── biology-teaching/
    │   └── SKILL.md
    ├── exam-generator/
    │   └── SKILL.md
    ├── tone-manager/
    │   └── SKILL.md
    ├── memory-recall/
    │   └── SKILL.md
    └── onboarding/
        └── SKILL.md
```

```python
# Pass skills dir to each expert agent
agent = create_deep_agent(
    model=resolved_model,
    tools=tools,
    system_prompt=BASE_SYSTEM_PROMPT,   # identity + markdown rules only (~90 tokens)
    skills=["src/app/agent/skills"],    # rest loaded on demand
    response_format=TeachingResponse,
)
```

**Token saving:** base system prompt drops from ~500 tokens to ~90 tokens. Skills load only when matched — teaching skill tokens only paid on teaching requests, never on simple replies.

---

## 17. Human-in-the-Loop — Clarifying Unclear Questions

**Yes — HIL is the right pattern when the router can't confidently classify intent.**

### When to Interrupt

```mermaid
flowchart TD
    A["User Message"] --> B{Router confidence}
    B -->|high confidence| C["Dispatch to expert agent"]
    B -->|low confidence\n< 0.7| D["HIL: clarify_intent tool"]
    D --> E{User responds}
    E -->|clarified| C
    E -->|ignored / timeout| F["Simple fallback response"]
```

### Implementation

```python
from deepagents import create_deep_agent
from langchain.tools import tool

@tool
def clarify_intent(question: str) -> str:
    """Ask the user a clarifying question when their request is ambiguous."""
    return question   # actual response comes from human interrupt

router_agent = create_deep_agent(
    model=cheap_model,
    tools=[clarify_intent],
    interrupt_on={
        "clarify_intent": {"allowed_decisions": ["respond"]},
        # "respond" = human types the answer directly as the tool result
    },
    checkpointer=checkpointer,   # required for HIL
    system_prompt=ROUTER_PROMPT,
)
```

### Scenarios Where HIL Helps

| Ambiguous Input | HIL Question | Result |
|----------------|-------------|--------|
| "تست بده" (could mean exam OR system test) | "آزمون زیست می‌خوای یا چیز دیگه؟" | routes correctly |
| "توضیح بده" (no topic given) | "کدوم مبحث زیست یازدهم؟" | teaching agent gets focused query |
| "یه چیز جالب بگو" (teaching? simple?) | no HIL — router picks `simple` at threshold 0.5 | avoids unnecessary interruption |

### HIL vs Auto-Clarify Threshold

```python
CLARIFY_THRESHOLD = 0.65   # router confidence below this → ask user
AUTO_SIMPLE_THRESHOLD = 0.5  # very low → just respond simply, don't interrupt
```

- **Above 0.65:** dispatch directly
- **0.5–0.65:** interrupt with one short clarifying question
- **Below 0.5:** treat as `simple`, respond without KG, no interruption

### Updated Architecture with Skills + HIL

```mermaid
flowchart TB
    subgraph Router["Router Agent (cheap model)"]
        Classify["Intent + confidence score"]
        HIL["clarify_intent tool\n(interrupt_on: respond)"]
    end

    subgraph Skills["Skills (progressive disclosure)"]
        S1["biology-teaching/SKILL.md"]
        S2["exam-generator/SKILL.md"]
        S3["tone-manager/SKILL.md"]
        S4["memory-recall/SKILL.md"]
        S5["onboarding/SKILL.md"]
    end

    subgraph Experts["Expert Agents"]
        T["Teaching Agent\n+ biology-teaching skill"]
        E["Exam Agent\n+ exam-generator skill"]
        S["Simple Agent\n(no skill needed)"]
        W["Welcome Agent\n+ onboarding skill"]
    end

    User["User Message"] --> Classify
    Classify -->|confidence >= 0.65| Experts
    Classify -->|confidence < 0.65| HIL
    HIL -->|user clarifies| Experts
    Skills --> T
    Skills --> E
    Skills --> W
```
