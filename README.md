# Signal Desk Bot -- Grundgeruest

Zugehöriges Projekt-Dokument (Strategien, Recherche, Roadmap): siehe "Signal Desk" Artefakt.

Dieses Repository ist der Code-Teil: eine bewusst simple, nachvollziehbare Grundstruktur
fuer den NASDAQ-Aktien-Bot. Noch OHNE echte Verbindung getestet (dafuer fehlen die
API-Keys deines zweiten Alpaca-Paper-Accounts) -- die Logik selbst ist aber bereits mit
synthetischen Daten getestet (`tests/`).

## Struktur

- `config.py` -- liest alle Einstellungen aus `.env` (nie Keys im Code!)
- `data/loader.py` -- Marktdaten holen (Alpaca API oder lokale CSV zum Testen)
- `strategies/` -- eine Strategie pro Datei, austauschbar (aktuell: Relative Momentum)
- `risk/manager.py` -- zentrale, strategie-unabhaengige Risikogrenzen
- `backtest/engine.py` -- einfache, nachvollziehbare Backtest-Engine
- `execution/alpaca_broker.py` -- Orderausfuehrung ueber Alpaca
- `run_daily.py` -- taeglicher Einstiegspunkt (per Cronjob gestartet)
- `tests/` -- Unit-Tests mit synthetischen Daten (kein Internet noetig)

## Warum kein Dauerprozess?

`run_daily.py` laeuft einmal pro Handelstag und beendet sich danach wieder. Das ist
einfacher zu ueberwachen als ein 24/7-Prozess: ein Absturz betrifft nur den einen
Tageslauf, nicht den ganzen Bot, und Logs sind pro Lauf klar abgegrenzt. Das passt auch
gut zu einer kostenlosen Ausfuehrung (siehe unten) statt einem eigenen Dauer-Server.

## Option A (empfohlen zum Start, kostenlos): GitHub Actions

Kein eigener Server noetig. GitHub fuehrt `run_daily.py` fuer dich einmal pro Handelstag
aus, kostenlos im Rahmen des Gratis-Kontingents (2.000 Minuten/Monat bei privaten
Repos -- ein Lauf braucht ~1-2 Minuten, also weit im gruenen Bereich).

1. Kostenlosen GitHub-Account anlegen (github.com), neues **privates** Repository
   erstellen, z.B. "signal-desk-bot".
2. Inhalt dieses Ordners hochladen (per Drag-and-Drop im Browser reicht -- kein
   Git-Kommandozeilen-Wissen noetig -- oder `git push`, falls du das kennst).
3. Im Repo: Settings -> Secrets and variables -> Actions -> "New repository secret".
   Dort direkt auf GitHub eintragen (niemals im Chat mit mir teilen):
   - `ALPACA_API_KEY`
   - `ALPACA_SECRET_KEY`
   - `ALPACA_BASE_URL` = `https://paper-api.alpaca.markets`
4. Optional unter "Variables" (gleiche Seite): `MAX_OPEN_POSITIONS`, `RISK_PER_TRADE_PCT`,
   `MAX_DAILY_LOSS_PCT` setzen (sonst gelten die Standardwerte aus `config.py`).
5. Fertig. Der Workflow (`.github/workflows/daily-run.yml`) laeuft automatisch werktags
   kurz nach US-Börsenöffnung. Unter dem Reiter "Actions" im Repo siehst du jeden Lauf
   und die Logs, und kannst ihn dort auch manuell per Knopfdruck ("Run workflow") starten.

**Ehrlicher Nachteil:** GitHub garantiert keine exakte Startzeit fuer geplante Läufe --
bei hoher Auslastung (v.a. zu vollen Stunden) kann sich ein Lauf um 5-30 Minuten
verzögern, in Ausnahmefällen auch mehr. Für unsere aktuelle Strategie (monatliches
Rebalancing, kein Intraday-Timing) ist das unkritisch. Falls wir später zu
zeitkritischeren Strategien wechseln, ist das ein guter Grund fuer Option B.

## Option B (später, wenn's ernster wird): eigener VPS

Mehr Kontrolle, exakteres Timing, eigenes Dashboard möglich -- kostet aber ab ca.
4,59 €/Monat (z.B. Hetzner CX22). Sinnvoll, sobald wir mit echtem Geld arbeiten oder
Strategien mit engerem Timing testen.

```bash
# 1. Python + Grundpakete
sudo apt update && sudo apt install -y python3-venv python3-pip

# 2. Projekt auf den Server kopieren (z.B. per scp oder git) nach /opt/signal-desk-bot

cd /opt/signal-desk-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. .env anlegen und AUSSCHLIESSLICH auf dem Server ausfuellen
cp .env.example .env
nano .env   # ALPACA_API_KEY und ALPACA_SECRET_KEY deines ZWEITEN Paper-Accounts eintragen

# 4. Tests laufen lassen (kein Internet noetig, prueft nur die Logik)
PYTHONPATH=/opt/signal-desk-bot python tests/test_backtest_engine.py

# 5. Einmal manuell testen
PYTHONPATH=/opt/signal-desk-bot python run_daily.py

# 6. Taeglichen Cronjob einrichten (Mo-Fr, 9:35 US-Ostkueste-Zeit -- Zeitzone am Server pruefen!)
crontab -e
# Zeile hinzufuegen (Uhrzeit ggf. an Serverzeitzone anpassen):
# 35 15 * * 1-5 cd /opt/signal-desk-bot && venv/bin/python run_daily.py >> logs/run.log 2>&1
```

## Sicherheits-Grundregeln

- `.env` niemals per Chat, E-Mail oder Git teilen -- nur direkt auf dem Server bearbeiten.
- Start immer mit `ALPACA_BASE_URL=https://paper-api.alpaca.markets` (Paper-Trading).
  Erst auf `https://api.alpaca.markets` umstellen, wenn wir gemeinsam entschieden haben,
  dass genug Paper-Trading-Historie mit gutem Ergebnis vorliegt.
- `MAX_DAILY_LOSS_PCT` ist die Notbremse: wird sie erreicht, macht der Bot fuer den Rest
  des Tages nichts mehr. Lieber zu vorsichtig eingestellt als zu locker.

## Naechste Schritte (Phase 3)

1. Echten Backtest auf historischen Daten fahren, sobald der Server (mit vollem
   Internetzugang, anders als diese Cloud-Sandbox hier) laeuft.
2. Weitere Strategien aus dem Signal-Desk-Dokument als eigene Dateien in `strategies/`
   ergaenzen (gleiches Interface wie `momentum.py`).
3. Ein bis zwei Wochen taeglich per Cronjob im Paper-Modus laufen lassen, Log-Ausgaben
   gemeinsam auswerten.
