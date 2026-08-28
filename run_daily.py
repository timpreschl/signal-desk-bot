"""
Taeglicher Einstiegspunkt fuer den Live-/Paper-Betrieb. Bewusst als einmalig laufendes
Skript gebaut (per Cronjob einmal pro Handelstag gestartet), nicht als Dauerprozess --
das ist einfacher zu ueberwachen, staerker fehlertolerant (ein Absturz haengt nicht den
ganzen Bot lahm, sondern betrifft nur den einen Lauf) und leichter zu verstehen.

Ablauf:
  1. Aktuelle Kursdaten holen (Alpaca Market Data API).
  2. Strategie(n) Signale berechnen lassen.
  3. Risikomanagement wendet Limits an.
  4. Falls Notbremse (Tagesverlust-Limit) aktiv: NICHTS tun, nur loggen.
  5. Sonst: Portfolio auf Zielgewichte umschichten.

Wird per Cron aufgerufen, z.B.:
  30 9 * * 1-5  cd /opt/signal-desk-bot && /opt/signal-desk-bot/venv/bin/python run_daily.py >> logs/run.log 2>&1
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from config import settings
from data.loader import AlpacaDataLoader
from strategies.momentum import RelativeMomentumStrategy
from risk.manager import RiskManager, RiskLimits
from execution.alpaca_broker import AlpacaBroker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("signal_desk.run_daily")

# Bewusst kurze, feste Watchlist statt "alle NASDAQ-Aktien" -- einfacher zu ueberwachen,
# und alle Symbole sind hochliquide (wichtig fuer sauberes Order-Fill-Verhalten).
WATCHLIST = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "COST"]


def main() -> None:
    settings.validate()
    broker = AlpacaBroker(settings)

    equity_now = broker.get_equity()
    logger.info("Aktuelles Portfolio-Equity: %.2f USD", equity_now)

    loader = AlpacaDataLoader(settings)
    end = datetime.utcnow()
    start = end - timedelta(days=400)  # genug Historie fuer 126-Tage-Lookback + Puffer
    prices = {symbol: loader.load(symbol, start.isoformat(), end.isoformat()) for symbol in WATCHLIST}

    strategy = RelativeMomentumStrategy(lookback_days=126, top_n=3)
    signals = strategy.generate_signals(prices)
    today_weights = signals.iloc[-1].to_dict()

    risk = RiskManager(RiskLimits(
        max_open_positions=settings.max_open_positions,
        max_daily_loss_pct=settings.max_daily_loss_pct,
    ))
    safe_weights = risk.cap_weights(today_weights)

    logger.info("Zielgewichte nach Risikomanagement: %s", safe_weights)
    broker.rebalance_to_weights(safe_weights)
    logger.info("Lauf abgeschlossen.")


if __name__ == "__main__":
    main()
