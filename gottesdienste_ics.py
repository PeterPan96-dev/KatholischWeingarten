#!/usr/bin/env python3
"""Liest die Gottesdienste-Seite der Seelsorgeeinheit Weingarten und erzeugt einen ICS-Kalender.

Aufruf:  python gottesdienste_ics.py
Ausgabe: gottesdienste.ics  (abonnierbar) und events.json (gesammelter Bestand)

Die Seite zeigt nur ca. eine Woche. Damit der Kalender nicht jede Woche "leer läuft",
werden alle bisher gesehenen Termine in events.json gesammelt und zusammengeführt.
"""
import hashlib
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

URL = "https://katholisch-weingarten.de/gottesdienste/"
TZ = ZoneInfo("Europe/Berlin")
OUT_ICS = Path("gottesdienste.ics")
OUT_JSON = Path("events.json")
CAL_NAME = "Gottesdienste Weingarten"
KEEP_DAYS = 60            # Termine, die älter sind, fliegen aus dem Bestand
DEFAULT_DURATION_MIN = 60

# ---------------------------------------------------------------- Filter ----
# Leer lassen = alles übernehmen. Vergleich ohne Groß-/Kleinschreibung.
ONLY_PLACES = []          # z. B. ["Basilika"] oder ["Basilika", "St. Maria"]
ONLY_KEYWORDS = []        # z. B. ["Eucharistiefeier", "Abendmesse"]
EXCLUDE_KEYWORDS = []     # z. B. ["Schülermesse", "Beichtgelegenheit"]
# ---------------------------------------------------------------------------

MONTHS = {m: i + 1 for i, m in enumerate(
    ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
     "September", "Oktober", "November", "Dezember"])}
WEEKDAYS = "Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag"
MONTH_RE = "|".join(MONTHS)

RE_WEEK = re.compile(rf"(\d{{1,2}})\.\s*(?:({MONTH_RE})\s*)?(?:(20\d\d)\s*)?bis\s*(\d{{1,2}})\.\s*({MONTH_RE})\s*(20\d\d)")
RE_DAY = re.compile(rf"^(?:{WEEKDAYS}),\s*(\d{{1,2}})\.\s*({MONTH_RE})(?:,\s*(.*))?$")
RE_EVENT = re.compile(r"^(\d{1,2})[.:](\d{2})\s*Uhr\s+([^:]{2,40}):\s*(.+)$")
RE_END = re.compile(r"\bbis\s+(\d{1,2})[.:](\d{2})\s*Uhr")


def clean(line: str) -> str:
    line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)     # Markdown-Links
    line = line.replace("**", "").replace("\xa0", " ")
    line = re.sub(r"\s*\((?:s\.|siehe)\s*Artikel\)", "", line)  # "(s. Artikel)" entfernen
    return re.sub(r"\s+", " ", line).strip()


def fetch_text() -> str:
    import requests
    from bs4 import BeautifulSoup
    r = requests.get(URL, timeout=30, headers={
        "User-Agent": "gottesdienste-ics/1.0 (privater Kalender-Feed, 1x taeglich)"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    # <br> und Block-Elemente zu Zeilenumbrüchen
    return soup.get_text("\n")


def passes_filter(place: str, title: str) -> bool:
    p, t = place.lower(), title.lower()
    if ONLY_PLACES and not any(x.lower() in p for x in ONLY_PLACES):
        return False
    if ONLY_KEYWORDS and not any(x.lower() in t for x in ONLY_KEYWORDS):
        return False
    if any(x.lower() in t for x in EXCLUDE_KEYWORDS):
        return False
    return True


def parse(text: str, today: date | None = None) -> list[dict]:
    today = today or date.today()
    lines = [clean(l) for l in text.splitlines()]
    lines = [l for l in lines if l]

    # Jahr aus der Wochenüberschrit ("7. bis 14. November 2026") ableiten
    year, start_month = today.year, None
    for l in lines:
        m = RE_WEEK.search(l)
        if m:
            end_year = int(m.group(6))
            start_month = MONTHS.get(m.group(2)) or MONTHS[m.group(5)]
            year = int(m.group(3)) if m.group(3) else (
                end_year - 1 if start_month > MONTHS[m.group(5)] else end_year)
            break

    events, current, holy = [], None, ""
    for l in lines:
        d = RE_DAY.match(l)
        if d:
            day, month = int(d.group(1)), MONTHS[d.group(2)]
            y = year + 1 if (start_month and month < start_month) else year
            current, holy = date(y, month, day), (d.group(3) or "").strip()
            continue
        if current is None:
            continue
        e = RE_EVENT.match(l)
        if not e:
            continue
        hh, mm, place, title = int(e.group(1)), int(e.group(2)), e.group(3).strip(), e.group(4).strip()
        start = datetime(current.year, current.month, current.day, hh, mm, tzinfo=TZ)
        end = start + timedelta(minutes=DEFAULT_DURATION_MIN)
        em = RE_END.search(title)
        if em:
            cand = start.replace(hour=int(em.group(1)), minute=int(em.group(2)))
            if cand > start:
                end = cand
            title = re.sub(r"\s+", " ", RE_END.sub("", title)).strip()
        if not passes_filter(place, title):
            continue
        desc = f"Gottesdienste Weingarten – {place}" + (f"\n{holy}" if holy else "") + f"\nQuelle: {URL}"
        events.append({
            "uid": hashlib.sha1(f"{start.isoformat()}|{place}|{title}".encode()).hexdigest()[:20]
                   + "@gottesdienste-ics",
            "start": start.isoformat(), "end": end.isoformat(),
            "summary": f"{title} ({place})", "location": place, "description": desc,
        })
    return events


def merge(old: list[dict], new: list[dict], today: date | None = None) -> list[dict]:
    today = today or date.today()
    cutoff = datetime.combine(today - timedelta(days=KEEP_DAYS), datetime.min.time(), tzinfo=TZ)
    # Wochenfenster der aktuellen Seite: alles Alte in diesem Fenster wird durch die neue Version ersetzt
    # (so verschwinden abgesagte/verschobene Termine wieder)
    if new:
        lo = min(datetime.fromisoformat(e["start"]) for e in new).replace(hour=0, minute=0)
        hi = max(datetime.fromisoformat(e["start"]) for e in new).replace(hour=23, minute=59)
        old = [e for e in old if not (lo <= datetime.fromisoformat(e["start"]) <= hi)]
    by_uid = {e["uid"]: e for e in old}
    by_uid.update({e["uid"]: e for e in new})
    kept = [e for e in by_uid.values() if datetime.fromisoformat(e["start"]) >= cutoff]
    return sorted(kept, key=lambda e: e["start"])


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line: str) -> str:
    raw, out = line.encode(), []
    while len(raw) > 75:
        cut = 75
        while raw[cut] & 0xC0 == 0x80:      # nicht mitten in einem UTF-8-Zeichen trennen
            cut -= 1
        out.append(raw[:cut].decode())
        raw = b" " + raw[cut:]
    out.append(raw.decode())
    return "\r\n".join(out)


def utc(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def to_ics(events: list[dict]) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//gottesdienste-ics//DE", "CALSCALE:GREGORIAN",
           "METHOD:PUBLISH", f"X-WR-CALNAME:{esc(CAL_NAME)}", "X-WR-TIMEZONE:Europe/Berlin",
           "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H"]
    for e in events:
        out += ["BEGIN:VEVENT", f"UID:{e['uid']}", f"DTSTAMP:{stamp}",
                f"DTSTART:{utc(e['start'])}", f"DTEND:{utc(e['end'])}",
                f"SUMMARY:{esc(e['summary'])}", f"LOCATION:{esc(e['location'])}",
                f"DESCRIPTION:{esc(e['description'])}", "END:VEVENT"]
    out.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in out) + "\r\n"


def main() -> int:
    new = parse(fetch_text())
    if not new:
        print("Keine Termine gefunden – Seitenstruktur geändert? Bestand bleibt unverändert.", file=sys.stderr)
        return 1
    old = json.loads(OUT_JSON.read_text(encoding="utf-8")) if OUT_JSON.exists() else []
    events = merge(old, new)
    if events == old and OUT_ICS.exists():
        print("Keine Änderungen.")
        return 0
    OUT_JSON.write_text(json.dumps(events, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_ICS.write_bytes(to_ics(events).encode("utf-8"))
    print(f"{len(new)} Termine von der Seite, {len(events)} im Kalender.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
