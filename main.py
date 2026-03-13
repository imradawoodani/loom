#!/usr/bin/env python3
"""
🦞 Agent Subcontractor
──────────────────────
Multi-model, multi-provider task execution with HLOS identity & settlement.

Usage:
  python main.py
  TASK="your task here" BUDGET=2.00 python main.py
"""
import os
import time
import hashlib
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

import hlos
import orchestrator

console = Console()

from model_registry import PROVIDER_COLORS, PROVIDER_LABELS

TASK   = os.environ.get("TASK",
    "Write a research paper on why AI agents need economic incentives to coordinate effectively")
BUDGET = float(os.environ.get("BUDGET", "2.00"))


def hash_output(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def print_plan(plan):
    t = Table(title="Execution Plan", box=box.ROUNDED, show_header=True, header_style="bold")
    t.add_column("#", width=3)
    t.add_column("Type", width=12)
    t.add_column("Model", width=16)
    t.add_column("Provider", width=14)
    t.add_column("Priority", width=10)
    t.add_column("Est. Cost", justify="right")
    t.add_column("Task")
    for s in plan["subtasks"]:
        c = PROVIDER_COLORS.get(s["provider"], "white")
        t.add_row(str(s["id"]), f"[bold]{s['type']}[/bold]", s["model_name"],
                  f"[{c}]{PROVIDER_LABELS[s['provider']]}[/{c}]",
                  s.get("priority", "balanced"), f"${s['est_cost_usd']:.4f}",
                  s["task"][:55] + ("…" if len(s["task"]) > 55 else ""))
    console.print(t)
    console.print(f"  Estimated total: [bold yellow]${plan['total_estimated_cost']:.4f}[/bold yellow] of ${BUDGET:.2f} budget\n")


def print_receipt(receipt, real_costs):
    console.rule("[bold]💳 HLOS Settlement Receipt[/bold]")
    t = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    t.add_column("Agent"); t.add_column("Provider"); t.add_column("TX ID")
    t.add_column("Attestation"); t.add_column("Cost", justify="right")
    for tx in receipt["transactions"]:
        name = tx.get("agent_name", "?")
        provider = real_costs.get(name, {}).get("provider", "?")
        c = PROVIDER_COLORS.get(provider, "white")
        t.add_row(name, f"[{c}]{PROVIDER_LABELS.get(provider, provider)}[/{c}]",
                  tx.get("tx_id", "?"), tx.get("attestation_id", "?"),
                  f"${tx.get('amount_usd', 0):.5f}")
    console.print(t)
    console.print(f"\n  Total paid:  [bold red]${receipt['total_paid_usd']:.5f}[/bold red]")
    console.print(f"  Remaining:   [bold green]${receipt['remaining_balance']:.5f}[/bold green]\n")


def run():
    console.rule("[bold magenta]🦞 Agent Subcontractor — Multi-Model Market[/bold magenta]")
    console.print(f"\n  [bold]Task:[/bold]   {TASK}")
    console.print(f"  [bold]Budget:[/bold]  ${BUDGET:.2f} USD\n")

    # 1. Fund wallet
    console.print("[cyan]◆ Funding HLOS escrow wallet...[/cyan]")
    wallet = hlos.fund_wallet(BUDGET)
    console.print(f"  ✓ Balance: ${wallet.get('balance', BUDGET):.2f}\n")

    # 2. Decompose + shop models
    console.print("[cyan]◆ Orchestrator decomposing task and shopping models...[/cyan]")
    plan = orchestrator.decompose_and_assign(TASK, BUDGET)
    console.print(f"  ✓ [bold]{plan['project_summary']}[/bold]\n")
    print_plan(plan)

    # 3. Issue passports
    console.print("[cyan]◆ Issuing HLOS passports...[/cyan]")
    passports = {}
    for s in plan["subtasks"]:
        agent_name = f"{s['model_name']}-{s['type']}-{s['id']}"
        passport = hlos.issue_passport(agent_name)
        passports[s["id"]] = {"passport": passport, "agent_name": agent_name}
        c = PROVIDER_COLORS.get(s["provider"], "white")
        console.print(f"  ✓ [{c}]{agent_name}[/{c}] → {passport['passport_id']}")
    console.print()

    # 4. Execute subtasks
    results, real_costs, context_so_far = [], {}, ""
    for s in plan["subtasks"]:
        agent_name  = passports[s["id"]]["agent_name"]
        passport_id = passports[s["id"]]["passport"]["passport_id"]
        c = PROVIDER_COLORS.get(s["provider"], "white")

        console.print(f"[cyan]◆ [{c}]{s['model_name']}[/{c}] → [bold]{s['type']}[/bold] (subtask {s['id']})...[/cyan]")
        t0 = time.time()
        output = orchestrator.run_subtask(s, context=context_so_far)
        elapsed = time.time() - t0

        actual_tokens = len(output.split()) * 1.3
        actual_cost   = s["model_spec"]["cost_per_1k_tokens"] * actual_tokens / 1000
        real_costs[agent_name] = {"provider": s["provider"], "cost": actual_cost}

        output_hash = hash_output(output)
        attest  = hlos.notarize(agent_name, s["task"], output_hash)
        payment = hlos.pay(agent_name, passport_id, round(actual_cost, 5), attest["attestation_id"])

        console.print(f"  ✓ {elapsed:.1f}s | hash: [dim]{output_hash}[/dim] | "
                      f"tx: [dim]{payment['tx_id']}[/dim] | paid: [bold]${actual_cost:.5f}[/bold]")
        console.print(Panel(output[:350] + ("…" if len(output) > 350 else ""),
                            title=f"[{c}]{s['model_name']}[/{c}] — {s['type']}",
                            border_style=c, expand=False))
        console.print()

        results.append({**s, "output": output, "agent_name": agent_name})
        context_so_far += f"\n[{s['type']} — {s['model_name']}]: {output}\n"

    # 5. Synthesize
    console.print("[cyan]◆ Orchestrator synthesizing final deliverable...[/cyan]\n")
    final = orchestrator.synthesize(TASK, results)
    console.print(Panel(final, title="[bold green]✓ FINAL DELIVERABLE[/bold green]",
                        border_style="green"))
    console.print()

    # 6. Receipt
    receipt = hlos.get_receipt()
    print_receipt(receipt, real_costs)

    with open("output.md", "w") as f:
        f.write(f"# {TASK}\n\n{final}\n\n---\n*Generated by Agent Subcontractor*\n")
    console.print("  📄 Saved to [bold]output.md[/bold]\n")


if __name__ == "__main__":
    run()
