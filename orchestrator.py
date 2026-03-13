"""
Orchestrator — the general contractor + procurement agent.

Step 1: Decompose the task into typed subtasks
Step 2: For each subtask, shop the model registry and assign the best model
Step 3: After all subtasks complete, synthesize into final deliverable
"""
import os
import json
from openai import OpenAI
from model_registry import pick_model, estimate_cost, MODELS
import providers

_client = OpenAI(
    api_key=os.environ.get("DO_API_KEY", ""),
    base_url="https://inference.do-ai.run/v1"
)
ORCHESTRATOR_MODEL = "claude-sonnet-4-6"

DECOMPOSE_PROMPT = """You are a project orchestrator managing a multi-model AI pipeline.
You have access to specialist models across providers (Anthropic, OpenAI, Google).

Available task types: brainstorm, research, outline, write, code, edit, summarize

Given a task and budget, decompose into the optimal set of subtasks.
Each subtask should have a DIFFERENT focus. Chain them so later subtasks can use earlier outputs.
Assign estimated_tokens (how much output you expect, 200-1500).

Return ONLY valid JSON:
{
  "project_summary": "one sentence",
  "subtasks": [
    {
      "id": 1,
      "type": "brainstorm",
      "task": "specific instruction",
      "estimated_tokens": 600,
      "priority": "balanced"
    }
  ]
}

priority options: "quality" | "cost" | "balanced"
Use "quality" for the most important subtasks, "cost" for simple ones."""

SPECIALIST_PROMPTS = {
    "brainstorm":  "You are a creative thinker and ideation expert. Generate novel, specific, well-reasoned ideas. Push beyond the obvious. Be creative and bold.",
    "research":    "You are a research analyst. Find relevant facts, studies, frameworks, and evidence. Be specific — cite real concepts, researchers, and data where possible.",
    "outline":     "You are a technical writer and document architect. Create clear, logical, hierarchical outlines. Every section should have a clear purpose.",
    "write":       "You are an expert writer. Produce polished, publication-ready prose. Be specific, not generic. No filler. Every sentence earns its place.",
    "code":        "You are a senior software engineer. Write clean, working, well-commented code. Include usage examples. Prefer clarity over cleverness.",
    "edit":        "You are a world-class editor. Improve clarity, flow, and impact. Cut what's weak. Sharpen what's strong. Return the improved version.",
    "summarize":   "You are an expert at distillation. Extract the key insights and present them clearly and concisely. Preserve nuance, cut padding.",
}


def decompose_and_assign(task: str, budget_usd: float) -> dict:
    """
    Decompose the task into subtasks and assign the best model to each.
    Returns the full execution plan with model assignments and cost estimates.
    """
    resp = _client.chat.completions.create(
        model=ORCHESTRATOR_MODEL,
        max_tokens=1500,
        messages=[
            {"role": "system", "content": DECOMPOSE_PROMPT},
            {"role": "user",   "content": f"Task: {task}\nBudget: ${budget_usd:.2f} USD"},
        ],
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    plan = json.loads(raw.strip())

    # Shop models for each subtask
    budget_remaining = budget_usd
    assigned = []
    for s in plan["subtasks"]:
        model = pick_model(s["type"], budget_remaining, s.get("priority", "balanced"))

        # Fall back to anthropic if provider not configured
        if not providers.provider_available(model["provider"]):
            fallback = {name: spec for name, spec in MODELS.items()
                       if spec["provider"] == "anthropic" and s["type"] in spec["quality"]}
            if fallback:
                name = max(fallback, key=lambda n: fallback[n]["quality"][s["type"]])
                model = {"name": name, **fallback[name]}

        est_cost = estimate_cost(model["name"], s.get("estimated_tokens", 800))
        budget_remaining -= est_cost

        assigned.append({
            **s,
            "model_name":   model["name"],
            "model_id":     model["model_id"],
            "provider":     model["provider"],
            "est_cost_usd": round(est_cost, 5),
            "model_spec":   model,
        })

    return {
        "project_summary": plan["project_summary"],
        "subtasks": assigned,
        "total_estimated_cost": round(sum(s["est_cost_usd"] for s in assigned), 5),
    }


def run_subtask(subtask: dict, context: str = "") -> str:
    """Execute a single subtask using its assigned model."""
    system = SPECIALIST_PROMPTS.get(subtask["type"],
                                    "You are a helpful AI. Complete the task thoroughly.")
    user = subtask["task"]
    if context:
        user = f"Previous work from the team:\n{context}\n\n---\nYour task:\n{subtask['task']}"

    text, _ = providers.call(subtask["model_spec"], system, user,
                             max_tokens=subtask.get("estimated_tokens", 1000))
    return text


def synthesize(task: str, subtask_results: list[dict]) -> str:
    """Combine all specialist outputs into the final deliverable."""
    results_text = "\n\n".join(
        f"[{r['type'].upper()} via {r['model_name']}]\n{r['output']}"
        for r in subtask_results
    )
    resp = _client.chat.completions.create(
        model=ORCHESTRATOR_MODEL,
        max_tokens=3000,
        messages=[
            {"role": "system", "content": (
                "You are a senior editor and project lead. "
                "Synthesize the work of your specialist team into one cohesive, "
                "polished final deliverable. Maintain all substance. Cut repetition. "
                "Format clearly with headers where appropriate."
            )},
            {"role": "user", "content": f"Original task: {task}\n\nSpecialist outputs:\n\n{results_text}"},
        ],
    )
    return resp.choices[0].message.content
