# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektüberblick

Dieses Repository ist ein kryptoanalytisches Forschungsprojekt zur SHA-256-Kompressionsfunktion
unter Bitcoin-Randbedingungen ("K1" = SHA-256 auf 32-Byte-Eingabe, identisch mit dem zweiten
Durchlauf des Bitcoin-Double-Hash).

- `K1_Voruntersuchung.md` ist das zentrale Arbeitsdokument: Definitionen, bewiesene Sätze,
  Messergebnisse und Verweise auf die zugehörigen Programme. Neue Ergebnisse aus `programme/`
  gehören inhaltlich hier eingetragen (mit Abschnittsnummer), nicht nur als Skript abgelegt.
- `programme/` enthält die zugehörigen Python-Skripte: je eine Analyse, ein Beweis oder ein
  Messlauf pro Datei. Die meisten Skripte sind eigenständig lauffähig (`python3 programme/<name>.py`)
  und implementieren SHA-256 in Klartext-Form (`rotr`, `S0`/`S1`, `s0`/`s1`, `Ch`, `Maj`, IV/K-Tabellen)
  statt eine Bibliothek zu nutzen, um Rundenzahl, Verdrahtung oder Bit-Constraints gezielt zu verändern.
- Ein paar Skripte importieren voneinander gemeinsame Bausteine, u. a. `k1_cnf.py`
  (liefert `baue`, `sha_ref`, `PAD`, `IV`) und `k1_propagation.py` (liefert `Prop`) — verwendet von
  `k1_gnd_bitweise.py`, `k1_gnd_kurve.py`, `k1_gnd_vollstaendig.py`, `k1_neutral_bits.py`,
  `k1_neutral_bits_paare.py`.
- Abhängigkeiten: Python-Standardbibliothek plus `numpy` in einigen Skripten. Es gibt kein
  `requirements.txt`, kein Build-System und keine formale Test-Suite (`k1_test.py` ist ein
  Analyse-/Verifikationsskript, kein pytest-Test). `k1_sat_messlauf.py` (externe CDCL-Kalibrierung,
  Abschnitt 22) braucht zusätzlich das Paket `python-sat` (`pip install python-sat`) für
  In-Prozess-Bindings von CaDiCaL/Kissat — kein Solver-Binary auf dem PATH nötig.

## Befehle

- Skript ausführen: `python3 programme/<name>.py`
- Es gibt kein zentrales Test-, Lint- oder Build-Kommando in diesem Repository.

# Git Workflow & Branching
- Verwende strikt Trunk-Based Development.
- Erstelle keine neuen Feature-Branches oder Worktrees.
- Führe alle Änderungen, Commits und Pushes direkt auf dem aktuell ausgecheckten Branch durch.
- Erstelle keine Pull Requests, sondern committe direkt.
