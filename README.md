# 🧵 Loom: Agent Marketplace

> **The agent that shops the AI market so you don't have to.**

Give Loom a task and a budget. It breaks the work into subtasks, shops across Claude, GPT, Llama, and Mistral for the best model per job, executes each one, and settles payment through HLOS. One deliverable. One receipt. Every model paid exactly what it earned.

**Most agents use one model. Loom runs a market.**

---

## How it works

```
You (task + budget)
    └── Orchestrator (Claude Sonnet)
            ├── Decomposes task into typed subtasks
            └── Shops model registry per subtask:
                    brainstorm  → gpt-4o-mini       cheap + creative
                    research    → llama-3.3-70b      open-source + thorough
                    outline     → claude-haiku       fast + structured
                    write       → claude-sonnet      quality prose
                    code        → mistral-small      clean + efficient
                    edit        → gpt-4o             fresh eyes
                    │
                    ▼
            HLOS: passport issued per agent
            HLOS: output notarized on completion
            HLOS: payment released per agent
                    │
                    ▼
            Orchestrator synthesizes → final deliverable
            HLOS receipt: tx ID + attestation + cost per model
```

---

## Stack

| Layer | Tool |
|---|---|
| Model access | DigitalOcean Gradient — one key, all providers |
| Orchestration | Claude Sonnet 4.6 |
| Identity & settlement | HLOS |
| Language | Python |

---

## Setup

**1. Install dependencies**
```bash
pip3 install openai requests rich python-dotenv
```

**2. Create a `.env` file in the project folder**
```bash
DO_API_KEY=dop_v1_...
HLOS_API_KEY=...
```

**3. Run**
```bash
python3 main.py
```

---

## Custom tasks

```bash
TASK="Build a go-to-market strategy for a developer tool" BUDGET=1.50 python3 main.py
TASK="Write a technical deep-dive on transformer attention" BUDGET=2.00 python3 main.py
TASK="Analyze the competitive landscape for AI coding tools" BUDGET=1.00 python3 main.py
```

---

## Models available

All accessed through a single DigitalOcean API key.

| Model | Provider | Best at | Cost/1k |
|---|---|---|---|
| claude-haiku | 🟠 Anthropic | outlines, fast tasks | $0.0008 |
| claude-sonnet | 🟠 Anthropic | writing, code | $0.003 |
| claude-opus | 🟠 Anthropic | highest quality | $0.015 |
| gpt-4o-mini | 🟢 OpenAI | brainstorming | $0.00015 |
| gpt-4o | 🟢 OpenAI | editing, ideation | $0.005 |
| llama-3.3-70b | 🟣 Meta | research | $0.00059 |
| mistral-small | 🔵 Mistral | code, structure | $0.0002 |

---

## Files

| File | Purpose |
|---|---|
| `main.py` | Entry point, full pipeline with live output |
| `orchestrator.py` | Decomposes tasks, shops models, synthesizes |
| `model_registry.py` | Model catalog — cost + quality scores, selection algorithm |
| `providers.py` | Unified API call through DigitalOcean Gradient |
| `hlos.py` | HLOS wallet, passports, notarization, payments |

---

*Built at OpenClaw Hackathon — The Penthouse, Oakland 🦞*
