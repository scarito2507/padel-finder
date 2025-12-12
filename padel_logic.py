# padel_logic.py

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any, Tuple, Optional


# =====================================================
# ⚙️ CONFIG GÉNÉRALE
# =====================================================

# ID activité padel côté Doinsport (d’après tes HAR)
DOINSPORT_ACTIVITY_ID = "ce8c306e-224a-4f24-aa9d-6500580924dc"
DOINSPORT_BOOKING_TYPE = "unique"

# Clubs Doinsport à interroger
DOINSPORT_CLUBS = [
    {
        "name": "Stadium Padel Caen",
        "club_id": "cda49d78-525c-4f66-b6f8-43001c8a6ad7",
        "from": "09:00",
        "to": "23:30",
    },
    {
        "name": "La Pommeraie",
        "club_id": "0e5db60e-1735-4f5e-92f4-b457ac72f912",
        "from": "09:00:00",
        "to": "23:00:00",
    },
    {
        "name": "Area Padel Caen",
        "club_id": "b78e6114-96e3-4f20-82c8-cc213cdd47d3",
        "from": "10:00",
        "to": "23:00",
    },
]

DOINSPORT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (padel-bot perso)",
    "Accept": "application/json, text/plain, */*",
    "X-Locale": "fr",
    "Content-Language": "fr",
}

DOINSPORT_BASE_URL = "https://api-v3.doinsport.club/clubs/playgrounds/plannings/{date}"

# =====================================================
# 🎾 CONFIG R PADEL ARENA (mymobileapp.fr)
# =====================================================

RPADEL_URL = "https://rpadel-arena.mymobileapp.fr/loadcalendrier_capsule_regroupe.asp"

RPADEL_ID_SPORT = "2"     # padel

# ⚠️ À METTRE À JOUR si besoin (token & dd) depuis DevTools
RPADEL_LIVEXPERIENCE_TOKEN = (
    "lecXpRemQM2psT2JTFPeZOoQz7msqGAkobZvWFEBJg4PKuTdkx-xKyOfFQ5cBTB0wnyYjdE9A9QLCSwAJ0X-HNPUyDe8F5L1S8Tb7-11122025112819785"
)
RPADEL_DD_VALUE = "1765450577011"

RPADEL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (padel-bot perso)",
    "Accept": "text/html, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://rpadel-arena.mymobileapp.fr",
    "Referer": "https://rpadel-arena.mymobileapp.fr/",
}

RPADEL_COOKIES = {
    # si besoin tu peux mettre des cookies ici, souvent pas nécessaire
}

# =====================================================
# 🎾 CONFIG PADELSHOT (Matchpoint)
# =====================================================

PADELSHOT_BASE_URL = "https://padelshot-fr.matchpoint.com.es"
PADELSHOT_ID_CUADRO = "4"  # Padel Caen Mondeville

PADELSHOT_HEADERS_HTML = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

PADELSHOT_HEADERS_JSON = {
    "User-Agent": "Mozilla/5.0 (padel-bot perso)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/json; charset=utf-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": PADELSHOT_BASE_URL,
    "Referer": f"{PADELSHOT_BASE_URL}/Booking/grid.aspx",
}


# =====================================================
# ⏱️ OUTILS TEMPS
# =====================================================

def hhmm_to_minutes(hhmm: str) -> int:
    """Convertit '13:30' ou '13:30:00' -> minutes depuis minuit."""
    parts = hhmm.split(":")
    if len(parts) < 2:
        return -1
    h = int(parts[0])
    m = int(parts[1])
    return h * 60 + m


def minutes_to_hhmm(minutes: int) -> str:
    """Convertit minutes depuis minuit -> 'HH:MM'."""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def iso_to_fr_date(date_iso: str) -> str:
    """Convertit '2025-12-12' -> '12/12/2025'."""
    y, m, d = date_iso.split("-")
    return f"{d}/{m}/{y}"


# =====================================================
# 🔍 D O I N S P O R T
# =====================================================

def check_doinsport_club(
    club_conf: Dict[str, Any],
    target_date_iso: str,
    min_from: int,
    min_to: int,
    allowed_durations_set: set,
) -> Dict[str, Any]:
    """
    Retourne un dict :
    {
        "club_name": "...",
        "slots": [ { startAt, duration_min, terrain, price_pp, participant_count }, ... ]
    }
    en ne gardant que :
      - startAt == fenêtre début
      - durée dans allowed_durations_set
      - créneau complètement dans [min_from, min_to]
    """
    club_name = club_conf["name"]
    club_id = club_conf["club_id"]
    from_param = club_conf.get("from", "08:00")
    to_param = club_conf.get("to", "23:30")

    url = DOINSPORT_BASE_URL.format(date=target_date_iso)
    params = {
        "club.id": club_id,
        "from": from_param,
        "to": to_param,
        "activities.id": DOINSPORT_ACTIVITY_ID,
        "bookingType": DOINSPORT_BOOKING_TYPE,
    }

    resp = requests.get(url, headers=DOINSPORT_HEADERS, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    terrains = data.get("hydra:member", [])
    slots_out = []

    for terrain in terrains:
        terrain_name = terrain.get("name", "Terrain ?")
        activities = terrain.get("activities", [])

        if isinstance(activities, dict):
            activities_iter = activities.values()
        else:
            activities_iter = activities

        for act in activities_iter:
            slots = act.get("slots", [])
            for slot in slots:
                start_at = slot.get("startAt")  # "13:00" ou "13:00:00"
                if not start_at:
                    continue

                start_min = hhmm_to_minutes(start_at)
                if start_min < 0:
                    continue

                # On veut que ça commence EXACTEMENT à la fenêtre
                if start_min != min_from:
                    continue

                prices = slot.get("prices", [])
                for p in prices:
                    if not p.get("bookable"):
                        continue

                    duration_seconds = p.get("duration")
                    if duration_seconds is None:
                        continue

                    duration_min = int(duration_seconds) // 60

                    # Durée autorisée ?
                    if allowed_durations_set and duration_min not in allowed_durations_set:
                        continue

                    end_min = start_min + duration_min

                    # Doit tenir dans la fenêtre
                    if end_min > min_to:
                        continue

                    price_per_participant = p.get("pricePerParticipant")
                    participant_count = p.get("participantCount")

                    display_time = f"{start_at[:2]}:{start_at[3:5]}"

                    slots_out.append({
                        "terrain": terrain_name,
                        "startAt": display_time,
                        "start_min": start_min,
                        "duration_min": duration_min,
                        "price_per_participant": price_per_participant,
                        "participant_count": participant_count,
                    })

    slots_out.sort(key=lambda x: (x["start_min"], x["duration_min"]))
    return {"club_name": club_name, "slots": slots_out}


# =====================================================
# 🎾 R  P A D E L  A R E N A
# =====================================================

def extract_duration_from_onclick(onclick_text: str) -> int:
    """
    Essaie d'extraire la durée en minutes depuis l'attribut onclick.
    Exemple: "document.getElementById('duree').value='90';choosePop(..."
    """
    if not onclick_text:
        return -1
    m = re.search(r"value='(\d+)'", onclick_text)
    if not m:
        return -1
    try:
        return int(m.group(1))
    except ValueError:
        return -1


def data_heure_to_minutes(data_heure: str) -> int:
    """Convertit '1300' -> 780, '1530' -> 930."""
    if len(data_heure) != 4 or not data_heure.isdigit():
        return -1
    h = int(data_heure[:2])
    m = int(data_heure[2:])
    return h * 60 + m


def check_rpadel(
    target_date_iso: str,
    min_from: int,
    min_to: int,
    allowed_durations_set: set,
) -> Dict[str, Any]:
    """
    R Padel Arena : ne renvoie que les créneaux :
      - commençant à min_from
      - durée autorisée
      - tenant dans la fenêtre.
    """
    target_date_fr = iso_to_fr_date(target_date_iso)

    data = {
        "myDate": target_date_fr,
        # la durée envoyée n'est pas critique : on filtre ensuite
        "duree": "90",
        "id_sport": RPADEL_ID_SPORT,
        "livexperience_site_token": RPADEL_LIVEXPERIENCE_TOKEN,
        "dd": RPADEL_DD_VALUE,
    }

    resp = requests.post(
        RPADEL_URL,
        headers=RPADEL_HEADERS,
        cookies=RPADEL_COOKIES,
        data=data,
        timeout=10,
    )
    resp.raise_for_status()

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    boutons = soup.select("button.btn-horaires")
    slots_out = []

    for btn in boutons:
        data_heure = btn.get("data-heure")  # ex: "1400"
        if not data_heure:
            continue

        start_min = data_heure_to_minutes(data_heure)
        if start_min < 0:
            continue

        # Doit commencer exactement à la fenêtre
        if start_min != min_from:
            continue

        onclick = btn.get("onclick", "")
        duration_min = extract_duration_from_onclick(onclick)

        if duration_min <= 0:
            texte_btn = btn.get_text(" ", strip=True)
            m = re.search(r"(\d+)\s*mn", texte_btn)
            if m:
                duration_min = int(m.group(1))

        if duration_min <= 0:
            continue

        # Durée autorisée ?
        if allowed_durations_set and duration_min not in allowed_durations_set:
            continue

        end_min = start_min + duration_min
        if end_min > min_to:
            continue

        display_time = f"{data_heure[:2]}:{data_heure[2:]}"
        h1 = btn.find("h1")
        texte_h1 = h1.get_text(" ", strip=True) if h1 else ""

        slots_out.append({
            "startAt": display_time,
            "start_min": start_min,
            "duration_min": duration_min,
            "raw_text": texte_h1,
        })

    slots_out.sort(key=lambda x: (x["start_min"], x["duration_min"]))
    return {"club_name": "R Padel Arena", "slots": slots_out}


# =====================================================
# 🎾 P A D E L S H O T  (Matchpoint)
# =====================================================

def _debug_search_key(html: str) -> Optional[str]:
    """Essaie plusieurs patterns pour trouver la clé dans le HTML."""
    m = re.search(r'"key"\s*:\s*"([^"]+)"', html)
    if m:
        return m.group(1)

    m = re.search(r"key\s*[:=]\s*'([^']+)'", html)
    if m:
        return m.group(1)

    m = re.search(r"(eNEe29kXfZ[A-Za-z0-9+/=]+)", html)
    if m:
        return m.group(1)

    return None


def get_dynamic_key(session: requests.Session, id_cuadro: str) -> str:
    """
    Récupère la 'key' dynamique depuis grid.aspx.
    Pas de prints pour ne pas polluer la console.
    """
    url1 = f"{PADELSHOT_BASE_URL}/Booking/grid.aspx"
    resp1 = session.get(url1, headers=PADELSHOT_HEADERS_HTML, timeout=10)
    resp1.raise_for_status()
    html1 = resp1.text

    key = _debug_search_key(html1)
    if key:
        return key

    # 2ème essai avec ?idCuadro
    url2 = f"{PADELSHOT_BASE_URL}/Booking/grid.aspx?idCuadro={id_cuadro}"
    resp2 = session.get(url2, headers=PADELSHOT_HEADERS_HTML, timeout=10)
    resp2.raise_for_status()
    html2 = resp2.text

    key = _debug_search_key(html2)
    if key:
        return key

    raise RuntimeError("Impossible de trouver la clé 'key' pour Padelshot.")


def check_padelshot(
    target_date_iso: str,
    min_from: int,
    min_to: int,
    allowed_durations_set: set,
) -> Dict[str, Any]:
    """
    Padelshot Caen Mondeville :
    - Récupère la clé dynamique
    - Appelle ObtenerCuadro
    - Analyse les HorariosFijos + Ocupaciones
    - Ne propose que les créneaux :
        * commençant exactement à min_from
        * dont la durée est autorisée
        * et qui correspondent à un HorarioFijo exact
        * et non occupés (pas d'Ocupacion qui chevauche)
    """
    target_date_fr = iso_to_fr_date(target_date_iso)

    session = requests.Session()
    key = get_dynamic_key(session, PADELSHOT_ID_CUADRO)

    payload = {
        "idCuadro": PADELSHOT_ID_CUADRO,
        "fecha": target_date_fr,
        "key": key,
    }

    resp = session.post(
        f"{PADELSHOT_BASE_URL}/booking/srvc.aspx/ObtenerCuadro",
        headers=PADELSHOT_HEADERS_JSON,
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()

    data = resp.json()
    cuadro = data.get("d", {})
    columnas = cuadro.get("Columnas", [])

    results_slots = []

    for col in columnas:
        terrain_name = col.get("TextoPrincipal", "Terrain ?")

        # Ocupaciones = réservations existantes
        busy_intervals: List[Tuple[int, int]] = []
        for occ in col.get("Ocupaciones", []):
            sh = occ.get("StrHoraInicioMostrar") or occ.get("StrHoraInicio")
            eh = occ.get("StrHoraFinMostrar") or occ.get("StrHoraFin")
            if not sh or not eh:
                continue
            s = hhmm_to_minutes(sh)
            e = hhmm_to_minutes(eh)
            if s < 0 or e <= s:
                continue
            busy_intervals.append((s, e))

        # HorariosFijos = créneaux possibles pour ce terrain
        horarios = col.get("HorariosFijos", [])

        for hf in horarios:
            sh = hf.get("StrHoraInicioMostrar") or hf.get("StrHoraInicio")
            eh = hf.get("StrHoraFinMostrar") or hf.get("StrHoraFin")
            if not sh or not eh:
                continue

            start_min = hhmm_to_minutes(sh)
            end_min = hhmm_to_minutes(eh)
            if start_min < 0 or end_min <= start_min:
                continue

            duration_min = end_min - start_min

            # Doit commencer exactement à la fenêtre
            if start_min != min_from:
                continue

            # Durée autorisée ?
            if allowed_durations_set and duration_min not in allowed_durations_set:
                continue

            # Doit tenir dans la fenêtre [min_from, min_to]
            if end_min > min_to:
                continue

            # Vérifier qu'aucune Ocupacion ne chevauche ce créneau
            overlapped = False
            for bs, be in busy_intervals:
                if not (be <= start_min or bs >= end_min):
                    overlapped = True
                    break

            if overlapped:
                continue

            results_slots.append({
                "terrain": terrain_name,
                "startAt": minutes_to_hhmm(start_min),
                "start_min": start_min,
                "duration_min": duration_min,
            })

    results_slots.sort(key=lambda x: (x["start_min"], x["duration_min"]))
    return {"club_name": "Padelshot Caen Mondeville", "slots": results_slots}


# =====================================================
# 🧠 FONCTION PRINCIPALE APPELÉE PAR FLASK
# =====================================================

def search_all(
    date_iso: str,
    window_from: str,
    window_to: str,
    allowed_durations_min: List[int],
) -> Dict[str, Any]:
    """
    Recherche les créneaux sur tous les complexes.

    Retourne un dict du type :
    {
        "date_iso": ...,
        "window_from": ...,
        "window_to": ...,
        "durations": [...],
        "doinsport": [
            { "club_name": "...", "slots": [...] },
            ...
        ],
        "rpadel": { "club_name": "...", "slots": [...] },
        "padelshot": { "club_name": "...", "slots": [...] },
        "errors": [ "message éventuel", ... ]
    }
    """
    min_from = hhmm_to_minutes(window_from)
    min_to = hhmm_to_minutes(window_to)
    allowed_set = set(int(d) for d in allowed_durations_min if int(d) > 0)

    out: Dict[str, Any] = {
        "date_iso": date_iso,
        "window_from": window_from,
        "window_to": window_to,
        "durations": sorted(list(allowed_set)),
        "doinsport": [],
        "rpadel": None,
        "padelshot": None,
        "errors": [],
    }

    # --- Doinsport ---
    for club in DOINSPORT_CLUBS:
        try:
            res = check_doinsport_club(club, date_iso, min_from, min_to, allowed_set)
            out["doinsport"].append(res)
        except Exception as e:
            out["errors"].append(f"Doinsport - {club['name']}: {e}")

    # --- R Padel Arena ---
    try:
        out["rpadel"] = check_rpadel(date_iso, min_from, min_to, allowed_set)
    except Exception as e:
        out["errors"].append(f"R Padel Arena: {e}")

    # --- Padelshot ---
    try:
        out["padelshot"] = check_padelshot(date_iso, min_from, min_to, allowed_set)
    except Exception as e:
        out["errors"].append(f"Padelshot: {e}")

    return out


if __name__ == "__main__":
    # Petit test en ligne de commande si tu veux
    res = search_all("2025-12-12", "18:00", "19:30", [90])
    print("Date:", res["date_iso"])
    print("Fenêtre:", res["window_from"], "->", res["window_to"], "Durées:", res["durations"])
    print()

    for club in res["doinsport"]:
        print(club["club_name"])
        if not club["slots"]:
            print("  Aucun créneau.")
        else:
            for s in club["slots"]:
                p = s["price_per_participant"] or 0
                c = s["participant_count"] or 0
                print(
                    f"  - {s['startAt']} | {s['duration_min']} min | "
                    f"{s['terrain']} | {p/100:.2f} € / joueur x {c}"
                )
        print()

    if res["rpadel"]:
        print(res["rpadel"]["club_name"])
        if not res["rpadel"]["slots"]:
            print("  Aucun créneau.")
        else:
            for s in res["rpadel"]["slots"]:
                print(f"  - {s['startAt']} | {s['duration_min']} min | {s['raw_text']}")
        print()

    if res["padelshot"]:
        print(res["padelshot"]["club_name"])
        if not res["padelshot"]["slots"]:
            print("  Aucun créneau.")
        else:
            for s in res["padelshot"]["slots"]:
                print(f"  - {s['startAt']} | {s['duration_min']} min | {s['terrain']}")
        print()

    if res["errors"]:
        print("Erreurs:")
        for e in res["errors"]:
            print(" -", e)
