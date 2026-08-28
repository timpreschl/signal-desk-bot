"""
Unit-Test mit synthetischen Kursdaten (kein Internetzugriff noetig) -- prueft, dass die
Backtest-Engine und die Momentum-Strategie mechanisch korrekt rechnen, BEVOR wir sie auf
echte Marktdaten loslassen (die erst auf dem VPS verfuegbar sind).
"""
import numpy as np
import pandas as pd

from backtest.engine import run_backtest
from strategies.momentum import RelativeMomentumStrategy


def make_synthetic_prices(seed: int, drift: float, n_days: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-03", periods=n_days)
    returns = rng.normal(loc=drift, scale=0.015, size=n_days)
    close = 100 * (1 + pd.Series(returns, index=dates)).cumprod()
    return pd.DataFrame({"close": close}, index=dates)


def test_momentum_strategy_prefers_the_stronger_trend():
    # Symbol A hat klar positiven Drift, Symbol B ist flach -- die Strategie MUSS
    # nach genuegend Historie A staerker gewichten als B.
    prices = {
        "A": make_synthetic_prices(seed=1, drift=0.0015),
        "B": make_synthetic_prices(seed=2, drift=0.0000),
    }
    strategy = RelativeMomentumStrategy(lookback_days=60, top_n=1)
    signals = strategy.generate_signals(prices)

    closes = pd.DataFrame({sym: df["close"] for sym, df in prices.items()})
    result = run_backtest(closes, signals)

    assert signals["A"].sum() > signals["B"].sum(), "Momentum-Strategie sollte den staerkeren Trend bevorzugen"
    assert np.isfinite(result.cagr)
    assert result.max_drawdown <= 0


def test_backtest_matches_buy_and_hold_when_always_fully_invested():
    prices = make_synthetic_prices(seed=3, drift=0.0008)
    closes = pd.DataFrame({"A": prices["close"]})
    weights = pd.DataFrame({"A": 1.0}, index=closes.index)

    result = run_backtest(closes, weights, initial_capital=1000.0)
    buy_and_hold_return = closes["A"].iloc[-1] / closes["A"].iloc[0] - 1

    assert abs(result.total_return - buy_and_hold_return) < 0.02


if __name__ == "__main__":
    test_momentum_strategy_prefers_the_stronger_trend()
    test_backtest_matches_buy_and_hold_when_always_fully_invested()
    print("Alle Tests bestanden.")
