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

    MIN_ORDER_USD = 5.0  # Alpaca-Mindestgroesse fuer notional-Orders; darunter lohnt keine Order.

    def rebalance_to_weights(self, target_weights: dict) -> None:
        """Bestehende Positionen schliessen, die nicht mehr im Zielportfolio sind, dann
        JE SYMBOL NUR DIE DIFFERENZ zwischen aktuellem Marktwert und Zielwert handeln.

        WICHTIG (Bugfix 02.09.2026): die alte Version hat bei jedem Lauf, der als
        "Rebalance-Tag" erkannt wurde, den VOLLEN Zielbetrag neu gekauft -- unabhaengig
        davon, ob die Position schon in der richtigen Groesse vorhanden war. Da die
        Momentum-Strategie aktuell an jedem Tag des laufenden Monats "Rebalance faellig"
        meldet (bekannte, separat dokumentierte Einschraenkung), hat sich das taeglich
        wiederholt und echte Positionen weit ueber die Zielgewichtung hinaus aufgebaut
        (auf Kredit/Margin, da mehr gekauft wurde als eigentlich Kapital vorhanden war).
        Diese Version handelt stattdessen nur die Differenz -- bei bereits korrekt
        getroffener Zielgroesse wird gar keine Order mehr ausgeloest, auch wenn die
        Strategie taeglich "Rebalance" sagt. Zu grosse Positionen werden dabei automatisch
        durch eine Verkaufsorder auf die Zielgroesse zurueckgestutzt.
        """
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        equity = self.get_equity()
        positions = self._client.get_all_positions()
        current_values = {p.symbol: float(p.market_value) for p in positions}

        for symbol in current_values:
            if symbol not in target_weights:
                logger.info("Schliesse Position %s (nicht mehr im Zielportfolio)", symbol)
                self._client.close_position(symbol)

        for symbol, weight in target_weights.items():
            target_value = equity * weight
            current_value = current_values.get(symbol, 0.0)
            diff = target_value - current_value

            if abs(diff) < self.MIN_ORDER_USD:
                logger.info(
                    "Position %s bereits nah am Ziel (%.2f USD, Ziel %.2f USD) -- keine Order noetig",
                    symbol, current_value, target_value,
                )
                continue

            side = OrderSide.BUY if diff > 0 else OrderSide.SELL
            action_label = "kaufen" if diff > 0 else "verkaufen"
            logger.info(
                "Anpassung %s: %s %.2f USD (aktuell %.2f USD -> Ziel %.2f USD, %.1f%% des Portfolios)",
                symbol, action_label, abs(diff), current_value, target_value, weight * 100,
            )
            # Hinweis: notional-Orders erfordern Bruchteilsanteile (fractional shares),
            # die Alpaca fuer die meisten liquiden NASDAQ-Werte unterstuetzt.
            order = MarketOrderRequest(
                symbol=symbol,
                notional=round(abs(diff), 2),
                side=side,
                time_in_force=TimeInForce.DAY,
            )
            self._client.submit_order(order)
