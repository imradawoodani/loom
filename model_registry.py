"""
Model Registry — all models available through DigitalOcean Gradient.

One DO API key gives you access to all of these.
Costs are approximate DO pricing per 1k tokens.

Quality scores (1-10) per task type reflect each model's strengths.
The orchestrator uses these to pick the best model per subtask
given budget and priority (quality | cost | balanced).
"""

MODELS = {
    # ── Anthropic via DO ──────────────────────────────────────────────────────
    "claude-haiku": {
        "provider":           "anthropic",
        "model_id":           "claude-haiku-4-5-20251001",
        "cost_per_1k_tokens": 0.0008,
        "quality": {
            "outline":    8,
            "summarize":  8,
            "edit":       7,
            "brainstorm": 6,
            "research":   6,
            "write":      7,
            "code":       7,
        },
        "description": "Fast, cheap Claude. Great for structured tasks and outlines.",
    },
    "claude-sonnet": {
        "provider":           "anthropic",
        "model_id":           "claude-sonnet-4-6",
        "cost_per_1k_tokens": 0.003,
        "quality": {
            "outline":    9,
            "write":      9,
            "code":       10,
            "edit":       9,
            "research":   8,
            "brainstorm": 8,
            "summarize":  9,
        },
        "description": "Best Claude. Writing, code, complex reasoning.",
    },
    "claude-opus": {
        "provider":           "anthropic",
        "model_id":           "claude-opus-4-6",
        "cost_per_1k_tokens": 0.015,
        "quality": {
            "write":      10,
            "research":   10,
            "brainstorm": 10,
            "edit":       10,
            "outline":    9,
            "code":       10,
            "summarize":  10,
        },
        "description": "Most powerful Claude. Use only when quality is critical.",
    },

    # ── OpenAI via DO ─────────────────────────────────────────────────────────
    "gpt-4o-mini": {
        "provider":           "openai",
        "model_id":           "gpt-4o-mini",
        "cost_per_1k_tokens": 0.00015,
        "quality": {
            "brainstorm": 9,
            "research":   7,
            "outline":    7,
            "summarize":  8,
            "write":      7,
            "edit":       7,
        },
        "description": "Cheapest capable model. Excellent brainstorming and ideation.",
    },
    "gpt-4o": {
        "provider":           "openai",
        "model_id":           "gpt-4o",
        "cost_per_1k_tokens": 0.005,
        "quality": {
            "brainstorm": 10,
            "write":       9,
            "edit":       10,
            "research":    9,
            "outline":     9,
            "code":        9,
            "summarize":   9,
        },
        "description": "Top OpenAI model. Best at creative brainstorming and editing.",
    },

    # ── Meta via DO ───────────────────────────────────────────────────────────
    "llama-3.3-70b": {
        "provider":           "meta",
        "model_id":           "meta-llama/Llama-3.3-70B-Instruct",
        "cost_per_1k_tokens": 0.00059,
        "quality": {
            "research":   8,
            "brainstorm": 8,
            "outline":    7,
            "write":      7,
            "summarize":  8,
            "code":       7,
        },
        "description": "Open-source powerhouse. Great research and summarization.",
    },
    "llama-3.1-8b": {
        "provider":           "meta",
        "model_id":           "meta-llama/Llama-3.1-8B-Instruct",
        "cost_per_1k_tokens": 0.0001,
        "quality": {
            "summarize":  7,
            "outline":    6,
            "brainstorm": 6,
            "research":   6,
        },
        "description": "Ultra-cheap open-source. Good for simple summarization tasks.",
    },

    # ── Mistral via DO ────────────────────────────────────────────────────────
    "mistral-small": {
        "provider":           "mistral",
        "model_id":           "mistral-small-latest",
        "cost_per_1k_tokens": 0.0002,
        "quality": {
            "code":       8,
            "outline":    7,
            "summarize":  7,
            "research":   7,
            "write":      7,
        },
        "description": "Cheap Mistral. Solid at code and structured outputs.",
    },
}

PROVIDER_COLORS = {
    "anthropic": "orange3",
    "openai":    "green3",
    "meta":      "purple",
    "mistral":   "cyan",
}
PROVIDER_LABELS = {
    "anthropic": "🟠 Anthropic",
    "openai":    "🟢 OpenAI",
    "meta":      "🟣 Meta",
    "mistral":   "🔵 Mistral",
}

TASK_TYPES = ["brainstorm", "research", "outline", "write", "code", "edit", "summarize"]


def pick_model(task_type: str, budget_remaining: float,
               priority: str = "balanced") -> dict:
    """
    Select the best model for a task given budget and priority.

    priority:
      "quality"  — best output regardless of cost
      "cost"     — cheapest model that can do the job
      "balanced" — best quality-per-dollar ratio
    """
    candidates = {
        name: spec for name, spec in MODELS.items()
        if task_type in spec["quality"]
        and spec["cost_per_1k_tokens"] * 2 < max(budget_remaining, 0.01)
    }
    if not candidates:
        candidates = {n: s for n, s in MODELS.items() if task_type in s["quality"]}
    if not candidates:
        raise ValueError(f"No model found for task type: {task_type}")

    if priority == "quality":
        chosen = max(candidates, key=lambda n: candidates[n]["quality"][task_type])
    elif priority == "cost":
        chosen = min(candidates, key=lambda n: candidates[n]["cost_per_1k_tokens"])
    else:  # balanced
        chosen = max(
            candidates,
            key=lambda n: candidates[n]["quality"][task_type]
                          / (candidates[n]["cost_per_1k_tokens"] * 1000 + 0.001)
        )

    return {"name": chosen, **candidates[chosen]}


def estimate_cost(model_name: str, estimated_tokens: int = 800) -> float:
    model = MODELS.get(model_name, {})
    return model.get("cost_per_1k_tokens", 0.001) * estimated_tokens / 1000
