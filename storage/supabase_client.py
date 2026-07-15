# مسیر فایل: storage/supabase_client.py
"""لایه‌ی ارتباط با Supabase — مطابق طرح جداول در architecture.md بخش ۹."""
from __future__ import annotations
import os
from datetime import datetime, timezone
import pandas as pd
from supabase import create_client, Client

from strategy.core import Signal


def get_client() -> Client:
    url = os.environ["SUPABASE_URL"].strip()
    key = os.environ["SUPABASE_KEY"].strip()

    if not url.startswith("http://") and not url.startswith("https://"):
        raise ValueError(
            f"SUPABASE_URL باید با https:// شروع شود، مقدار فعلی این‌طور نیست: {url!r} "
            "(نمونه‌ی صحیح: https://xxxxxxxxxxxxx.supabase.co — از Project Settings > API > Project URL)"
        )
    url = url.rstrip("/")  # اسلش اضافه در انتها هم گاهی باعث خطای Invalid URL می‌شود

    return create_client(url, key)


def cache_ohlcv(client: Client, symbol: str, timeframe: str, df: pd.DataFrame):
    records = [
        {
            "symbol": symbol, "timeframe": timeframe,
            "timestamp": ts.isoformat(),
            "open": float(row["open"]), "high": float(row["high"]),
            "low": float(row["low"]), "close": float(row["close"]),
            "volume": float(row["volume"]), "source": row.get("source", "unknown"),
        }
        for ts, row in df.iterrows()
    ]
    if records:
        client.table("ohlcv_cache").upsert(records, on_conflict="symbol,timeframe,timestamp").execute()


def insert_signal(client: Client, sig: Signal, confidence: float, params_version: str):
    client.table("signals").insert({
        "symbol": sig.symbol,
        "timestamp": sig.timestamp.isoformat(),
        "direction": sig.direction,
        "entry": sig.entry,
        "stop_loss": sig.stop_loss,
        "tp1": sig.tp1, "tp2": sig.tp2, "tp3": sig.tp3,
        "ml_confidence": confidence,
        "status": "pending",
        "sent_to_telegram": True,
        "params_version": params_version,
    }).execute()


def get_pending_signals(client: Client, symbol: str) -> list[dict]:
    resp = client.table("signals").select("*").eq("symbol", symbol).eq("status", "pending").execute()
    return resp.data


def update_signal_status(client: Client, signal_id: int, status: str, pnl_pct: float):
    client.table("signals").update({
        "status": status,
        "pnl_pct": pnl_pct,
        "closed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", signal_id).execute()


def save_param_version(client: Client, symbol: str, version: str, risk_params: dict,
                        ml_threshold: float, adjusted_score: float, weights: dict,
                        accepted: bool, notes: str = ""):
    client.table("param_history").insert({
        "symbol": symbol, "version": version,
        "effective_from": datetime.now(timezone.utc).isoformat(),
        "atr_mult": risk_params["atr_mult"],
        "tp1_r": risk_params["tp1_r"], "tp2_r": risk_params["tp2_r"], "tp3_r": risk_params["tp3_r"],
        "ml_threshold": ml_threshold, "adjusted_score": adjusted_score,
        "backtest_weight": weights["backtest"], "live_weight": weights["live"],
        "accepted": accepted, "notes": notes,
    }).execute()


def get_active_params(client: Client, symbol: str) -> dict | None:
    resp = (client.table("param_history").select("*").eq("symbol", symbol)
            .eq("accepted", True).order("effective_from", desc=True).limit(1).execute())
    return resp.data[0] if resp.data else None
