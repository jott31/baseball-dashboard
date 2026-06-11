import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote
from datetime import datetime, timedelta, date as date_type
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="NPB · KBO Scores",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; background:#0a0a0a; color:#e8e8e8; }
.block-container { padding-top:1.2rem !important; max-width:1100px; }
.masthead { display:flex; align-items:baseline; gap:14px; border-bottom:2px solid #1e1e1e; padding-bottom:.7rem; margin-bottom:1rem; }
.masthead-title { font-family:'Bebas Neue',sans-serif; font-size:2.4rem; letter-spacing:.08em; color:#fff; line-height:1; }
.masthead-sub { font-family:'IBM Plex Mono',monospace; font-size:.62rem; color:#444; letter-spacing:.2em; text-transform:uppercase; }
.section-label { font-family:'IBM Plex Mono',monospace; font-size:.58rem; letter-spacing:.24em; color:#444; text-transform:uppercase; margin-bottom:.5rem; margin-top:.3rem; }
.card { background:#111; border:1px solid #1e1e1e; border-radius:6px; padding:14px 18px; margin-bottom:8px; }
.card-venue { font-family:'IBM Plex Mono',monospace; font-size:.58rem; letter-spacing:.15em; color:#333; text-transform:uppercase; margin-bottom:8px; }
.card-teams { display:flex; justify-content:space-between; align-items:center; gap:12px; }
.team-block { flex:1; }
.team-name { font-family:'Bebas Neue',sans-serif; font-size:1.4rem; letter-spacing:.04em; line-height:1; }
.team-name.winner { color:#f0f0f0; }
.team-name.loser  { color:#383838; }
.team-name.neutral{ color:#aaa; }
.score-mid { display:flex; gap:14px; align-items:center; font-family:'IBM Plex Mono',monospace; }
.score { font-size:2.1rem; font-weight:600; min-width:1.8ch; text-align:center; }
.score.winner { color:#f0f0f0; }
.score.loser  { color:#282828; }
.score.neutral{ color:#888; }
.score-sep { color:#252525; font-size:1rem; }
.card-footer { display:flex; justify-content:space-between; align-items:center; margin-top:10px; padding-top:8px; border-top:1px solid #181818; }
.card-meta { font-family:'IBM Plex Mono',monospace; font-size:.6rem; color:#333; letter-spacing:.1em; }
.card-links { display:flex; gap:10px; flex-wrap:wrap; }
.ext-link { font-family:'IBM Plex Mono',monospace; font-size:.6rem; letter-spacing:.08em; color:#444; text-decoration:none; border-bottom:1px solid #222; white-space:nowrap; }
.ext-link:hover { color:#bbb; border-color:#555; }
.linescore-wrap { overflow-x:auto; margin:10px 0 4px 0; }
.linescore { border-collapse:collapse; width:100%; font-family:'IBM Plex Mono',monospace; font-size:.65rem; }
.linescore th { color:#2a2a2a; font-weight:400; padding:3px 6px; text-align:center; border-bottom:1px solid #1a1a1a; }
.linescore td { padding:3px 6px; text-align:center; color:#666; }
.linescore td.team-col { text-align:left; color:#3a3a3a; min-width:80px; }
.linescore td.tot { font-weight:600; color:#aaa; border-left:1px solid #1e1e1e; }
.box-title { font-family:'IBM Plex Mono',monospace; font-size:.6rem; letter-spacing:.2em; color:#555; text-transform:uppercase; margin:14px 0 4px 0; }
.boxscore-wrap { overflow-x:auto; margin:4px 0 10px 0; }
.boxscore { border-collapse:collapse; width:100%; font-family:'IBM Plex Mono',monospace; font-size:.64rem; }
.boxscore th { color:#2e2e2e; font-weight:400; padding:3px 7px; text-align:right; border-bottom:1px solid #1a1a1a; }
.boxscore th.pname { text-align:left; }
.boxscore td { padding:3px 7px; text-align:right; color:#777; }
.boxscore td.pname { text-align:left; min-width:120px; white-space:nowrap; }
.boxscore td.ppos { text-align:left; color:#3a3a3a; min-width:42px; }
.player-link { color:#9aa6b2; text-decoration:none; border-bottom:1px dotted #2c3338; }
.player-link:hover { color:#e0e0e0; border-color:#888; }
.player-plain { color:#777; }
.notes-line { font-family:'IBM Plex Mono',monospace; font-size:.62rem; color:#555; letter-spacing:.05em; margin:3px 0; line-height:1.6; }
.notes-key { color:#777; font-weight:600; }
.no-games { font-family:'IBM Plex Mono',monospace; font-size:.75rem; color:#2a2a2a; letter-spacing:.12em; padding:28px 0; text-align:center; border:1px dashed #181818; border-radius:6px; margin:8px 0; }
.info-box { font-family:'IBM Plex Mono',monospace; font-size:.7rem; color:#555; letter-spacing:.1em; background:#111; border:1px solid #1e1e1e; border-radius:5px; padding:10px 14px; margin-bottom:12px; line-height:1.7; }
.err-box  { font-family:'IBM Plex Mono',monospace; font-size:.7rem; color:#884444; letter-spacing:.1em; background:#1a1010; border:1px solid #331a1a; border-radius:5px; padding:10px 14px; margin-bottom:8px; line-height:1.7; }
#MainMenu, footer, header { visibility:hidden; }
div[data-testid="stDecoration"] { display:none; }
div[data-baseweb="tab-list"] { gap:2px; border-bottom:1px solid #1a1a1a !important; }
div[data-baseweb="tab"] { background:transparent !important; font-family:'IBM Plex Mono',monospace !important; font-size:.7rem !important; letter-spacing:.12em !important; color:#444 !important; padding:8px 16px !important; border-bottom:2px solid transparent !important; }
div[aria-selected="true"][data-baseweb="tab"] { color:#ddd !important; border-bottom:2px solid #ddd !important; background:transparent !important; }
</style>
""", unsafe_allow_html=True)

JST = ZoneInfo("Asia/Tokyo")
KST = ZoneInfo("Asia/Seoul")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

def now_jst():
    return datetime.now(JST)

def fmt_date(d: str) -> str:
    # NOTE: avoid "%-d" — Linux-only, crashes on Windows
    try:
        dt = datetime.strptime(d, "%Y-%m-%d")
        return f"{dt.strftime('%A, %B')} {dt.day}"
    except Exception:
        return d

def winner_cls(a, h):
    try:
        ai, hi = int(a), int(h)
        if hi > ai: return "loser", "winner"
        if ai > hi: return "winner", "loser"
        return "neutral", "neutral"
    except Exception:
        return "neutral", "neutral"

def get(url, referer="https://npb.jp/"):
    return requests.get(url, headers={**HEADERS, "Referer": referer}, timeout=14)


# ══════════════════════════════════════════════════════════════════════════════
# PLAYER LINKS — Baseball Reference
#
# BR is used (not FanGraphs) because BR's Register covers essentially every NPB
# and KBO player while FanGraphs has no NPB pages. We link to BR's search
# endpoint with the player's name; BR resolves it (landing on the player page
# when unambiguous). BR's player pages/titles use romanized GIVEN-name-first
# order ("Koki Kitayama"), so passing the full name — not a bare surname —
# is what makes the search land on the right person.
#
# Links open in the USER'S browser, so Cloudflare datacenter-IP blocking of
# baseball-reference.com is irrelevant here.
# ══════════════════════════════════════════════════════════════════════════════

def br_search_url(name: str) -> str:
    return "https://www.baseball-reference.com/search/search.fcgi?search=" + quote(name.strip())

def br_link(search_name: str, display: str) -> str:
    """Anchor linking `display` text to a BR search for `search_name`."""
    if not search_name.strip():
        return f'<span class="player-plain">{display}</span>'
    return (f'<a class="player-link" href="{br_search_url(search_name)}" '
            f'target="_blank">{display}</a>')


# ══════════════════════════════════════════════════════════════════════════════
# NPB FULL-NAME REGISTER
#
# Problem: NPB.jp box scores print only surnames ("Kitayama", "Kiyomiya"),
# which makes BR searches unreliable (many players share a surname).
#
# Solution: NPB.jp publishes an alphabetical ACTIVE-PLAYER register at
#   https://npb.jp/bis/eng/players/active/index_{a..z}.html
# Each entry is:  "{num} {Position}[ (*)]{Surname}, {Given}{Full Team Name}"
# linking to that player's NPB page. We fetch all 26 letter pages ONCE
# (cached 24h) and build  (team_short, surname_lower) -> [candidates].
#
# A box-score row gives us the surname AND the team (from the team-label
# table), so we match on (team, surname). When exactly one player matches we
# expand to the full name for the BR link; when 0 or >1 match (e.g. two
# "Kikuchi" on Hiroshima) we fall back to searching the surname alone.
#
# Same npb.jp domain that already works server-side — no new blocking risk.
# ══════════════════════════════════════════════════════════════════════════════

# Full register team name  ->  short label used in box scores / linescore
NPB_TEAM_TO_SHORT = {
    "Yomiuri Giants": "Yomiuri",
    "Hanshin Tigers": "Hanshin",
    "YOKOHAMA DeNA BAYSTARS": "DeNA",
    "Yokohama DeNA BayStars": "DeNA",
    "Chunichi Dragons": "Chunichi",
    "Hiroshima Toyo Carp": "Hiroshima",
    "Tokyo Yakult Swallows": "Yakult",
    "Fukuoka SoftBank Hawks": "SoftBank",
    "Fukuoka Softbank Hawks": "SoftBank",
    "Hokkaido Nippon-Ham Fighters": "Nippon-Ham",
    "ORIX Buffaloes": "ORIX",
    "Tohoku Rakuten Golden Eagles": "Rakuten",
    "Saitama Seibu Lions": "Seibu",
    "Chiba Lotte Marines": "Lotte",
}

_NPB_TEAMS_ALT = "|".join(
    sorted((re.escape(t) for t in NPB_TEAM_TO_SHORT), key=len, reverse=True)
)
# Anchor text format inside the register, e.g.:
#   <a href=".../51755155.html">15 PitcherKitayama, KokiHokkaido Nippon-Ham Fighters</a>
_REGISTER_ENTRY = re.compile(
    r'href="(?P<url>https?://npb\.jp/bis/eng/players/\d+\.html)"[^>]*>\s*'
    r'\d+\s+(?:Pitcher|Catcher|Infielder|Outfielder)(?:\s*\(\*\))?\s*'
    r'(?P<surname>[^,<]+?),\s*(?P<given>[A-Za-z\'\-\. ]+?)'
    r'(?P<team>' + _NPB_TEAMS_ALT + r')\s*<',
    re.IGNORECASE,
)


@st.cache_data(ttl=86400, show_spinner=False)
def load_npb_register() -> dict:
    """
    Returns { f"{team_short}|{surname_lower}": [ {full, url}, ... ] }.
    Fetched once per day. Tolerant of individual page failures.
    """
    reg: dict[str, list[dict]] = {}
    for letter in "abcdefghijklmnopqrstuvwxyz":
        url = f"https://npb.jp/bis/eng/players/active/index_{letter}.html"
        try:
            r = get(url)
            if r.status_code != 200:
                continue
        except Exception:
            continue
        for m in _REGISTER_ENTRY.finditer(r.text):
            surname = m.group("surname").strip()
            given   = m.group("given").strip()
            team    = m.group("team")
            short   = NPB_TEAM_TO_SHORT.get(team, team)
            key     = f"{short}|{surname.lower()}"
            entry   = {"full": f"{given} {surname}", "url": m.group("url")}
            bucket  = reg.setdefault(key, [])
            if entry not in bucket:
                bucket.append(entry)
    return reg


def npb_full_name(register: dict, team_short: str, box_name: str):
    """
    Expand a box-score name ('Kitayama', 'K.Suzuki') to a full romanized
    name using the register. Returns (search_name, confident).
    - confident=True  -> search_name is the full 'Given Surname'
    - confident=False -> search_name is just the surname (best-effort)
    """
    surname = box_name.split(".")[-1].strip()  # drop initial prefixes
    cands = register.get(f"{team_short}|{surname.lower()}", [])
    if len(cands) == 1:
        return cands[0]["full"], True
    return surname, False


# ══════════════════════════════════════════════════════════════════════════════
# NPB — STEP 1: day-index page -> individual game links
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def get_npb_game_links(date_str: str) -> tuple[list[str], str]:
    year    = date_str[:4]
    compact = date_str.replace("-", "")
    day_url = f"https://npb.jp/bis/eng/{year}/games/gm{compact}.html"

    try:
        r = get(day_url)
    except Exception as e:
        return [], f"Network error fetching day index: {e}"

    if r.status_code == 404:
        return [], "No games page for this date (off-day or outside season)."
    if r.status_code != 200:
        return [], f"NPB.jp day page returned HTTP {r.status_code}."

    soup  = BeautifulSoup(r.text, "lxml")
    base  = f"https://npb.jp/bis/eng/{year}/games/"
    game_links = []
    pattern    = re.compile(rf"s{compact}\d{{5}}\.html")

    for a in soup.find_all("a", href=True):
        filename = a["href"].split("/")[-1]
        if pattern.match(filename):
            full_url = base + filename if not a["href"].startswith("http") else a["href"]
            if full_url not in game_links:
                game_links.append(full_url)

    return game_links, ""


# ══════════════════════════════════════════════════════════════════════════════
# NPB — STEP 2: parse each individual game page (scores, linescore, box, notes)
#
# Confirmed structure (live fetch s2026060701896.html, Jun 7 2026):
#   away listed FIRST; venue "Jingu | T - 2:33 ( 14:01 - 16:34 ) Att. ..."
#   linescore "Nippon-Ham 2 0 0 0 4 1 0 0 0 - 7 9 1"
#   Each team's box preceded by a one-cell table with the team SHORT name.
#   Batting header:  ["", AB, H, RBI, BB, HP, SO]
#   Pitching header: ["", IP, "", BF, H, BB, HB, SO, ER]  (blank col = frac IP)
#   Notes: first cell "WP :"/"LP :"/"S :"/"HR :"; HR continuation rows blank 1st.
# ══════════════════════════════════════════════════════════════════════════════

NPB_SHORT_NAMES = {
    "Yomiuri", "Hanshin", "DeNA", "Chunichi", "Hiroshima", "Yakult",
    "SoftBank", "Nippon-Ham", "ORIX", "Rakuten", "Seibu", "Lotte",
}
BAT_HEADER_KEYS = {"AB", "RBI"}
PIT_HEADER_KEYS = {"IP", "BF"}
STAT_HEADER_WORDS = {"AB", "IP", "H", "R", "E", "BB", "SO", "HP",
                     "HB", "ER", "BF", "WP", "LP", "HR", "ERA", "RBI", "S"}


def _direct_rows(tbl):
    rows = tbl.find_all("tr", recursive=False)
    for section in tbl.find_all(["tbody", "thead"], recursive=False):
        rows += section.find_all("tr", recursive=False)
    return rows

def _direct_cells(tr):
    return [c.get_text(strip=True) for c in tr.find_all(["th", "td"], recursive=False)]

def _split_player(name_cell: str) -> tuple[str, str]:
    if "," in name_cell:
        name, _, pos = name_cell.partition(",")
        return name.strip(), pos.strip()
    return name_cell.strip(), ""


@st.cache_data(ttl=300)
def parse_npb_game(game_url: str) -> dict:
    result = {
        "away": "", "home": "",
        "away_score": None, "home_score": None,
        "venue": "", "time": "", "status": "UNKNOWN",
        "linescore": [], "batting": [], "pitching": [], "notes": [],
        "game_url": game_url, "error": "",
    }

    try:
        r = get(game_url)
    except Exception as e:
        result["error"] = str(e)
        return result
    if r.status_code != 200:
        result["error"] = f"HTTP {r.status_code}"
        return result

    soup = BeautifulSoup(r.text, "lxml")

    # ── Team names + scores ──────────────────────────────────────────────────
    title   = soup.title.string if soup.title else ""
    title_m = re.search(r"\(Scores\)\s+(.+?)\s+vs\s+(.+?)(?:\s*\||\s*$)", title or "")

    score_rows = []
    for tr in soup.find_all("tr"):
        cells = [c for c in _direct_cells(tr) if c]
        if len(cells) < 2:
            continue
        last, second_last = cells[-1], cells[-2]
        if not re.match(r"^\d{1,2}$", last):
            continue
        if len(second_last) <= 3 or re.match(r"^\d", second_last):
            continue
        if second_last.upper() in STAT_HEADER_WORDS:
            continue
        if "," in second_last or "(" in second_last:
            continue
        score_rows.append((second_last, last))
    score_rows = score_rows[:2]

    if len(score_rows) >= 2:
        result["away"], result["home"] = score_rows[0][0], score_rows[1][0]
        result["away_score"], result["home_score"] = score_rows[0][1], score_rows[1][1]
        result["status"] = "FINAL"
    elif title_m:
        result["away"], result["home"] = title_m.group(1).strip(), title_m.group(2).strip()
        result["status"] = "SCHEDULED"

    # ── Venue + time ─────────────────────────────────────────────────────────
    for tbl in soup.find_all("table"):
        cells = [td.get_text(strip=True) for td in tbl.find_all("td") if td.get_text(strip=True)]
        if not cells:
            continue
        row_text = " ".join(cells)
        if re.search(r"\d{1,2}:\d{2}", row_text) and len(cells) >= 2:
            venue_candidate = cells[0]
            if not re.match(r"^(AB|IP|R|H|E|BB|SO|WP|LP|HR)$", venue_candidate) and len(venue_candidate) > 2:
                result["venue"] = venue_candidate
                time_m = re.search(r"\(\s*(\d{1,2}:\d{2})\s*-", row_text)
                if time_m:
                    result["time"] = time_m.group(1)
                break

    # ── Linescore ────────────────────────────────────────────────────────────
    linescore, seen_ls = [], set()
    for tbl in soup.find_all("table"):
        for row in _direct_rows(tbl):
            if id(row) in seen_ls:
                continue
            seen_ls.add(id(row))
            text = row.get_text(" ", strip=True)
            ls_m = re.match(
                r"^([A-Za-z][A-Za-z\-]+)\s+((?:\d+\s+)+)-\s+(\d+)\s+(\d+)\s+(\d+)\s*$", text)
            if ls_m:
                linescore.append({"team": ls_m.group(1), "innings": ls_m.group(2).split(),
                                  "r": ls_m.group(3), "h": ls_m.group(4), "e": ls_m.group(5)})
    result["linescore"] = linescore

    # ── Box scores ───────────────────────────────────────────────────────────
    # Collect batting and pitching boxes in DOCUMENT ORDER. We do NOT trust a
    # team-label table to precede each box: on npb.jp the two teams' boxes sit
    # side-by-side in one layout row, and both label tables can appear before
    # any stat table — which previously caused every box to inherit the last
    # label ("Yakult, Yakult, ..."). Instead, NPB always lists the AWAY team's
    # boxes first and the HOME team's second, so we assign teams positionally
    # from the score block (result["away"] / result["home"]).
    batting_boxes, pitching_boxes = [], []
    seen_tbl = set()

    for tbl in soup.find_all("table"):
        if id(tbl) in seen_tbl:
            continue
        rows = _direct_rows(tbl)
        if not rows:
            continue

        # Skip standalone team-label tables (1 row, 1 short-name cell). We no
        # longer use them for assignment, but skipping avoids mis-parsing them.
        if len(rows) == 1:
            cells = [c for c in _direct_cells(rows[0]) if c]
            if len(cells) == 1 and cells[0] in NPB_SHORT_NAMES:
                continue

        header_set = {h for h in _direct_cells(rows[0]) if h}

        if BAT_HEADER_KEYS <= header_set:
            seen_tbl.add(id(tbl))
            players = []
            for row in rows[1:]:
                cells = _direct_cells(row)
                if len(cells) < 7:
                    continue
                name_cell = cells[0]
                if not name_cell or not re.search(r"[A-Za-z]", name_cell):
                    continue
                if name_cell.upper() in STAT_HEADER_WORDS or name_cell.lower().startswith("total"):
                    continue
                stats = cells[1:7]
                if not all(re.match(r"^\d+$", s) for s in stats):
                    continue
                name, pos = _split_player(name_cell)
                players.append({"name": name, "pos": pos, "stats": stats})
            if players:
                batting_boxes.append({"team": "", "players": players})
            continue

        if PIT_HEADER_KEYS <= header_set:
            seen_tbl.add(id(tbl))
            players = []
            for row in rows[1:]:
                cells = _direct_cells(row)
                if len(cells) < 9:
                    continue
                name_cell = cells[0]
                if not name_cell or not re.search(r"[A-Za-z]", name_cell):
                    continue
                if name_cell.upper() in STAT_HEADER_WORDS or name_cell.lower().startswith("total"):
                    continue
                ip = (cells[1] + (" " + cells[2] if cells[2] else "")).strip()
                tail = cells[3:9]  # BF H BB HB SO ER
                if not all(re.match(r"^\d+$", s) for s in tail):
                    continue
                name, pos = _split_player(name_cell)
                players.append({"name": name, "pos": pos,
                                "stats": {"ip": ip or "–", "bf": tail[0], "h": tail[1],
                                          "bb": tail[2], "hb": tail[3], "so": tail[4], "er": tail[5]}})
            if players:
                pitching_boxes.append({"team": "", "players": players})
            continue

    batting_boxes  = batting_boxes[:2]
    pitching_boxes = pitching_boxes[:2]

    # Assign teams by position: away first, home second. Map the full team name
    # from the score block to its short box-score label (e.g. "Hokkaido
    # Nippon-Ham Fighters" -> "Nippon-Ham"); fall back to the full name.
    away_short = NPB_TEAM_TO_SHORT.get(result["away"], result["away"])
    home_short = NPB_TEAM_TO_SHORT.get(result["home"], result["home"])
    order = [away_short, home_short]
    for i, box in enumerate(batting_boxes):
        box["team"] = order[i] if i < 2 else ""
    for i, box in enumerate(pitching_boxes):
        box["team"] = order[i] if i < 2 else ""

    result["batting"]  = batting_boxes
    result["pitching"] = pitching_boxes

    # ── Game notes (WP / LP / S / HR) ────────────────────────────────────────
    notes, last_key = [], None
    for tr in soup.find_all("tr"):
        cells = _direct_cells(tr)
        if len(cells) < 2:
            continue
        key, val = cells[0].replace(":", "").strip(), cells[1].strip()
        if key in {"WP", "LP", "S", "HR"} and val:
            notes.append((key, val)); last_key = key
        elif not key and last_key == "HR" and re.match(r"^\[[A-Z]+\]", val):
            notes.append(("HR", val))
    result["notes"] = notes

    return result


@st.cache_data(ttl=300)
def get_npb_schedule_from_day(date_str: str) -> list[dict]:
    year    = date_str[:4]
    compact = date_str.replace("-", "")
    day_url = f"https://npb.jp/bis/eng/{year}/games/gm{compact}.html"
    try:
        r = get(day_url)
        if r.status_code != 200:
            return []
    except Exception:
        return []

    soup, games = BeautifulSoup(r.text, "lxml"), []
    large_logos = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "_l.gif" in src and "flag_" not in src and "samurai" not in src.lower() and "japan" not in src.lower():
            parent = img.parent
            text = parent.get_text(strip=True) if parent else ""
            if not text or len(text) > 40:
                text = img.get("alt", "").replace("#", "").strip()
            large_logos.append({"text": text, "src": src})

    for i in range(0, len(large_logos) - 1, 2):
        games.append({
            "away": large_logos[i]["text"] or f"Team {i+1}",
            "home": large_logos[i + 1]["text"] or f"Team {i+2}",
            "away_score": None, "home_score": None, "venue": "", "time": "",
            "status": "SCHEDULED", "linescore": [], "batting": [], "pitching": [],
            "notes": [], "game_url": day_url, "error": "",
        })
    return games


# ══════════════════════════════════════════════════════════════════════════════
# KBO SCRAPER — eng.koreabaseball.com (official English site)
#
# The English scoreboard exposes linescores + W/S/L pitcher decisions, but NO
# per-player batting lines. mykbostats.com DOES have full box scores, but:
#   (1) it returns HTTP 403 to datacenter IPs (so it would fail on Streamlit
#       Cloud — matches the project's "data source graveyard"), and
#   (2) the box score is rendered client-side (Phoenix LiveView), so it isn't
#       in the server HTML that requests+BeautifulSoup can see anyway.
# So for KBO we link the decision pitchers (full romanized names) to BR.
# ══════════════════════════════════════════════════════════════════════════════

KBO_TEAM_NAMES = {
    "KT": "KT Wiz", "DOOSAN": "Doosan Bears", "LG": "LG Twins",
    "LOTTE": "Lotte Giants", "SAMSUNG": "Samsung Lions", "SSG": "SSG Landers",
    "HANWHA": "Hanwha Eagles", "NC": "NC Dinos", "KIA": "Kia Tigers",
    "KIWOOM": "Kiwoom Heroes",
}
KBO_VENUES = {
    "JAMSIL": "Jamsil", "GOCHEOKSKY": "Gocheok Sky Dome", "GOCHEOK": "Gocheok Sky Dome",
    "MUNHAK": "Incheon (Munhak)", "SUWON": "Suwon", "DAEJEON": "Daejeon",
    "HANBAT": "Daejeon (Hanbat)", "DAEGU": "Daegu", "SAJIK": "Busan (Sajik)",
    "CHANGWON": "Changwon", "GWANGJU": "Gwangju", "ULSAN": "Ulsan",
    "POHANG": "Pohang", "CHEONGJU": "Cheongju",
}

def expand_kbo(code: str) -> str:
    return KBO_TEAM_NAMES.get(code.upper().strip(), code.strip().title())

def tidy_kbo_name(name: str) -> str:
    return " ".join(w.capitalize() for w in name.split())

def parse_kbo_decisions(segment: str) -> tuple[str, list[tuple[str, str]]]:
    venue = ""
    vm = re.match(r"\s*([A-Z][A-Z]{2,11})\s+\d{1,2}:\d{2}", segment)
    if vm and vm.group(1) not in KBO_TEAM_NAMES:
        venue = KBO_VENUES.get(vm.group(1), vm.group(1).title())

    decisions, parts = [], re.split(r"([WSL]):", segment)
    for i in range(1, len(parts) - 1, 2):
        label, raw = parts[i], parts[i + 1]
        nm = re.match(r"\s*([A-Za-z][A-Za-z\.\'\- ]*?)\s*$|\s*([A-Za-z][A-Za-z\.\'\- ]*?)(?=\s{2,}|\Z)", raw)
        name = (nm.group(1) or nm.group(2)) if nm else raw.strip()
        name = re.split(r"\d", name)[0].strip()
        if name:
            decisions.append((label, name))
    return venue, decisions


@st.cache_data(ttl=300)
def fetch_kbo(date_str: str) -> tuple[list, str, str]:
    url = f"https://eng.koreabaseball.com/Schedule/Scoreboard.aspx?searchDate={date_str}"
    try:
        r = requests.get(url, headers={**HEADERS, "Referer": "https://eng.koreabaseball.com/"}, timeout=14)
        if r.status_code != 200:
            return [], f"KBO site returned HTTP {r.status_code}.", url
    except Exception as e:
        return [], f"Network error: {e}", url

    soup, games = BeautifulSoup(r.text, "lxml"), []
    final_pat = re.compile(r'\b([A-Z]{2,7})\s+(\d{1,2})\s+FINAL\s+(\d{1,2})\s+([A-Z]{2,7})\b')
    sched_pat = re.compile(r'\b([A-Z]{2,7})\s+(\d{1,2}:\d{2})\s+([A-Z]{2,7})\b')

    page_text = soup.get_text(" ")
    game_headers, seen_spans = [], set()

    for m in final_pat.finditer(page_text):
        if m.start() in seen_spans:
            continue
        seen_spans.add(m.start())
        a, asc, hsc, h = m.group(1), m.group(2), m.group(3), m.group(4)
        if a in KBO_TEAM_NAMES and h in KBO_TEAM_NAMES:
            game_headers.append({"away": expand_kbo(a), "home": expand_kbo(h),
                                 "away_score": asc, "home_score": hsc, "status": "FINAL",
                                 "time": "", "pos": m.start(), "end": m.end()})

    for m in sched_pat.finditer(page_text):
        if m.start() in seen_spans:
            continue
        seen_spans.add(m.start())
        a, tv, h = m.group(1), m.group(2), m.group(3)
        if a in KBO_TEAM_NAMES and h in KBO_TEAM_NAMES:
            game_headers.append({"away": expand_kbo(a), "home": expand_kbo(h),
                                 "away_score": None, "home_score": None, "status": "SCHEDULED",
                                 "time": tv, "pos": m.start(), "end": m.end()})

    game_headers.sort(key=lambda x: x["pos"])

    for i, hdr in enumerate(game_headers):
        seg_end = game_headers[i + 1]["pos"] if i + 1 < len(game_headers) else len(page_text)
        segment = page_text[hdr["end"]:min(seg_end, hdr["end"] + 400)]
        hdr["venue"], hdr["decisions"] = parse_kbo_decisions(segment)

    score_tables = []
    for tbl in soup.find_all("table"):
        rows = tbl.find_all("tr", recursive=False)
        if not rows:
            tbody = tbl.find("tbody")
            rows = tbody.find_all("tr", recursive=False) if tbody else []
        if len(rows) < 2:
            continue
        codes = []
        for row in rows[:2]:
            first = row.find(["th", "td"], recursive=False)
            if first:
                codes.append(first.get_text(strip=True).upper())
        if len(codes) == 2 and all(c in KBO_TEAM_NAMES for c in codes):
            score_tables.append((codes, tbl))

    for i, hdr in enumerate(game_headers):
        ls = []
        if i < len(score_tables):
            _, tbl = score_tables[i]
            rows = tbl.find_all("tr", recursive=False)
            if not rows:
                tbody = tbl.find("tbody")
                rows = tbody.find_all("tr", recursive=False) if tbody else []
            for row in rows[:2]:
                cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"], recursive=False)]
                if not cells:
                    continue
                team_code, inn_cells = cells[0], cells[1:]
                innings, totals, r_val = [], [], None
                if len(inn_cells) >= 4:
                    totals = inn_cells[-4:]
                    innings = [c for c in inn_cells[:-4] if c]
                    r_val = totals[0] if totals[0] and re.match(r'^\d+$', totals[0]) else None
                ls.append({"team": expand_kbo(team_code), "innings": innings, "r": r_val or "–",
                           "h": totals[1] if len(totals) > 1 and totals[1] else "–",
                           "e": totals[2] if len(totals) > 2 and totals[2] else "–"})

        games.append({"away": hdr["away"], "home": hdr["home"],
                      "away_score": hdr["away_score"], "home_score": hdr["home_score"],
                      "venue": hdr.get("venue", ""), "time": hdr["time"], "status": hdr["status"],
                      "linescore": ls, "decisions": hdr.get("decisions", []),
                      "batting": [], "pitching": [], "notes": []})

    if not games:
        return [], (f"No KBO games found for {fmt_date(date_str)}. "
                    f"May be an off day (KBO plays Tue–Sun, no Mondays)."), url
    return games, "", url


# ══════════════════════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════════════════════

def render_linescore(ls: list):
    if not ls:
        return
    max_inn = max(len(r["innings"]) for r in ls)
    inn_headers = "".join(f"<th>{i+1}</th>" for i in range(max_inn))
    hdr = f"<tr><th></th>{inn_headers}<th class='tot'>R</th><th class='tot'>H</th><th class='tot'>E</th></tr>"
    rows = ""
    for r in ls:
        cells = "".join(f"<td>{r['innings'][i] if i < len(r['innings']) else '–'}</td>" for i in range(max_inn))
        rows += (f"<tr><td class='team-col'>{r['team']}</td>{cells}"
                 f"<td class='tot'>{r['r']}</td><td class='tot'>{r['h']}</td><td class='tot'>{r['e']}</td></tr>")
    st.markdown(f"<div class='linescore-wrap'><table class='linescore'>"
                f"<thead>{hdr}</thead><tbody>{rows}</tbody></table></div>", unsafe_allow_html=True)


def _npb_player_anchor(register, team_short, box_name):
    """BR anchor for an NPB box-score name, expanded via register when possible."""
    search_name, confident = npb_full_name(register, team_short, box_name)
    if confident:
        # display full name; link to full-name BR search
        return br_link(search_name, search_name)
    # fall back: show what the box printed, search the surname
    return br_link(search_name, box_name)


def render_batting_box(box, fallback_title, register):
    title = box.get("team") or fallback_title
    team_short = box.get("team") or ""
    head = ("<tr><th class='pname'>BATTING</th><th class='pname'></th>"
            "<th>AB</th><th>H</th><th>RBI</th><th>BB</th><th>HP</th><th>SO</th></tr>")
    rows = ""
    for p in box["players"]:
        link = _npb_player_anchor(register, team_short, p["name"])
        cells = "".join(f"<td>{s}</td>" for s in p["stats"])
        rows += f"<tr><td class='pname'>{link}</td><td class='ppos'>{p['pos']}</td>{cells}</tr>"
    st.markdown(f"<div class='box-title'>{title} — Batting</div>"
                f"<div class='boxscore-wrap'><table class='boxscore'>"
                f"<thead>{head}</thead><tbody>{rows}</tbody></table></div>", unsafe_allow_html=True)


def render_pitching_box(box, fallback_title, register):
    title = box.get("team") or fallback_title
    team_short = box.get("team") or ""
    head = ("<tr><th class='pname'>PITCHING</th><th class='pname'></th>"
            "<th>IP</th><th>BF</th><th>H</th><th>BB</th><th>HB</th><th>SO</th><th>ER</th></tr>")
    rows = ""
    for p in box["players"]:
        link = _npb_player_anchor(register, team_short, p["name"])
        s = p["stats"]
        rows += (f"<tr><td class='pname'>{link}</td><td class='ppos'>{p['pos']}</td>"
                 f"<td>{s['ip']}</td><td>{s['bf']}</td><td>{s['h']}</td><td>{s['bb']}</td>"
                 f"<td>{s['hb']}</td><td>{s['so']}</td><td>{s['er']}</td></tr>")
    st.markdown(f"<div class='box-title'>{title} — Pitching</div>"
                f"<div class='boxscore-wrap'><table class='boxscore'>"
                f"<thead>{head}</thead><tbody>{rows}</tbody></table></div>", unsafe_allow_html=True)


def render_game_notes(notes, register, away_short, home_short):
    if not notes:
        return
    label_map = {"WP": "WIN", "LP": "LOSS", "S": "SAVE", "HR": "HR"}
    html = ""
    for key, val in notes:
        # HR lines are prefixed like "[F] Reyes ( ... )"; the [X] tag isn't a
        # reliable team key, so for notes we expand by trying BOTH teams.
        m = re.match(r"^(?:\[[A-Z]+\]\s*)?([A-Za-z\.\'\-]+(?:\s[A-Za-z\.\'\-]+)?)", val)
        if m:
            box_name = m.group(1)
            search_name, confident = npb_full_name(register, away_short, box_name)
            if not confident:
                search_name, confident = npb_full_name(register, home_short, box_name)
            display = search_name if confident else box_name
            linked = val.replace(box_name, br_link(search_name, display), 1)
        else:
            linked = val
        html += f"<div class='notes-line'><span class='notes-key'>{label_map.get(key, key)}</span> &nbsp;{linked}</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_kbo_decisions(decisions):
    if not decisions:
        return
    label_map = {"W": "WIN", "S": "SAVE", "L": "LOSS"}
    html = ""
    for key, raw in decisions:
        display = tidy_kbo_name(raw)
        html += (f"<div class='notes-line'><span class='notes-key'>{label_map.get(key, key)}</span> &nbsp;"
                 f"{br_link(display, display)}</div>")
    st.markdown(html, unsafe_allow_html=True)


def render_card(g, league, date_str, register=None):
    away, home = g.get("away", "?"), g.get("home", "?")
    as_, hs = g.get("away_score"), g.get("home_score")
    venue, time_, status = g.get("venue", ""), g.get("time", ""), g.get("status", "")
    ls, gurl = g.get("linescore", []), g.get("game_url", "")
    final = as_ is not None and hs is not None
    batting, pitching = g.get("batting", []), g.get("pitching", [])
    notes, decisions = g.get("notes", []), g.get("decisions", [])

    ac, hc = winner_cls(as_, hs) if final else ("neutral", "neutral")
    as_d, hs_d = (str(as_) if final else "–"), (str(hs) if final else "–")

    if status == "FINAL":
        label = "FINAL"
    elif status in ("IN PROGRESS", "LIVE", "INPROGRESS"):
        label = "🔴 LIVE"
    elif time_:
        label = f"{time_} {'JST' if league == 'NPB' else 'KST'}"
    else:
        label = status or "SCHEDULED"

    year, compact = date_str[:4], date_str.replace("-", "")
    if league == "NPB":
        primary = gurl or f"https://npb.jp/bis/eng/{year}/games/gm{compact}.html"
        links = (f'<a class="ext-link" href="{primary}" target="_blank">NPB.jp</a>'
                 f'<a class="ext-link" href="https://npb.jp/bis/eng/{year}/games/gm{compact}.html" target="_blank">All Games</a>')
    else:
        kbo_url = f"https://eng.koreabaseball.com/Schedule/Scoreboard.aspx?searchDate={date_str}"
        links = (f'<a class="ext-link" href="{kbo_url}" target="_blank">KBO Official</a>'
                 f'<a class="ext-link" href="https://mykbostats.com/games" target="_blank">MyKBOStats</a>')

    venue_html = f"<div class='card-venue'>{venue}</div>" if venue else ""
    st.markdown(f"""
    <div class="card">
      {venue_html}
      <div class="card-teams">
        <div class="team-block">
          <div class="team-name {ac}">{away}</div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:.58rem;color:#2a2a2a;margin-top:2px">AWAY</div>
        </div>
        <div class="score-mid">
          <span class="score {ac}">{as_d}</span><span class="score-sep">·</span><span class="score {hc}">{hs_d}</span>
        </div>
        <div class="team-block" style="text-align:right">
          <div class="team-name {hc}" style="text-align:right">{home}</div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:.58rem;color:#2a2a2a;margin-top:2px;text-align:right">HOME</div>
        </div>
      </div>
      <div class="card-footer">
        <div class="card-meta">{label}</div>
        <div class="card-links">{links}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    has_detail = ls or batting or pitching or notes or decisions
    if final and has_detail:
        with st.expander(f"Box score — {away} @ {home}"):
            if ls:
                render_linescore(ls)
            if notes:
                # Box labels are short names; derive away/home short labels.
                away_short = batting[0]["team"] if len(batting) >= 1 and batting[0].get("team") else ""
                home_short = batting[1]["team"] if len(batting) >= 2 and batting[1].get("team") else ""
                render_game_notes(notes, register or {}, away_short, home_short)
            if decisions:
                render_kbo_decisions(decisions)
                st.markdown("<div class='notes-line' style='color:#333'>"
                            "Per-player batting lines aren't published on KBO's English site — "
                            "pitcher decisions above link to Baseball Reference.</div>", unsafe_allow_html=True)
            fallbacks = [away, home]
            if batting:
                cols = st.columns(2) if len(batting) == 2 else (st.container(),)
                for idx, box in enumerate(batting):
                    with cols[idx] if len(batting) == 2 else cols[0]:
                        render_batting_box(box, fallbacks[idx] if idx < 2 else "", register or {})
            if pitching:
                cols = st.columns(2) if len(pitching) == 2 else (st.container(),)
                for idx, box in enumerate(pitching):
                    with cols[idx] if len(pitching) == 2 else cols[0]:
                        render_pitching_box(box, fallbacks[idx] if idx < 2 else "", register or {})


def scores_page_npb(date_str: str):
    with st.spinner("Fetching NPB game links…"):
        game_links, err = get_npb_game_links(date_str)

    if err:
        st.markdown(f"<div class='err-box'>⚠ {err}</div>", unsafe_allow_html=True)
        return

    if not game_links:
        st.markdown("<div class='info-box'>Games not yet completed — showing schedule from NPB.jp</div>",
                    unsafe_allow_html=True)
        sched = get_npb_schedule_from_day(date_str)
        if sched:
            for g in sched:
                render_card(g, "NPB", date_str)
        else:
            st.markdown(f"<div class='no-games'>No NPB games found for {fmt_date(date_str)}</div>",
                        unsafe_allow_html=True)
        return

    # Player-name register (cached 24h) — used to expand surnames to full names.
    register = load_npb_register()

    progress = st.progress(0, text="Loading game results…")
    games = []
    for i, gurl in enumerate(game_links):
        games.append(parse_npb_game(gurl))
        progress.progress((i + 1) / len(game_links), text=f"Loading game {i+1} of {len(game_links)}…")
    progress.empty()

    for g in games:
        if g.get("error"):
            st.markdown(f"<div class='err-box'>⚠ Could not load game: {g['error']}</div>", unsafe_allow_html=True)
        else:
            render_card(g, "NPB", date_str, register=register)


def scores_page_kbo(date_str: str):
    with st.spinner("Fetching KBO scores…"):
        games, err, src_url = fetch_kbo(date_str)

    if err:
        st.markdown(f"<div class='err-box'>⚠ {err}</div>", unsafe_allow_html=True)
        st.markdown(f"[View on KBO Official ↗]({src_url})")

    if not games and not err:
        st.markdown(f"<div class='no-games'>No KBO games found for {fmt_date(date_str)}</div>",
                    unsafe_allow_html=True)
        return

    for g in games:
        render_card(g, "KBO", date_str)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="masthead">
  <div class="masthead-title">NPB · KBO</div>
  <div class="masthead-sub">Scores &amp; Schedule</div>
</div>""", unsafe_allow_html=True)

jst_now = now_jst()

c1, c2, c3 = st.columns([3, 1, 1])
with c1:
    selected_date = st.date_input("Date", value=(jst_now - timedelta(days=1)).date(),
                                  max_value=jst_now.date(), min_value=date_type(2020, 1, 1),
                                  label_visibility="collapsed", format="YYYY-MM-DD")
    selected_str = selected_date.strftime("%Y-%m-%d")
with c2:
    st.markdown(f"<div style='font-family:IBM Plex Mono,monospace;font-size:.62rem;color:#333;padding-top:10px'>"
                f"JST {jst_now.strftime('%H:%M')}</div>", unsafe_allow_html=True)
with c3:
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

today_s     = jst_now.strftime("%Y-%m-%d")
yesterday_s = (jst_now - timedelta(days=1)).strftime("%Y-%m-%d")
dlabel = (f"Today · {fmt_date(selected_str)}"     if selected_str == today_s     else
          f"Yesterday · {fmt_date(selected_str)}" if selected_str == yesterday_s else
          fmt_date(selected_str))
st.markdown(f"<div class='section-label' style='margin-bottom:.8rem'>{dlabel}</div>", unsafe_allow_html=True)

st.markdown("""
<div class='info-box'>
  NPB from <strong>NPB.jp</strong> (official game pages + box scores) ·
  KBO from <strong>eng.koreabaseball.com</strong> ·
  Player names link to <strong>Baseball Reference</strong> (NPB full names via NPB.jp register) · Cache: 5 min
</div>""", unsafe_allow_html=True)

t_npb, t_kbo = st.tabs(["🇯🇵  NPB Scores", "🇰🇷  KBO Scores"])
with t_npb:
    scores_page_npb(selected_str)
with t_kbo:
    scores_page_kbo(selected_str)

st.markdown("---")
st.markdown(f"<span style='font-family:IBM Plex Mono,monospace;font-size:.58rem;color:#222;letter-spacing:.1em'>"
            f"NPB.jp · eng.koreabaseball.com · {datetime.now(JST).year} season</span>", unsafe_allow_html=True)
