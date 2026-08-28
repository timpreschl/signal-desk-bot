"""
Duenne Schicht ueber alpaca-py fuer Orderausfuehrung. Bewusst simpel: Marktorders auf
Zielgewichte umrechnen. Wird erst aktiv, sobald .env auf dem Server ausgefuellt ist --
lokal/hier ohne Keys nicht lauffaehig (das ist gewollt, siehe config.validate()).
"""
from __future__ import annotations

import logging

logger = logging.getLogger("signal_desk.execution")


class AlpacaBroker:
    def __init__(self, settings) -> None:
        from alpaca.trading.client import TradingClient

        settings.validate()
        self._settings = settings
        self._client = TradingClient(
            settings.alpaca_api_key,
            settings.alpaca_secret_key,
            paper=settings.is_paper(),
        )
        mode = "PAPER" if settings.is_paper() else "LIVE (ECHTGELD)"
        logger.warning("AlpacaBroker gestartet im Modus: %s", mode)

    def get_equity(self) -> float:
        account = self._client.get_account()
        return float(account.equity)

    def rebalance_to_weights(self, target_weights: dict) -> None:
        """Sehr einfache Umsetzung: bestehende Positionen schliessen, die nicht mehr im
        Zielportfolio sind, dann Zielgewichte per Marktorder aufbauen. Fuer Phase 3/4
        (echter Bot-Betrieb) wird das noch um Teilausfuehrung, Limit-Orders und
        Fehlerbehandlung erweitert -- hier zunaechst die nachvollziehbare Grundversion.
        """
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        equity = self.get_equity()
        current_positions = {p.symbol: float(p.qty) for p in self._client.get_all_positions()}

        for symbol in current_positions:
            if symbol not in target_weights:
                logger.info("Schliesse Position %s (nicht mehr im Zielportfolio)", symbol)
                self._client.close_position(symbol)

        for symbol, weight in target_weights.items():
            target_value = equity * weight
            logger.info("Zielposition %s: %.2f USD (%.1f%% des Portfolios)", symbol, target_value, weight * 100)
            # Hinweis: notional-Orders erfordern Bruchteilsanteile (fractional shares),
            # die Alpaca fuer die meisten liquiden NASDAQ-Werte unterstuetzt.
            order = MarketOrderRequest(
                symbol=symbol,
                notional=round(target_value, 2),
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
            )
            self._client.submit_order(order)
