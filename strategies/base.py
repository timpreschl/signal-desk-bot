"""
Jede Strategie ist bewusst simpel gehalten: sie bekommt Kursdaten fuer mehrere Symbole
und gibt nur ein Signal-DataFrame zurueck (Datum x Symbol -> Gewicht zwischen -1 und 1,
0 = keine Position). Risiko und Ausfuehrung sind bewusst NICHT Teil der Strategie --
das entkoppelt "welche Idee handeln wir" von "wie viel Risiko nehmen wir dafuer".
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd


class Strategy(ABC):
    name: str = "base"

    @abstractmethod
    def generate_signals(self, prices: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """prices: {symbol: DataFrame mit close-Spalte, DatetimeIndex}
        Rueckgabe: DataFrame, Index=Datum, Spalten=Symbole, Werte in [-1, 1].
        """
        raise NotImplementedError
