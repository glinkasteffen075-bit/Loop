# Entscheidungslog fuer den Loop-Orchestrator

Diese Datei dokumentiert nicht verborgenes internes Modell-Denken, sondern die nachvollziehbare fachliche Herleitung der bisherigen Architektur, der Prompts und der empfohlenen Umsetzung.

Sie ist als Projektakte gedacht: Warum wurde etwas vorgeschlagen, welche Probleme wurden erkannt, welche Struktur wurde daraus abgeleitet und welche Dateien wurden im Repo angelegt.

## Ausgangsziel

Das Ziel ist ein Orchestrator-Loop zwischen:

- einem Supervisor-Modell wie GPT oder Jetski BT
- Codex als technischem Executor
- GitHub als gemeinsamem Zustands- und Austauschkanal

Der gewuenschte Ablauf ist:

1. Der Supervisor bewertet den Zustand eines Projekts.
2. Wenn das Ziel noch nicht erreicht ist, formuliert er einen neuen Prompt oder Task.
3. Dieser Task gelangt zu Codex.
4. Codex programmiert, prueft und erzeugt Output.
5. Der Output wird nach GitHub zurueckgegeben.
6. Der Supervisor bewertet erneut.
7. Der Loop endet erst, wenn das Gesamtziel wirklich erfuellt ist.

Beispiel fuer ein Globalziel:

"Arbeite weiter an meinem KI-Projekt Isaac und mache das Programm stabil. Erst wenn alle relevanten Module und das Kernmodul fluessig und ohne kritische Fehler laufen, ist der Auftrag erfuellt."

## Was im vorhandenen Repo bereits vorhanden war

Im Repo waren bereits erste Bausteine vorhanden:

- `listener.py`
- `pinger.py`
- `codex_trigger.py`
- `run_codex.sh`

Diese Struktur zeigte, dass bereits folgende Idee umgesetzt wurde:

- GitHub wird gepollt
- neue Supervisor-Kommentare werden erkannt
- daraus wird ein Prompt fuer Codex abgeleitet
- Codex soll dann gestartet werden

Das ist ein sinnvoller Start, aber noch keine vollstaendige Orchestrierung.

## Zentrale Feststellungen

Bei der Analyse des bisherigen Ansatzes wurden mehrere Kernprobleme sichtbar:

### 1. Kommentar-basierter Trigger reicht nicht aus

Wenn nur der neueste Kommentar ausgewertet wird, fehlt ein stabiler Systemzustand.

Probleme:

- dieselbe Anweisung kann mehrfach verarbeitet werden
- Teilergebnisse sind schwer nachvollziehbar
- es ist unklar, ob ein Task bereits erledigt, wiederholt oder blockiert ist

### 2. Es fehlte ein strukturierter Rueckkanal von Codex

Ein Prompt an Codex allein loest das Hauptproblem nicht. Der Supervisor braucht spaeter harte Signale, um den Output zu bewerten.

Dazu gehoeren:

- welche Dateien wurden geaendert
- welche Tests wurden ausgefuehrt
- welche Kommandos liefen mit welchem Exit-Code
- welche Blocker bestehen noch

### 3. Das Ziel "stabil" war zu unscharf

Ein globales Ziel wie "mach das Projekt stabil" ist als Vision sinnvoll, aber als Bewertungskriterium zu unpraezise.

Deshalb wurde empfohlen, Stabilitaet in konkrete Pruefpunkte zu uebersetzen, z. B.:

- Start ohne Absturz
- Kernpfade funktionieren
- relevante Tests oder Smoke Checks sind gruen
- keine ungefangenen Exceptions in zentralen Ablaufen
- keine neue schwere Regression

### 4. Es fehlte eine echte Rollenaufteilung

Die saubere Trennung wurde so hergeleitet:

- Supervisor: planen und bewerten
- Codex: implementieren und pruefen
- GitHub: Zustand, Historie, Trigger, Reports

Diese Trennung verhindert, dass Planung, Umsetzung und Bewertung vermischt werden.

## Daraus abgeleitete Architektur

Aus den Problemen wurde ein MVP-Orchestrator abgeleitet.

### Rollen

- `Supervisor`
- `Executor`
- `GitHub`

### Persistente Artefakte

Statt nur freier Chatnachrichten wurden zwei Kernartefakte eingefuehrt:

- `orchestrator/tasks/current-task.json`
- `orchestrator/reports/latest-result.json`

Warum:

- Der Task ist der verbindliche Arbeitsauftrag.
- Das Result ist der strukturierte Nachweis der Arbeit.
- Beide koennen von GPT, Codex, GitHub und optional CI gelesen werden.

### Statusmodell

Es wurden explizite Statuswerte vorgeschlagen, damit der Loop maschinenlesbar wird.

Beispiele:

- global: `idle`, `task_ready`, `executor_running`, `awaiting_evaluation`, `goal_complete`, `human_required`, `error`
- task/result: `open`, `in_progress`, `success`, `partial_success`, `blocked`, `failed`

Warum:

- Der Supervisor kann klar entscheiden, was als Naechstes passieren soll.
- Doppelte oder widerspruechliche Auswertungen werden reduziert.

### Trigger-Logik

Es wurde folgende Priorisierung empfohlen:

1. GitHub Webhook
2. GitHub Actions als Ausloeser
3. Polling als MVP-Fallback

Warum:

- Polling ist fuer einen ersten Prototyp okay.
- Langfristig ist eventbasierte Ausloesung robuster und schneller.

## Was konkret im Repo angelegt wurde

Folgende Dateien wurden erstellt:

- `ORCHESTRATOR_SPEC.md`
- `GPT_SYSTEM_RULE_DE.md`
- `IMPLEMENTATION_NOTES.md`
- `orchestrator/prompts/supervisor_system.md`
- `orchestrator/prompts/codex_executor_prompt.md`
- `orchestrator/schemas/task.schema.json`
- `orchestrator/schemas/result.schema.json`
- `orchestrator/tasks/current-task.example.json`
- `orchestrator/reports/latest-result.example.json`

## Warum diese Dateien erzeugt wurden

### `ORCHESTRATOR_SPEC.md`

Diese Datei beschreibt den Gesamtmechanismus:

- Rollen
- Loop-Lebenszyklus
- Triggerstrategie
- Bewertungslogik
- GitHub als Zustandskanal

### `GPT_SYSTEM_RULE_DE.md`

Diese Datei ist die deutsche Systemregel fuer deinen Supervisor.

Sie enthaelt bewusst:

- keine Zeitbegrenzung
- Nutzung aller verfuegbaren Werkzeuge und Faehigkeiten
- Pflicht zur evidenzbasierten Bewertung
- Pflicht zur Formulierung konkreter statt vager Folgeaufgaben

### `supervisor_system.md`

Das ist die englische Supervisor-Fassung fuer eine promptgesteuerte Nutzung.

### `codex_executor_prompt.md`

Diese Datei legt fest, wie Codex als Executor arbeiten soll:

- aktuellen Task lesen
- Repo analysieren
- aendern
- testen
- Result schreiben
- ehrlich ueber Blocker berichten

### JSON-Schemas und Beispiele

Die Schemas wurden erzeugt, damit die Kommunikation nicht nur textuell, sondern strukturiert erfolgt.

Dadurch kann der Supervisor spaeter Regeln wie diese anwenden:

- wenn `status = success` und Akzeptanzkriterien belegt sind, dann Task abschliessen
- wenn `status = partial_success`, dann naechsten kleineren Task erzeugen
- wenn `status = blocked`, dann `human_required` oder Infrastruktur-Fix

## Wie der letzte Output zustande kam

Die letzte Antwort beruhte auf folgenden offenen Zielen:

1. Du wolltest eine Systemregel fuer GPT.
2. Du wolltest einen konkreten technischen Ablauf fuer den Loop.
3. Du wolltest, dass Zeitfreiheit und die Nutzung aller verfuegbaren Werkzeuge und Faehigkeiten explizit in die Prompts aufgenommen werden.

Daraufhin wurde entschieden:

- nicht nur eine Erklaerung zu schreiben
- sondern direkt nutzbare Dateien in das Repo zu legen

Die Entscheidung war bewusst pragmatisch:

- Spezifikation zuerst
- dann Prompttexte
- dann maschinenlesbare Schemas
- dann Beispielpayloads

So entsteht ein Satz von Dateien, den du direkt im Projekt, in GitHub oder in einer spaeteren Automatisierung nutzen kannst.

## Wichtige Architekturentscheidung

Die wichtigste fachliche Entscheidung war:

Nicht mehr nur:

- Kommentar lesen
- Prompt bauen
- Codex starten

Sondern:

- Task speichern
- Codex triggern
- Ergebnis speichern
- Supervisor prueft Ergebnis plus GitHub-Zustand plus optional CI

Diese Umstellung ist entscheidend, weil sie aus einem fragilen Nachrichtenfluss einen pruefbaren Workflow macht.

## Was absichtlich nicht behauptet wurde

Es wurde bewusst nicht behauptet, dass der aktuelle Loop schon voll funktionsfaehig ist.

Noch offen ist insbesondere:

- `pinger.py` von kommentarorientiert auf taskorientiert umbauen
- `run_codex.sh` mit realem Codex-Aufruf versehen
- Result-Datei automatisch schreiben und committen
- optional CI-Checks in die Bewertung aufnehmen

## Empfohlene naechste Schritte

Die sinnvollste technische Fortsetzung ist:

1. `pinger.py` so erweitern, dass `task_id`, `result_id` und Commit-SHAs dedupliziert werden
2. Trigger auf `current-task.json` und `latest-result.json` ausrichten
3. `run_codex.sh` an den realen Executor anbinden
4. einen kleinen Reporter-Schritt einfuehren, der `latest-result.json` schreibt
5. optional GitHub Actions als Trigger oder Bewertungsquelle einbinden

## Zusammenfassung

Die bisherige Arbeit im Repo war kein willkuerlicher Theorieblock, sondern die Ableitung einer robusteren Architektur aus den konkret sichtbaren Schwaechen des vorhandenen Ansatzes.

Kurz gesagt:

- Dein Grundkonzept ist tragfaehig.
- Das Repo hatte schon einen funktionierenden Ansatz fuer Triggering.
- Der naechste notwendige Schritt war Struktur, nicht mehr lose Erklaerung.
- Deshalb wurden Systemregel, Executor-Prompt, Spezifikation, Schemas und Beispielpayloads direkt als Repo-Dateien angelegt.

Diese Datei dient als nachvollziehbare Herleitungsakte fuer genau diese Entscheidungen.
