# Gottesdienste Weingarten als Kalender-Abo

Ein Skript liest zweimal pro Woche (sonntags und donnerstags) https://katholisch-weingarten.de/gottesdienste/ und erzeugt `gottesdienste.ics`.

## Einrichtung (einmalig, ca. 5 Minuten)

1. Auf github.com ein **öffentliches** Repository anlegen, z. B. `gottesdienste-kalender`.
2. Diese Dateien hochladen: `gottesdienste_ics.py`, `README.md` und den Ordner `.github/workflows/` mit `update.yml`
   (der Ordnername beginnt mit Punkt, beim Web-Upload ggf. über „Create new file" und den Pfad `.github/workflows/update.yml` eintippen).
3. Reiter **Actions** öffnen, Workflows aktivieren, „Gottesdienste-Kalender aktualisieren" wählen und **Run workflow** klicken.
   Danach liegen `gottesdienste.ics` und `events.json` im Repo.
4. Abo-URL:
   `https://raw.githubusercontent.com/<DEIN-NAME>/<REPO>/main/gottesdienste.ics`

## Abonnieren

- **Apple Kalender (iPhone):** Einstellungen → Kalender → Accounts → Account hinzufügen → Andere → Kalenderabo hinzufügen → URL einfügen.
- **Google Kalender (Web):** Weitere Kalender (+) → Per URL → URL einfügen. Google aktualisiert Abos nur alle 12–24 Stunden.
- **Proton Kalender (Web):** Weitere Kalender (+) → Kalender per URL hinzufügen.
- **Android/GrapheneOS:** über Google-/Proton-Kalender oder eine App wie ICSx5 (URL abonnieren).

## Filter

Oben in `gottesdienste_ics.py` gibt es drei Listen: `ONLY_PLACES`, `ONLY_KEYWORDS`, `EXCLUDE_KEYWORDS`.
Beispiel nur Basilika ohne Schülermessen: `ONLY_PLACES = ["Basilika"]`, `EXCLUDE_KEYWORDS = ["Schülermesse"]`.

## Wenn es mal nicht mehr klappt

Ändert die Gemeinde den Seitenaufbau, findet das Skript keine Termine, der Lauf schlägt fehl (GitHub schickt eine Mail)
und der bisherige Kalender bleibt unverändert bestehen.
