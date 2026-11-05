# Gottesdienste Weingarten als Kalender-Abo

Ein Skript liest zweimal pro Woche (sonntags und donnerstags) die Seite
https://katholisch-weingarten.de/gottesdienste/ und erzeugt daraus `gottesdienste.ics`, einen Kalender, den man abonnieren kann.

## Abo-URL

```
https://raw.githubusercontent.com/PeterPan96-dev/KatholischWeingarten/main/gottesdienste.ics
```

So abonnierst du sie:

- **Apple Kalender (iPhone):** Einstellungen → Kalender → Accounts → Account hinzufügen → Andere → Kalenderabo hinzufügen → URL einfügen.
- **Google Kalender (Web):** Weitere Kalender (+) → Per URL → URL einfügen. Google aktualisiert Abos nur alle 12–24 Stunden.
- **Proton Kalender (Web):** Weitere Kalender (+) → Kalender per URL hinzufügen.
- **Android/GrapheneOS:** über Google-/Proton-Kalender oder eine App wie ICSx5 (URL abonnieren).

## Wie es funktioniert

| Datei | Aufgabe |
| --- | --- |
| `gottesdienste_ics.py` | Liest die Seite, erkennt Tage, Uhrzeiten, Orte und Titel und schreibt die Kalenderdatei |
| `.github/workflows/update.yml` | GitHub Action, die das Skript automatisch ausführt |
| `events.json` | Gesammelter Bestand aller bisher gesehenen Termine |
| `gottesdienste.ics` | Der fertige Kalender (wird automatisch erzeugt, nicht von Hand ändern) |

- **Zeitplan:** sonntags und donnerstags gegen 5:17 Uhr UTC (etwa 5:17 bis 6:17 Uhr Ortszeit). GitHub kann geplante Läufe verspätet starten.
- **Gesammelte Termine:** Die Seite zeigt nur etwa eine Woche im Voraus. Damit der Kalender nicht leerläuft, bleiben Termine im Bestand, auch wenn sie von der Seite verschwinden (60 Tage lang). Verschobene oder abgesagte Termine im Zeitraum der aktuellen Seite werden durch die neue Fassung ersetzt.
- **Änderungen:** Die Datei wird nur neu geschrieben und committet, wenn sich Termine geändert haben.

## Sofort aktualisieren

1. https://github.com/PeterPan96-dev/KatholischWeingarten/actions öffnen (eingeloggt, am besten im Browser, nicht in der App).
2. Links **Gottesdienste-Kalender aktualisieren** wählen.
3. **Run workflow** → Branch `main` → grünen Button **Run workflow** klicken.
4. Nach etwa einer Minute zeigt ein grüner Haken, dass der Lauf fertig ist. Die Kalender-Apps holen die neue Datei beim nächsten Abruf.

## Filter

Oben in `gottesdienste_ics.py` stehen drei Listen. Standardmäßig sind alle leer, dann werden alle Termine übernommen.

- `ONLY_PLACES`: nur diese Orte, z. B. `["Basilika", "Hl. Geist"]`
- `ONLY_KEYWORDS`: nur Titel mit diesen Wörtern, z. B. `["Eucharistiefeier", "Abendmesse"]`
- `EXCLUDE_KEYWORDS`: diese Titel auslassen, z. B. `["Schülermesse", "Beichtgelegenheit"]`

Zum Ändern in GitHub auf die Datei klicken, das Stift-Symbol wählen, Liste anpassen und speichern.
Ein geänderter Filter wirkt sofort für den Zeitraum, den die Seite gerade zeigt. Ältere, bereits gesammelte Termine in `events.json` bleiben unverändert bestehen. Wer sie loswerden will, löscht `events.json` und startet einen Lauf von Hand.

## Wenn es mal nicht mehr klappt

- Ändert die Gemeinde den Seitenaufbau, findet das Skript keine Termine. Der Lauf schlägt dann fehl (GitHub schickt eine Mail), und der bisherige Kalender bleibt unverändert bestehen. Dann muss der Parser in `gottesdienste_ics.py` angepasst werden.
- Pausiert GitHub die geplanten Läufe nach langer Inaktivität des Repos, hilft ein Klick auf **Enable workflow** im Reiter Actions.

## Datenschutz

Das Repo ist öffentlich, weil Kalender-Apps die Datei sonst nicht abonnieren können. Es enthält nur die ohnehin öffentlichen Gottesdienstzeiten und keine persönlichen Daten. Private Termine gehören nicht in diesen Feed.
