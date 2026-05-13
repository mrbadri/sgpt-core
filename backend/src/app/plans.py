"""Plan definitions, pricing, and LLM token cost constants."""

from __future__ import annotations

PLAN_CONFIG: dict[str, dict] = {
    "free":  {"label": "رایگان 🆓",   "budget_usd": 0.2},
    "basic": {"label": "پایه 🥈",     "budget_usd": 2.00},
    "pro":   {"label": "حرفه‌ای 🥇",  "budget_usd": 8.00},
}

# (plan_key, duration_months) → price in IRR
PLAN_PRICES: dict[tuple[str, int], int] = {
    ("basic", 1): 1_000,
    ("basic", 3): 299_000,
    ("pro",   1): 600_000,
    ("pro",   3): 1500_000,
}

# USD per 1M tokens — adjust to match actual deployed model
INPUT_COST_PER_1M: float  = 0.5
OUTPUT_COST_PER_1M: float = 3.0
