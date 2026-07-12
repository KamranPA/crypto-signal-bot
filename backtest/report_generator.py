# مسیر فایل: backtest/report_generator.py
"""تولید گزارش بک‌تست به‌صورت فایل HTML تعاملی (plotly) — در reports/ کامیت می‌شود."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backtest.engine import BacktestReport

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def generate_html_report(report: BacktestReport, out_dir: Path = REPORTS_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = out_dir / f"backtest_{report.symbol}_{date_str}.html"

    closed = report.closed_trades  # فقط معاملات بسته‌شده (TP/SL) — open_at_end حذف شده
    equity = (1 + pd.Series([t.pnl_pct for t in closed]) / 100).cumprod()
    times = [t.exit_time for t in closed]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                         subplot_titles=(f"{report.symbol} — Equity Curve", "PnL هر معامله (%)"),
                         row_heights=[0.65, 0.35])

    fig.add_trace(go.Scatter(x=times, y=equity, mode="lines", name="Equity"), row=1, col=1)

    colors = ["#00dbff" if t.pnl_pct >= 0 else "#b2b5be" for t in closed]
    fig.add_trace(go.Bar(x=times, y=[t.pnl_pct for t in closed], marker_color=colors,
                          name="PnL %"), row=2, col=1)

    fig.update_layout(
        title=f"گزارش بک‌تست — {report.symbol}",
        template="plotly_dark",
        height=700,
        annotations=[
            dict(text=(
                f"تعداد معاملات بسته‌شده: {len(closed)} (+{report.n_open_at_end} بدون نتیجه تا پایان دیتا) | "
                f"Win Rate: {report.win_rate:.1%} | "
                f"Profit Factor: {report.profit_factor:.2f} | "
                f"میانگین سود هر معامله: {report.avg_pnl_pct:.2f}% | "
                f"Max Drawdown: {report.max_drawdown_pct:.2f}%"
            ), showarrow=False, xref="paper", yref="paper", x=0.5, y=1.08, font=dict(size=13))
        ],
    )
    fig.write_html(str(path))
    return path


def generate_summary_md(reports: list[BacktestReport], out_dir: Path = REPORTS_DIR,
                         skipped: list[str] | None = None, degraded: list[str] | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "summary.md"
    skipped = skipped or []
    degraded = degraded or []

    lines = [
        "# خلاصه‌ی بک‌تست واچ‌لیست",
        "",
        f"تاریخ تولید: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]

    if skipped:
        lines += [
            f"⚠️ **این ارزها کاملاً fail شدند و در جدول زیر نیستند:** {', '.join(skipped)}  ",
            "(علت را در لاگ اجرای GitHub Actions همان run ببینید — معمولاً خطای دریافت دیتا)",
            "",
        ]
    if degraded:
        lines += [
            f"ℹ️ **این ارزها فقط با دیتای CoinEx (بدون Yahoo، تاریخچه‌ی کوتاه‌تر) بک‌تست شدند:** "
            f"{', '.join(degraded)}",
            "",
        ]

    lines += [
        "> Win Rate / Profit Factor / PnL / Max Drawdown فقط بر اساس معاملات **بسته‌شده** "
        "(رسیده به TP یا SL) محاسبه شده‌اند. ستون «بدون نتیجه» تعداد معاملاتی است که تا پایان "
        "دیتا نه TP نه SL خورده‌اند و در این آمار لحاظ نشده‌اند.",
        "",
        "| ارز | معاملات بسته‌شده | بدون نتیجه | Win Rate | Profit Factor | میانگین PnL % | Max Drawdown % |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in reports:
        lines.append(
            f"| {r.symbol} | {len(r.closed_trades)} | {r.n_open_at_end} | {r.win_rate:.1%} | "
            f"{r.profit_factor:.2f} | {r.avg_pnl_pct:.2f}% | {r.max_drawdown_pct:.2f}% |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
