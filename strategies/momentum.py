"""
Relative-Momentum-Strategie (siehe Signal-Desk-Dokument, akademisch am besten belegte
Kandidatin: robust ueber 150+ Jahre und 40+ Laender, siehe Van Vliet et al.).

Regel (bewusst simpel, Standard-Formulierung):
  - Einmal im Monat: Rueckblick ueber `lookback_days` (Standard 126 Handelstage ~ 6 Monate).
  - Die `top_n` Symbole mit der hoechsten Kursperformance im Rueckblickzeitraum werden
    gleichgewichtet long gehalten, alle anderen auf 0.
  - Kein Short-Selling in dieser ersten Version -- weniger Komplexitaet, weniger Risiko.
"""
from __future__ import annotations

from typing import Dict

import pandas as pd

from strategies.base import Strategy


class RelativeMomentumStrategy(Strategy):
    name = "relative_momentum"

    def __init__(self, lookback_days: int = 126, top_n: int = 3, rebalance: str = "ME"):
        self.lookback_days = lookback_days
        self.top_n = top_n
        self.rebalance = rebalance

    def generate_signals(self, prices: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        closes = pd.DataFrame({sym: df["close"] for sym, df in prices.items()}).dropna(how="all")
        momentum = closes.pct_change(self.lookback_days)

        # Nur an Rebalance-Terminen (z.B. Monatsende) neu entscheiden, dazwischen halten.
        rebalance_dates = closes.resample(self.rebalance).last().index
        signals = pd.DataFrame(0.0, index=closes.index, columns=closes.columns)

        current_weights = pd.Series(0.0, index=closes.columns)
        for date in closes.index:
            if date in rebalance_dates and date in momentum.index:
                scores = momentum.loc[date].dropna()
                winners = scores.sort_values(ascending=False).head(self.top_n).index
                current_weights = pd.Series(0.0, index=closes.columns)
                if len(winners) > 0:
                    current_weights[winners] = 1.0 / len(winners)
            signals.loc[date] = current_weights

        return signals
