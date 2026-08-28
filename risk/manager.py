"""
Risikomanagement ist zentral und strategie-unabhaengig -- egal welche Strategie ein Signal
liefert, hier wird begrenzt, wie viel tatsaechlich passiert. Genau der Baustein, der
"vollstaendig automatisch, aber nicht ohne Kontrolle" ermoeglicht.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskLimits:
    max_open_positions: int = 5
    risk_per_trade_pct: float = 1.0      # % des Portfolios, das pro Position riskiert wird
    max_daily_loss_pct: float = 3.0      # Notbremse: bei Erreichen -> keine neuen Trades mehr heute
    max_position_pct: float = 25.0       # Kein Symbol darf mehr als X % des Portfolios ausmachen


class RiskManager:
    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits

    def cap_weights(self, target_weights: dict) -> dict:
        """Begrenzt Zielgewichte auf max_position_pct und max_open_positions,
        BEVOR ueberhaupt eine Order gebaut wird."""
        capped = {sym: min(w, self.limits.max_position_pct / 100) for sym, w in target_weights.items() if w > 0}
        if len(capped) > self.limits.max_open_positions:
            top = sorted(capped.items(), key=lambda kv: kv[1], reverse=True)[: self.limits.max_open_positions]
            capped = dict(top)
        return capped

    def daily_loss_breached(self, equity_start_of_day: float, equity_now: float) -> bool:
        if equity_start_of_day <= 0:
            return False
        drawdown_pct = (equity_start_of_day - equity_now) / equity_start_of_day * 100
        return drawdown_pct >= self.limits.max_daily_loss_pct
