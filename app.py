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
    # NOTE: avoid "%-d" — it's Linux-only and crashes on Windows
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
# PLAYER LINKS
#
# Baseball Reference is used (rather than FanGraphs) because BR's Register
# covers virtually every NPB and KBO player, while FanGraphs has no NPB
# player pages at all and only partial KBO coverage. We link to BR's search
# endpoint so no player-ID mapping is needed — BR resolves the name itself
# (and lands directly on the player page when the name is unambiguous).
# These links open in the USER'S browser, so Cloudflare datacenter-IP
# blocking is not a concern here.
# ══════════════════════════════════════════════════════════════════════════════

def br_player_link(name: str, display: str | None = None) -> str:
    """Return an <a> tag linking a player name to Baseball Reference search."""
    clean = re.sub(r"\s+", " ", name).strip()
    if not clean:
        return display or name
    url = "https://www.baseball-reference.com/search/search.fcgi?search=" + quote(clean)
    return f'<a class="player-link" href="{url}" target="_blank">{display or clean}</a>'


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — scrape the day-index page to get individual game links
# URL: https://npb.jp/bis/eng/YYYY/games/gmYYYYMMDD.html
# These pages contain <a href="sYYYYMMDDnnnnn.html"> links for each game
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def get_npb_game_links(date_str: str) -> tuple[list[str], str]:
    """
    Returns (list_of_game_urls, error_msg).
    Game URLs look like: https://npb.jp/bis/eng/2026/games/s2026052901848.html
    """
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
        href = a["href"]
        filename = href.split("/")[-1]
        if pattern.match(filename):
            full_url = base + filename if not href.startswith("http") else href
            if full_url not in game_links:
                game_links.append(full_url)

    if not game_links:
        return [], ""

    return game_links, ""


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — scrape each individual game page
# URL: https://npb.jp/bis/eng/YYYY/games/sYYYYMMDDnnnnn.html
#
# Confirmed structure (live fetch of s2026060701896.html, Jun 7 2026):
#
#   Score block:  away team listed FIRST, then home team
#   Venue line:   "Jingu | T - 2:33 ( 14:01 - 16:34 ) Att. - 29,328"
#   Linescore:    "Nippon-Ham 2 0 0 0 4 1 0 0 0 - 7 9 1"
#
#   NEW — full box scores are on the SAME page (no extra requests):
#
#   Each team's box is preceded by a tiny one-cell table holding the team's
#   SHORT name (e.g. "Nippon-Ham", "Yakult").
#
#   Batting table header row:  ["", "AB", "H", "RBI", "BB", "HP", "SO"]
#   Batting player row:        ["Mizuno, SS", "5", "1", "0", "0", "0", "1"]
#                              (name and position joined by comma; position
#                               can be compound like "3B-1B" or "PH-CF")
#
#   Pitching table header row: ["", "IP", "", "BF", "H", "BB", "HB", "SO", "ER"]
#                              (note the EXTRA blank column after IP — it holds
#                               the fractional innings, e.g. "2/3")
#   Pitching player row:       ["Kitayama, (W)", "9", "", "31", "4", "1", "0", "6", "1"]
#
#   Game notes rows:           first cell "WP :", "LP :", "S :", or "HR :",
#                              second cell the detail; HR continuation rows
#                              have an empty first cell.
# ══════════════════════════════════════════════════════════════════════════════

NPB_SHORT_NAMES = {
    "Yomiuri", "Hanshin", "DeNA", "Chunichi", "Hiroshima", "Yakult",
    "SoftBank", "Nippon-Ham", "ORIX", "Rakuten", "Seibu", "Lotte",
}

BAT_HEADER_KEYS = {"AB", "RBI"}      # must both appear in header row
PIT_HEADER_KEYS = {"IP", "BF"}       # must both appear in header row

STAT_HEADER_WORDS = {"AB", "IP", "H", "R", "E", "BB", "SO", "HP",
                     "HB", "ER", "BF", "WP", "LP", "HR", "ERA", "RBI", "S"}


def _direct_rows(tbl):
    """All <tr> that are direct children of a table (or its thead/tbody)."""
    rows = tbl.find_all("tr", recursive=False)
    for section in tbl.find_all(["tbody", "thead"], recursive=False):
        rows += section.find_all("tr", recursive=False)
    return rows


def _direct_cells(tr):
    """Texts of direct-child th/td only — never descends into nested tables."""
    return [c.get_text(strip=True) for c in tr.find_all(["th", "td"], recursive=False)]


def _split_player(name_cell: str) -> tuple[str, str]:
    """'Mizuno, SS' -> ('Mizuno', 'SS');  'Kitayama, (W)' -> ('Kitayama', '(W)')"""
    if "," in name_cell:
        name, _, pos = name_cell.partition(",")
        return name.strip(), pos.strip()
    return name_cell.strip(), ""


@st.cache_data(ttl=300)
def parse_npb_game(game_url: str) -> dict:
    """
    Returns a game dict with keys:
      away, home, away_score, home_score, venue, time, status,
      linescore (list of dicts: {team, innings[], r, h, e}),
      batting   (list of {team, players:[{name,pos,stats[6]}]}),  away first
      pitching  (list of {team, players:[{name,pos,stats: {ip,bf,h,bb,hb,so,er}}]}),
      notes     (list of (key, text) like ("WP","Kitayama ( 5 - 2 )")),
      game_url
    """
    result = {
        "away": "", "home": "",
        "away_score": None, "home_score": None,
        "venue": "", "time": "",
        "status": "UNKNOWN",
        "linescore": [],
        "batting": [],
        "pitching": [],
        "notes": [],
        "game_url": game_url,
        "error": "",
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

    # ── Team names + final scores ────────────────────────────────────────────
    # (see original comments — recursive=False everywhere to dodge nested-table
    #  duplication, <th> cells included because score cells are <th> not <td>)

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
        result["away"]       = score_rows[0][0]
        result["home"]       = score_rows[1][0]
        result["away_score"] = score_rows[0][1]
        result["home_score"] = score_rows[1][1]
        result["status"]     = "FINAL"
    elif title_m:
        result["away"]   = title_m.group(1).strip()
        result["home"]   = title_m.group(2).strip()
        result["status"] = "SCHEDULED"

    # ── Venue + time ─────────────────────────────────────────────────────────
    for tbl in soup.find_all("table"):
        cells = [td.get_text(strip=True) for td in tbl.find_all("td") if td.get_text(strip=True)]
        if not cells:
            continue
        row_text = " ".join(cells)
        if re.search(r"\d{1,2}:\d{2}", row_text) and len(cells) >= 2:
            venue_candidate = cells[0]
            if not re.match(r"^(AB|IP|R|H|E|BB|SO|WP|LP|HR)$", venue_candidate):
                if len(venue_candidate) > 2:
                    result["venue"] = venue_candidate
                    time_m = re.search(r"\(\s*(\d{1,2}:\d{2})\s*-", row_text)
                    if time_m:
                        result["time"] = time_m.group(1)
                    break

    # ── Linescore ────────────────────────────────────────────────────────────
    linescore   = []
    seen_ls_ids = set()
    for tbl in soup.find_all("table"):
        for row in _direct_rows(tbl):
            row_id = id(row)
            if row_id in seen_ls_ids:
                continue
            seen_ls_ids.add(row_id)
            text = row.get_text(" ", strip=True)
            ls_m = re.match(
                r"^([A-Za-z][A-Za-z\-]+)\s+((?:\d+\s+)+)-\s+(\d+)\s+(\d+)\s+(\d+)\s*$",
                text
            )
            if ls_m:
                linescore.append({
                    "team":    ls_m.group(1),
                    "innings": ls_m.group(2).split(),
                    "r": ls_m.group(3),
                    "h": ls_m.group(4),
                    "e": ls_m.group(5),
                })
    if linescore:
        result["linescore"] = linescore

    # ── Box scores (batting + pitching) ──────────────────────────────────────
    # Walk tables in document order. A one-cell table whose text is a known
    # NPB short name sets the "current team" label; the batting/pitching
    # tables that follow belong to that team until the next label appears.
    batting_boxes  = []
    pitching_boxes = []
    current_label  = None
    seen_tbl_ids   = set()

    for tbl in soup.find_all("table"):
        if id(tbl) in seen_tbl_ids:
            continue
        rows = _direct_rows(tbl)
        if not rows:
            continue

        # Team-label table: one row, exactly one non-empty cell, known name
        if len(rows) == 1:
            cells = [c for c in _direct_cells(rows[0]) if c]
            if len(cells) == 1 and cells[0] in NPB_SHORT_NAMES:
                current_label = cells[0]
                continue

        header = _direct_cells(rows[0])
        header_set = {h for h in header if h}

        # ---- Batting table ----
        if BAT_HEADER_KEYS <= header_set:
            seen_tbl_ids.add(id(tbl))
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
                batting_boxes.append({"team": current_label or "", "players": players})
            continue

        # ---- Pitching table ----
        if PIT_HEADER_KEYS <= header_set:
            seen_tbl_ids.add(id(tbl))
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
                ip_whole, ip_frac = cells[1], cells[2]
                ip = (ip_whole + (" " + ip_frac if ip_frac else "")).strip()
                tail = cells[3:9]   # BF H BB HB SO ER
                if not all(re.match(r"^\d+$", s) for s in tail):
                    continue
                name, pos = _split_player(name_cell)
                players.append({
                    "name": name, "pos": pos,
                    "stats": {"ip": ip or "–", "bf": tail[0], "h": tail[1],
                              "bb": tail[2], "hb": tail[3], "so": tail[4],
                              "er": tail[5]},
                })
            if players:
                pitching_boxes.append({"team": current_label or "", "players": players})
            continue

    result["batting"]  = batting_boxes[:2]
    result["pitching"] = pitching_boxes[:2]

    # ── Game notes (WP / LP / S / HR) ────────────────────────────────────────
    notes = []
    last_key = None
    for tr in soup.find_all("tr"):
        cells = _direct_cells(tr)
        if len(cells) < 2:
            continue
        key = cells[0].replace(":", "").strip()
        val = cells[1].strip()
        if key in {"WP", "LP", "S", "HR"} and val:
            notes.append((key, val))
            last_key = key
        elif not key and last_key == "HR" and re.match(r"^\[[A-Z]+\]", val):
            # HR continuation rows: empty first cell, "[F] Martinez ( ... )"
            notes.append(("HR", val))
    result["notes"] = notes

    return result


# ══════════════════════════════════════════════════════════════════════════════
# Also handle SCHEDULED day pages (no game links yet) —
# fall back to parsing the day-index page for team names + times
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def get_npb_schedule_from_day(date_str: str) -> list[dict]:
    """
    Parse the day-index page for scheduled (unplayed) games.
    Returns list of partial game dicts with away/home/time/venue but no scores.
    """
    year    = date_str[:4]
    compact = date_str.replace("-", "")
    day_url = f"https://npb.jp/bis/eng/{year}/games/gm{compact}.html"

    try:
        r = get(day_url)
        if r.status_code != 200:
            return []
    except Exception:
        return []

    soup  = BeautifulSoup(r.text, "lxml")
    games = []

    large_logos = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "_l.gif" in src and "flag_" not in src and "samurai" not in src.lower() and "japan" not in src.lower():
            parent = img.parent
            text   = parent.get_text(strip=True) if parent else ""
            if not text or len(text) > 40:
                text = img.get("alt", "").replace("#", "").strip()
            large_logos.append({"text": text, "src": src})

    for i in range(0, len(large_logos) - 1, 2):
        away_text = large_logos[i]["text"]
        home_text = large_logos[i + 1]["text"]
        games.append({
            "away": away_text or f"Team {i+1}",
            "home": home_text or f"Team {i+2}",
            "away_score": None,
            "home_score": None,
            "venue": "",
            "time": "",
            "status": "SCHEDULED",
            "linescore": [],
            "batting": [], "pitching": [], "notes": [],
            "game_url": day_url,
            "error": "",
        })

    return games


# ══════════════════════════════════════════════════════════════════════════════
# KBO SCRAPER  —  eng.koreabaseball.com (official KBO English site)
#
# URL: https://eng.koreabaseball.com/Schedule/Scoreboard.aspx
# Date param: ?searchDate=YYYY-MM-DD  (confirmed working for past dates)
#
# Confirmed structure for a COMPLETED game:
#   Header text (between logo imgs): "LG 4 FINAL 1 HANWHA"
#   Venue line: "JAMSIL 18:30 W: KIM Do Gyu L: KIM Jin Sung"
#               (S: appears between W: and L: when there's a save;
#                in flattened text the labels can run into the previous
#                name with no space, e.g. "KIM Seo HyeonL: BARNES Charlie")
#   Table row:  TEAMCODE | 1 | 0 | 1 | ... | - | R | H | E | B
#
# NOTE: the English scoreboard exposes NO per-player batting/pitching lines.
# The only player-level data is the W / S / L pitcher decisions, which we
# parse and link. Full KBO box scores exist only on the Korean-language
# site (www.koreabaseball.com) behind constructed game IDs — fragile, and
# names are in Hangul, so it is intentionally not scraped here.
# ══════════════════════════════════════════════════════════════════════════════

KBO_TEAM_NAMES = {
    "KT":      "KT Wiz",
    "DOOSAN":  "Doosan Bears",
    "LG":      "LG Twins",
    "LOTTE":   "Lotte Giants",
    "SAMSUNG": "Samsung Lions",
    "SSG":     "SSG Landers",
    "HANWHA":  "Hanwha Eagles",
    "NC":      "NC Dinos",
    "KIA":     "Kia Tigers",
    "KIWOOM":  "Kiwoom Heroes",
}

# Venue codes that appear in the decisions line — used to pull the ballpark
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
    """'KIM Seo Hyeon' -> 'Kim Seo Hyeon' (KBO eng site shouts surnames)."""
    return " ".join(w.capitalize() for w in name.split())

def parse_kbo_decisions(segment: str) -> tuple[str, list[tuple[str, str]]]:
    """
    Parse the venue/decisions text that follows a game header, e.g.
      'HANBAT 14:00 W: KIM Seo HyeonL: BARNES Charlie'
    Returns (venue, [('W','KIM Seo Hyeon'), ('L','BARNES Charlie'), ...]).
    """
    venue = ""
    vm = re.match(r"\s*([A-Z][A-Z]{2,11})\s+\d{1,2}:\d{2}", segment)
    if vm and vm.group(1) not in KBO_TEAM_NAMES:
        venue = KBO_VENUES.get(vm.group(1), vm.group(1).title())

    decisions = []
    # Split on W: / S: / L: labels. The colon cannot follow a digit here, and
    # team/venue codes never contain ':', so this is safe even when a label
    # runs into the previous name ('...HyeonL:').
    parts = re.split(r"([WSL]):", segment)
    # parts = [pre, 'W', ' KIM Seo Hyeon', 'L', ' BARNES Charlie', ...]
    for i in range(1, len(parts) - 1, 2):
        label = parts[i]
        raw   = parts[i + 1]
        # name = leading run of letters/dots/apostrophes/hyphens/spaces,
        # with a possible single trailing capital that belongs to the NEXT
        # label already stripped by the split
        nm = re.match(r"\s*([A-Za-z][A-Za-z\.\'\- ]*?)\s*$|\s*([A-Za-z][A-Za-z\.\'\- ]*?)(?=\s{2,}|\Z)", raw)
        name = (nm.group(1) or nm.group(2)) if nm else raw.strip()
        # Cut anything that is clearly not part of a name (digits onward)
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

    soup  = BeautifulSoup(r.text, "lxml")
    games = []

    final_pat = re.compile(
        r'\b([A-Z]{2,7})\s+(\d{1,2})\s+FINAL\s+(\d{1,2})\s+([A-Z]{2,7})\b'
    )
    sched_pat = re.compile(
        r'\b([A-Z]{2,7})\s+(\d{1,2}:\d{2})\s+([A-Z]{2,7})\b'
    )

    page_text = soup.get_text(" ")

    game_headers = []
    seen_spans = set()

    for m in final_pat.finditer(page_text):
        if m.start() not in seen_spans:
            seen_spans.add(m.start())
            away_code, away_scr, home_scr, home_code = m.group(1), m.group(2), m.group(3), m.group(4)
            if away_code in KBO_TEAM_NAMES and home_code in KBO_TEAM_NAMES:
                game_headers.append({
                    "away": expand_kbo(away_code),
                    "home": expand_kbo(home_code),
                    "away_score": away_scr,
                    "home_score": home_scr,
                    "status": "FINAL",
                    "time": "",
                    "pos": m.start(),
                    "end": m.end(),
                })

    for m in sched_pat.finditer(page_text):
        if m.start() not in seen_spans:
            seen_spans.add(m.start())
            away_code, time_val, home_code = m.group(1), m.group(2), m.group(3)
            if away_code in KBO_TEAM_NAMES and home_code in KBO_TEAM_NAMES:
                game_headers.append({
                    "away": expand_kbo(away_code),
                    "home": expand_kbo(home_code),
                    "away_score": None,
                    "home_score": None,
                    "status": "SCHEDULED",
                    "time": time_val,
                    "pos": m.start(),
                    "end": m.end(),
                })

    game_headers.sort(key=lambda x: x["pos"])

    # ── Venue + W/S/L pitcher decisions: parse the text BETWEEN headers ──────
    for i, hdr in enumerate(game_headers):
        seg_end = game_headers[i + 1]["pos"] if i + 1 < len(game_headers) else len(page_text)
        segment = page_text[hdr["end"]:min(seg_end, hdr["end"] + 400)]
        venue, decisions = parse_kbo_decisions(segment)
        hdr["venue"] = venue
        hdr["decisions"] = decisions

    # ── Parse linescore tables ────────────────────────────────────────────────
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

    # ── Match headers to tables and build game dicts ──────────────────────────
    for i, hdr in enumerate(game_headers):
        ls = []

        if i < len(score_tables):
            codes, tbl = score_tables[i]
            rows = tbl.find_all("tr", recursive=False)
            if not rows:
                tbody = tbl.find("tbody")
                rows = tbody.find_all("tr", recursive=False) if tbody else []

            for row in rows[:2]:
                cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"], recursive=False)]
                if not cells:
                    continue
                team_code = cells[0]
                inn_cells = cells[1:]
                innings, totals, r_val = [], [], None
                if len(inn_cells) >= 4:
                    totals = inn_cells[-4:]   # R, H, E, B
                    inning_cells = inn_cells[:-4]
                    innings = [c for c in inning_cells if c]
                    r_val = totals[0] if totals[0] and re.match(r'^\d+$', totals[0]) else None
                ls.append({
                    "team":    expand_kbo(team_code),
                    "innings": innings,
                    "r": r_val or "–",
                    "h": totals[1] if len(totals) > 1 and totals[1] else "–",
                    "e": totals[2] if len(totals) > 2 and totals[2] else "–",
                })

        games.append({
            "away":       hdr["away"],
            "home":       hdr["home"],
            "away_score": hdr["away_score"],
            "home_score": hdr["home_score"],
            "venue":      hdr.get("venue", ""),
            "time":       hdr["time"],
            "status":     hdr["status"],
            "linescore":  ls,
            "decisions":  hdr.get("decisions", []),
            "batting": [], "pitching": [], "notes": [],
        })

    if not games:
        return [], (
            f"No KBO games found for {fmt_date(date_str)}. "
            f"May be an off day (KBO plays Tue–Sun, no Mondays)."
        ), url

    return games, "", url

# ══════════════════════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════════════════════

def render_linescore(ls: list):
    if not ls:
        return
    max_inn = max(len(row["innings"]) for row in ls)
    inn_headers = "".join(f"<th>{i+1}</th>" for i in range(max_inn))
    hdr = f"<tr><th></th>{inn_headers}<th class='tot'>R</th><th class='tot'>H</th><th class='tot'>E</th></tr>"
    rows_html = ""
    for row in ls:
        cells = "".join(f"<td>{row['innings'][i] if i < len(row['innings']) else '–'}</td>"
                        for i in range(max_inn))
        rows_html += (f"<tr><td class='team-col'>{row['team']}</td>{cells}"
                      f"<td class='tot'>{row['r']}</td>"
                      f"<td class='tot'>{row['h']}</td>"
                      f"<td class='tot'>{row['e']}</td></tr>")
    st.markdown(
        f"<div class='linescore-wrap'><table class='linescore'>"
        f"<thead>{hdr}</thead><tbody>{rows_html}</tbody></table></div>",
        unsafe_allow_html=True
    )


def render_batting_box(box: dict, fallback_title: str):
    title = box.get("team") or fallback_title
    head = ("<tr><th class='pname'>BATTING</th><th class='pname'></th>"
            "<th>AB</th><th>H</th><th>RBI</th><th>BB</th><th>HP</th><th>SO</th></tr>")
    rows = ""
    for p in box["players"]:
        link  = br_player_link(p["name"])
        cells = "".join(f"<td>{s}</td>" for s in p["stats"])
        rows += (f"<tr><td class='pname'>{link}</td>"
                 f"<td class='ppos'>{p['pos']}</td>{cells}</tr>")
    st.markdown(
        f"<div class='box-title'>{title} — Batting</div>"
        f"<div class='boxscore-wrap'><table class='boxscore'>"
        f"<thead>{head}</thead><tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True
    )


def render_pitching_box(box: dict, fallback_title: str):
    title = box.get("team") or fallback_title
    head = ("<tr><th class='pname'>PITCHING</th><th class='pname'></th>"
            "<th>IP</th><th>BF</th><th>H</th><th>BB</th><th>HB</th><th>SO</th><th>ER</th></tr>")
    rows = ""
    for p in box["players"]:
        link = br_player_link(p["name"])
        s    = p["stats"]
        rows += (f"<tr><td class='pname'>{link}</td>"
                 f"<td class='ppos'>{p['pos']}</td>"
                 f"<td>{s['ip']}</td><td>{s['bf']}</td><td>{s['h']}</td>"
                 f"<td>{s['bb']}</td><td>{s['hb']}</td><td>{s['so']}</td>"
                 f"<td>{s['er']}</td></tr>")
    st.markdown(
        f"<div class='box-title'>{title} — Pitching</div>"
        f"<div class='boxscore-wrap'><table class='boxscore'>"
        f"<thead>{head}</thead><tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True
    )


def render_game_notes(notes: list):
    """WP / LP / S / HR lines from NPB — player name inside is linked."""
    if not notes:
        return
    label_map = {"WP": "WIN", "LP": "LOSS", "S": "SAVE", "HR": "HR"}
    html = ""
    for key, val in notes:
        # Pull the player name: leading text up to '(' or the '[F] ' prefix
        m = re.match(r"^(?:\[[A-Z]+\]\s*)?([A-Za-z\.\'\-]+(?:\s[A-Za-z\.\'\-]+)?)", val)
        if m:
            name   = m.group(1)
            linked = val.replace(name, br_player_link(name), 1)
        else:
            linked = val
        html += (f"<div class='notes-line'><span class='notes-key'>"
                 f"{label_map.get(key, key)}</span> &nbsp;{linked}</div>")
    st.markdown(html, unsafe_allow_html=True)


def render_kbo_decisions(decisions: list):
    """W / S / L pitcher decisions from the KBO scoreboard, names linked."""
    if not decisions:
        return
    label_map = {"W": "WIN", "S": "SAVE", "L": "LOSS"}
    html = ""
    for key, raw_name in decisions:
        display = tidy_kbo_name(raw_name)
        html += (f"<div class='notes-line'><span class='notes-key'>"
                 f"{label_map.get(key, key)}</span> &nbsp;"
                 f"{br_player_link(raw_name, display)}</div>")
    st.markdown(html, unsafe_allow_html=True)


def render_card(g: dict, league: str, date_str: str):
    away   = g.get("away", "?")
    home   = g.get("home", "?")
    as_    = g.get("away_score")
    hs     = g.get("home_score")
    venue  = g.get("venue", "")
    time_  = g.get("time", "")
    status = g.get("status", "")
    ls     = g.get("linescore", [])
    gurl   = g.get("game_url", "")
    final  = as_ is not None and hs is not None

    batting   = g.get("batting", [])
    pitching  = g.get("pitching", [])
    notes     = g.get("notes", [])
    decisions = g.get("decisions", [])

    ac, hc = winner_cls(as_, hs) if final else ("neutral", "neutral")
    as_d   = str(as_) if final else "–"
    hs_d   = str(hs)  if final else "–"

    if status == "FINAL":
        label = "FINAL"
    elif status in ("IN PROGRESS", "LIVE", "INPROGRESS"):
        label = "🔴 LIVE"
    elif time_:
        label = f"{time_} {'JST' if league == 'NPB' else 'KST'}"
    else:
        label = status or "SCHEDULED"

    year    = date_str[:4]
    compact = date_str.replace("-", "")

    if league == "NPB":
        primary_url = gurl or f"https://npb.jp/bis/eng/{year}/games/gm{compact}.html"
        links = (
            f'<a class="ext-link" href="{primary_url}" target="_blank">NPB.jp</a>'
            f'<a class="ext-link" href="https://npb.jp/bis/eng/{year}/games/gm{compact}.html" target="_blank">All Games</a>'
        )
    else:
        kbo_url = f"https://eng.koreabaseball.com/Schedule/Scoreboard.aspx?searchDate={date_str}"
        links = (
            f'<a class="ext-link" href="{kbo_url}" target="_blank">KBO Official</a>'
            f'<a class="ext-link" href="https://mykbostats.com/games" target="_blank">MyKBOStats</a>'
        )

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
          <span class="score {ac}">{as_d}</span>
          <span class="score-sep">·</span>
          <span class="score {hc}">{hs_d}</span>
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
                render_game_notes(notes)
            if decisions:
                render_kbo_decisions(decisions)
                st.markdown(
                    "<div class='notes-line' style='color:#333'>"
                    "Per-player batting lines aren't published on KBO's English site — "
                    "player names above link to Baseball Reference.</div>",
                    unsafe_allow_html=True
                )
            # Away box first, then home (matches document order on NPB.jp)
            fallbacks = [away, home]
            if batting:
                c1, c2 = st.columns(2) if len(batting) == 2 else (st.container(), None)
                for idx, box in enumerate(batting):
                    target = (c1, c2)[idx] if len(batting) == 2 else c1
                    with target:
                        render_batting_box(box, fallbacks[idx] if idx < 2 else "")
            if pitching:
                c1, c2 = st.columns(2) if len(pitching) == 2 else (st.container(), None)
                for idx, box in enumerate(pitching):
                    target = (c1, c2)[idx] if len(pitching) == 2 else c1
                    with target:
                        render_pitching_box(box, fallbacks[idx] if idx < 2 else "")


def scores_page_npb(date_str: str):
    with st.spinner("Fetching NPB game links…"):
        game_links, err = get_npb_game_links(date_str)

    if err:
        st.markdown(f"<div class='err-box'>⚠ {err}</div>", unsafe_allow_html=True)
        return

    if not game_links:
        st.markdown(
            "<div class='info-box'>Games not yet completed — showing schedule from NPB.jp</div>",
            unsafe_allow_html=True
        )
        sched = get_npb_schedule_from_day(date_str)
        if sched:
            for g in sched:
                render_card(g, "NPB", date_str)
        else:
            st.markdown(
                f"<div class='no-games'>No NPB games found for {fmt_date(date_str)}</div>",
                unsafe_allow_html=True
            )
        return

    progress = st.progress(0, text="Loading game results…")
    games = []
    for i, gurl in enumerate(game_links):
        g = parse_npb_game(gurl)
        games.append(g)
        progress.progress((i + 1) / len(game_links), text=f"Loading game {i+1} of {len(game_links)}…")
    progress.empty()

    for g in games:
        if g.get("error"):
            st.markdown(f"<div class='err-box'>⚠ Could not load game: {g['error']}</div>", unsafe_allow_html=True)
        else:
            render_card(g, "NPB", date_str)


def scores_page_kbo(date_str: str):
    with st.spinner("Fetching KBO scores…"):
        games, err, src_url = fetch_kbo(date_str)

    if err:
        st.markdown(f"<div class='err-box'>⚠ {err}</div>", unsafe_allow_html=True)
        st.markdown(f"[View on KBO Official ↗]({src_url})")

    if not games and not err:
        st.markdown(
            f"<div class='no-games'>No KBO games found for {fmt_date(date_str)}</div>",
            unsafe_allow_html=True
        )
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
    selected_date = st.date_input(
        "Date",
        value=(jst_now - timedelta(days=1)).date(),
        max_value=jst_now.date(),
        min_value=date_type(2020, 1, 1),
        label_visibility="collapsed",
        format="YYYY-MM-DD",
    )
    selected_str = selected_date.strftime("%Y-%m-%d")
with c2:
    st.markdown(
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:.62rem;color:#333;padding-top:10px'>"
        f"JST {jst_now.strftime('%H:%M')}</div>", unsafe_allow_html=True
    )
with c3:
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

today_s     = jst_now.strftime("%Y-%m-%d")
yesterday_s = (jst_now - timedelta(days=1)).strftime("%Y-%m-%d")
dlabel = (
    f"Today · {fmt_date(selected_str)}"     if selected_str == today_s     else
    f"Yesterday · {fmt_date(selected_str)}" if selected_str == yesterday_s else
    fmt_date(selected_str)
)
st.markdown(f"<div class='section-label' style='margin-bottom:.8rem'>{dlabel}</div>", unsafe_allow_html=True)

st.markdown("""
<div class='info-box'>
  NPB data from <strong>NPB.jp</strong> (official game pages, incl. box scores) ·
  KBO data from <strong>eng.koreabaseball.com</strong> (official KBO English site) ·
  Player links → Baseball Reference · Cache: 5 min
</div>""", unsafe_allow_html=True)

t_npb, t_kbo = st.tabs(["🇯🇵  NPB Scores", "🇰🇷  KBO Scores"])

with t_npb:
    scores_page_npb(selected_str)

with t_kbo:
    scores_page_kbo(selected_str)

st.markdown("---")
st.markdown(
    f"<span style='font-family:IBM Plex Mono,monospace;font-size:.58rem;color:#222;letter-spacing:.1em'>"
    f"NPB.jp · eng.koreabaseball.com · {datetime.now(JST).year} season</span>",
    unsafe_allow_html=True
)
