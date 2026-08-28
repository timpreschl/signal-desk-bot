"""
Zentrale Konfiguration. Liest alles aus Umgebungsvariablen (.env-Datei) --
es stehen NIRGENDS Zugangsdaten fest im Code. Die .env-Datei wird direkt
auf dem Server angelegt und nie geteilt.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    alpaca_api_key: str = os.getenv("ALPACA_API_KEY", "")
    alpaca_secret_key: str = os.getenv("ALPACA_SECRET_KEY", "")
    alpaca_base_url: str = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

    max_open_positions: int = int(os.getenv("MAX_OPEN_POSITIONS", "5"))
    risk_per_trade_pct: float = float(os.getenv("RISK_PER_TRADE_PCT", "1.0"))
    max_daily_loss_pct: float = float(os.getenv("MAX_DAILY_LOSS_PCT", "3.0"))

    def is_paper(self) -> bool:
        return "paper-api" in self.alpaca_base_url

    def validate(self) -> None:
        if not self.alpaca_api_key or not self.alpaca_secret_key:
            raise RuntimeError(
                "ALPACA_API_KEY / ALPACA_SECRET_KEY fehlen. Bitte .env auf dem Server "
                "ausfuellen (siehe .env.example) -- niemals Keys im Code oder Chat teilen."
            )


settings = Settings()
