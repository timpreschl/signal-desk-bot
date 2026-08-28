"""
Bewusst einfache, nachvollziehbare Backtest-Engine (kein Blackbox-Framework) --
verstaendlich genug, um jedem Ergebnis zu misstrauen, bis wir es selbst nachvollzogen haben.

Nimmt Signal-Gewichte (siehe strategies/base.py) und taegliche Schlusskurse, simuliert eine
tägliche Umschichtung auf die Zielgewichte und berechnet die Standard-Kennzahlen.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    cagr: float
    max_drawdown: float
    sharpe: float
    total_return: float


def run_backtest(closes: pd.DataFrame, weights: pd.DataFrame, initial_capital: float = 10_000.0) -> BacktestResult:
    returns = closes.pct_change().fillna(0.0)
    # Gewichte von gestern auf heutige Returns anwenden (kein Lookahead-Bias).
    strat_returns = (weights.shift(1).fillna(0.0) * returns).sum(axis=1)

    equity = (1 + strat_returns).cumprod() * initial_capital
    total_return = equity.iloc[-1] / initial_capital - 1

    n_years = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = (equity.iloc[-1] / initial_capital) ** (1 / n_years) - 1 if n_years > 0 else float("nan")

    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max
    max_drawdown = drawdown.min()

    ann_factor = np.sqrt(252)
    sharpe = (strat_returns.mean() / strat_returns.std() * ann_factor) if strat_returns.std() > 0 else float("nan")

    return BacktestResult(
        equity_curve=equity,
        cagr=cagr,
        max_drawdown=max_drawdown,
        sharpe=sharpe,
        total_return=total_return,
    )
