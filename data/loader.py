"""
Datenanbindung. Zwei Quellen:
  - AlpacaDataLoader: echte Marktdaten ueber die Alpaca Market Data API (braucht .env-Keys,
    funktioniert nur mit echtem Internetzugang -- also auf dem VPS, nicht in dieser Sandbox).
  - CsvDataLoader: laedt lokale CSV-Dateien (Spalten: date, open, high, low, close, volume).
    Nuetzlich zum Testen ohne Internet/API-Keys, z.B. mit exportierten historischen Daten.

Beide geben ein einheitliches pandas-DataFrame zurueck, damit Strategien und Backtest-Engine
nicht wissen muessen, woher die Daten kommen.
"""
from __future__ import annotations

import pandas as pd


class CsvDataLoader:
    def load(self, path: str) -> pd.DataFrame:
        df = pd.read_csv(path, parse_dates=["date"])
        df = df.sort_values("date").set_index("date")
        required = {"open", "high", "low", "close", "volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"CSV fehlen Spalten: {missing}")
        return df


class AlpacaDataLoader:
    """Holt taegliche Kursdaten ueber die Alpaca Market Data API.
    Braucht funktionierenden Internetzugang (auf dem VPS gegeben) und gueltige .env-Keys.
    """

    def __init__(self, settings) -> None:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        from alpaca.data.enums import DataFeed

        settings.validate()
        self._client = StockHistoricalDataClient(settings.alpaca_api_key, settings.alpaca_secret_key)
        self._TimeFrame = TimeFrame
        self._StockBarsRequest = StockBarsRequest
        # Kostenlose Alpaca-Accounts duerfen nur den IEX-Feed abfragen, nicht den
        # vollen SIP-Konsolidierungsfeed (der ist kostenpflichtig) -- ohne dieses
        # Flag schlaegt jede Anfrage mit "subscription does not permit querying
        # recent SIP data" fehl. IEX deckt trotzdem alle liquiden NASDAQ-Werte
        # aus unserer Watchlist gut ab.
        self._feed = DataFeed.IEX

    def load(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        request = self._StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=self._TimeFrame.Day,
            start=start,
            end=end,
            feed=self._feed,
        )
        bars = self._client.get_stock_bars(request).df
        bars = bars.reset_index().set_index("timestamp")
        bars.index.name = "date"
        return bars[["open", "high", "low", "close", "volume"]]
