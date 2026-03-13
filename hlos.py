"""
HLOS client — wallet tracking, agent passports, notarization.
Swap HLOS_API_KEY into your env and the real endpoints will light up.
"""
import os
import requests
import uuid
from datetime import datetime

HLOS_API_KEY = os.environ.get("HLOS_API_KEY", "YOUR_HLOS_KEY")
BASE_URL = "https://api.hlos.ai/v1"

HEADERS = {
    "Authorization": f"Bearer {HLOS_API_KEY}",
    "Content-Type": "application/json",
}

# ── Ledger (local fallback for demo if HLOS calls fail) ──────────────────────
_ledger: list[dict] = []
_wallet_balance: float = 0.0


def fund_wallet(amount_usd: float) -> dict:
    """Deposit credits into HLOS wallet for this session."""
    global _wallet_balance
    try:
        r = requests.post(f"{BASE_URL}/wallet/fund", headers=HEADERS,
                          json={"amount": amount_usd}, timeout=5)
        r.raise_for_status()
        result = r.json()
        _wallet_balance = result.get("balance", amount_usd)
        return result
    except Exception:
        # Local fallback
        _wallet_balance = amount_usd
        return {"balance": _wallet_balance, "status": "funded (local)"}


def issue_passport(agent_name: str) -> dict:
    """Give an agent a HLOS passport (identity)."""
    try:
        r = requests.post(f"{BASE_URL}/passport/issue", headers=HEADERS,
                          json={"agent_name": agent_name}, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {
            "passport_id": f"passport_{uuid.uuid4().hex[:8]}",
            "agent_name": agent_name,
            "issued_at": datetime.utcnow().isoformat(),
            "status": "issued (local)",
        }


def notarize(agent_name: str, task: str, output_hash: str) -> dict:
    """Notarize a completed subtask — proof of work on-chain."""
    try:
        r = requests.post(f"{BASE_URL}/notarize", headers=HEADERS,
                          json={"agent": agent_name, "task": task,
                                "output_hash": output_hash}, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        attestation_id = f"attest_{uuid.uuid4().hex[:10]}"
        return {
            "attestation_id": attestation_id,
            "agent": agent_name,
            "task": task,
            "output_hash": output_hash,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "notarized (local)",
        }


def pay(agent_name: str, passport_id: str, amount_usd: float,
        attestation_id: str) -> dict:
    """Release payment from escrow to a subagent on task completion."""
    global _wallet_balance
    try:
        r = requests.post(f"{BASE_URL}/wallet/pay", headers=HEADERS,
                          json={"recipient": passport_id,
                                "amount": amount_usd,
                                "attestation_id": attestation_id}, timeout=5)
        r.raise_for_status()
        result = r.json()
        _wallet_balance = result.get("remaining_balance", _wallet_balance - amount_usd)
        entry = {**result, "agent_name": agent_name}
    except Exception:
        _wallet_balance -= amount_usd
        entry = {
            "tx_id": f"tx_{uuid.uuid4().hex[:10]}",
            "agent_name": agent_name,
            "passport_id": passport_id,
            "amount_usd": amount_usd,
            "attestation_id": attestation_id,
            "remaining_balance": _wallet_balance,
            "status": "paid (local)",
        }
    _ledger.append(entry)
    return entry


def get_receipt() -> dict:
    """Return the full payment receipt for this session."""
    total_paid = sum(e.get("amount_usd", 0) for e in _ledger)
    return {
        "transactions": _ledger,
        "total_paid_usd": round(total_paid, 4),
        "remaining_balance": round(_wallet_balance, 4),
    }
