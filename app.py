import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
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
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%A, %B %-d")
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

    # Individual game links match pattern: s{YYYYMMDD}{5-digits}.html
    # e.g. s2026052901848.html  — only regular season (not farm = fgm*)
    game_links = []
    pattern    = re.compile(rf"s{compact}\d{{5}}\.html")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        # href may be relative ("s2026052901848.html") or absolute
        filename = href.split("/")[-1]
        if pattern.match(filename):
            full_url = base + filename if not href.startswith("http") else href
            if full_url not in game_links:
                game_links.append(full_url)

    if not game_links:
        # Games may not have individual pages yet (scheduled, not completed)
        # Return empty list with no error — caller will show schedule info
        return [], ""

    return game_links, ""


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — scrape each individual game page
# URL: https://npb.jp/bis/eng/YYYY/games/sYYYYMMDDnnnnn.html
#
# Confirmed structure (from live fetch of s2026052901848.html):
#
#   Page title:  "Friday, May 29, 2026 (Scores) Rakuten vs Yakult"
#
#   Score block (list items):
#     - | | Tokyo Yakult Swallows | 7 |
#     - | | Tohoku Rakuten Golden Eagles | 2 |
#
#   Venue / time line (table):
#     | Rakuten Mobile | T - 3:13 ( 18:00 - 21:13 ) Att. - 25,137 |
#
#   Linescore (text row):
#     Yakult  1 0 0 2 0 0 2 0 2 - 7 15 0
#     Rakuten 0 0 0 0 0 1 0 0 1 - 2 8 1
#
#   The away team is listed FIRST in the score block (top row).
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def parse_npb_game(game_url: str) -> dict:
    """
    Returns a game dict with keys:
      away, home, away_score, home_score, venue, time, status,
      linescore (list of dicts: {team, innings[], r, h, e}),
      game_url
    """
    result = {
        "away": "", "home": "",
        "away_score": None, "home_score": None,
        "venue": "", "time": "",
        "status": "UNKNOWN",
        "linescore": [],
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
    # Structure confirmed from live page fetch of s2026052901848.html:
    #
    #   Score block is a <ul> where each <li> has its OWN single-row table:
    #     <li><table><tr><th/><th>Tokyo Yakult Swallows</th><th>7</th></tr></table></li>
    #     <li><table><tr><th/><th>Tohoku Rakuten Golden Eagles</th><th>2</th></tr></table></li>
    #
    #   Cells are <th> not <td>, and tables are NESTED inside outer layout tables.
    #
    # Previous bugs:
    #   1. Used find_all("td") — missed <th> score cells entirely
    #   2. Used tr.find_all("td") without recursive=False — descended into nested
    #      tables and matched the same row twice (outer tr + inner tr both returned
    #      the same descendant tds), causing both team slots to show the away team.
    #   3. Linescore: same nesting issue caused 4 rows instead of 2.
    #
    # Fix: use tr.find_all(["th","td"], recursive=False) — direct children only.

    # Method A: page title — "Friday, May 29, 2026 (Scores) Rakuten vs Yakult"
    title   = soup.title.string if soup.title else ""
    title_m = re.search(r"\(Scores\)\s+(.+?)\s+vs\s+(.+?)(?:\s*\||\s*$)", title or "")

    # Method B: scan every <tr>, get only its DIRECT child cells (th or td),
    # look for rows shaped like: [empty?] [Team Full Name] [score digit]
    score_rows = []
    for tr in soup.find_all("tr"):
        # recursive=False → only direct children, never descends into nested tables
        cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"], recursive=False)]
        cells = [c for c in cells if c]   # drop empty logo cells
        if len(cells) < 2:
            continue
        last        = cells[-1]
        second_last = cells[-2]
        # Score: 1-2 digit number
        if not re.match(r"^\d{1,2}$", last):
            continue
        # Team name: meaningful length, not starting with digit
        if len(second_last) <= 3 or re.match(r"^\d", second_last):
            continue
        # Exclude stat headers and player rows (player names contain commas)
        if second_last.upper() in {"AB", "IP", "H", "R", "E", "BB", "SO", "HP",
                                    "HB", "ER", "BF", "WP", "LP", "HR", "ERA"}:
            continue
        if "," in second_last or "(" in second_last:
            continue
        score_rows.append((second_last, last))

    # First two valid rows are away then home (document order on npb.jp)
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
    # Line: "Rakuten Mobile | T - 3:13 ( 18:00 - 21:13 ) Att. - 25,137"
    # Venue is first cell, time info is second cell
    for tbl in soup.find_all("table"):
        cells = [td.get_text(strip=True) for td in tbl.find_all("td") if td.get_text(strip=True)]
        if not cells:
            continue
        row_text = " ".join(cells)
        # Look for the venue+time table: contains a time pattern and "Att."
        if re.search(r"\d{1,2}:\d{2}", row_text) and len(cells) >= 2:
            # First meaningful cell = venue
            venue_candidate = cells[0]
            # Exclude cells that look like stats headers (AB, H, RBI etc.)
            if not re.match(r"^(AB|IP|R|H|E|BB|SO|WP|LP|HR)$", venue_candidate):
                if len(venue_candidate) > 2:
                    result["venue"] = venue_candidate
                    # Extract start time from "( 18:00 - 21:13 )"
                    time_m = re.search(r"\(\s*(\d{1,2}:\d{2})\s*-", row_text)
                    if time_m:
                        result["time"] = time_m.group(1)
                    break

    # ── Linescore ────────────────────────────────────────────────────────────
    # Confirmed rows from s2026052901848.html:
    #   "Yakult  1 0 0 2 0 0 2 0 2 - 7 15 0"
    #   "Rakuten 0 0 0 0 0 1 0 0 1 - 2 8 1"
    #
    # Each linescore row is a <tr> inside a table. The full row text
    # matches: ShortName [inning digits...] - R H E
    #
    # Nesting fix: iterate tables, then for each table iterate its direct
    # child <tr> rows only (using find_all("tr", recursive=False) on tbody/table)
    # to avoid matching the same row via both outer and inner table contexts.
    linescore   = []
    seen_ls_ids = set()
    for tbl in soup.find_all("table"):
        # Get direct child rows only — avoids nested table duplication
        direct_rows = tbl.find_all("tr", recursive=False)
        # Also check tbody/thead direct children
        for section in tbl.find_all(["tbody", "thead"], recursive=False):
            direct_rows += section.find_all("tr", recursive=False)
        for row in direct_rows:
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

    # On the day page, each game is represented by two team logo imgs (_l.gif)
    # with adjacent text nodes giving the short team name,
    # and a venue+time text between them.
    #
    # The confirmed markdown showed this pattern (simplified):
    #   logo_f_l.gif  "Nippon-Ham"    "ES CON FIELD 18:00"    logo_g_l.gif  "Yomiuri"
    #
    # Strategy: find all large logo imgs (_l.gif, not _m.gif or _s.gif),
    # collect their surrounding text in document order,
    # then pair them up as away/home.

    large_logos = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "_l.gif" in src and "flag_" not in src and "samurai" not in src.lower() and "japan" not in src.lower():
            # Get the nearest text sibling/parent text as team name
            parent = img.parent
            text   = parent.get_text(strip=True) if parent else ""
            # Also check the next sibling
            if not text or len(text) > 40:
                text = img.get("alt", "").replace("#", "").strip()
            large_logos.append({"text": text, "src": src})

    # Pair up: even index = away, odd = home
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
#   Venue line: "DAEJEON 18:30 W: WILLIAM Tolhurst S: ..."
#   Table row:  TEAMCODE | 1 | 0 | 1 | ... | - | R | H | E | B
#
# Confirmed structure for a SCHEDULED game:
#   Header text: "LG 18:30 KT"
#   Table row:   TEAMCODE | - | - | - | ... | (empty R/H/E/B)
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

def expand_kbo(code: str) -> str:
    return KBO_TEAM_NAMES.get(code.upper().strip(), code.strip().title())

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

    # ── Extract game header texts ─────────────────────────────────────────────
    # Each game header sits between two team logo <img> tags.
    # In the page text between consecutive logo img tags we see:
    #   FINAL game:     "TEAMCODE SCORE FINAL SCORE TEAMCODE"
    #   Scheduled game: "TEAMCODE TIME TEAMCODE"
    #
    # We scan the page text for these patterns, then pair with the
    # subsequent scoreboard table.

    # Pattern for FINAL: e.g. "LG 4 FINAL 1 HANWHA"
    final_pat = re.compile(
        r'\b([A-Z]{2,7})\s+(\d{1,2})\s+FINAL\s+(\d{1,2})\s+([A-Z]{2,7})\b'
    )
    # Pattern for SCHEDULED/LIVE: e.g. "LG 18:30 KT" or "KT 3 LG" (live)
    sched_pat = re.compile(
        r'\b([A-Z]{2,7})\s+(\d{1,2}:\d{2})\s+([A-Z]{2,7})\b'
    )

    page_text = soup.get_text(" ")

    # Build ordered list of game headers from page text
    game_headers = []
    seen_spans = set()

    for m in final_pat.finditer(page_text):
        if m.start() not in seen_spans:
            seen_spans.add(m.start())
            away_code, away_scr, home_scr, home_code = m.group(1), m.group(2), m.group(3), m.group(4)
            # Validate both codes are KBO teams
            if away_code in KBO_TEAM_NAMES and home_code in KBO_TEAM_NAMES:
                game_headers.append({
                    "away": expand_kbo(away_code),
                    "home": expand_kbo(home_code),
                    "away_score": away_scr,
                    "home_score": home_scr,
                    "status": "FINAL",
                    "time": "",
                    "pos": m.start(),
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
                })

    # Sort by position in page (document order)
    game_headers.sort(key=lambda x: x["pos"])

    # ── Extract venue from page text for each game ────────────────────────────
    # Venue line appears right after each header: "DAEJEON 18:30 W: ..."
    # We grab the text between the header match and the next table
    venue_pat = re.compile(r'([A-Z][A-Z\-]+)\s+\d{1,2}:\d{2}')

    # ── Parse linescore tables ────────────────────────────────────────────────
    # Find tables that look like scoreboard tables:
    # first column is a known KBO team code, remaining columns are digits or "-"
    score_tables = []
    for tbl in soup.find_all("table"):
        rows = tbl.find_all("tr", recursive=False)
        if not rows:
            tbody = tbl.find("tbody")
            rows = tbody.find_all("tr", recursive=False) if tbody else []
        if len(rows) < 2:
            continue

        # Check first cell of first two rows is a KBO team code
        codes = []
        for row in rows[:2]:
            first = row.find(["th","td"], recursive=False)
            if first:
                codes.append(first.get_text(strip=True).upper())

        if len(codes) == 2 and all(c in KBO_TEAM_NAMES for c in codes):
            score_tables.append((codes, tbl))

    # ── Match headers to tables and build game dicts ──────────────────────────
    for i, hdr in enumerate(game_headers):
        ls = []
        venue = ""

        if i < len(score_tables):
            codes, tbl = score_tables[i]
            rows = tbl.find_all("tr", recursive=False)
            if not rows:
                tbody = tbl.find("tbody")
                rows = tbody.find_all("tr", recursive=False) if tbody else []

            for row in rows[:2]:
                cells = [c.get_text(strip=True) for c in row.find_all(["th","td"], recursive=False)]
                if not cells:
                    continue
                team_code = cells[0]
                # Remaining cells: innings (digits or "-") then R H E B
                inn_cells = cells[1:]
                # Split into innings and totals: innings end at last "-" or last digit before R
                # R is the first non-inning total — it appears after all innings
                # Innings: cells that are digit or "-"
                # Totals: last 4 cells (R H E B), may be empty string if unplayed
                innings = []
                r_val = None
                if len(inn_cells) >= 4:
                    totals = inn_cells[-4:]   # R, H, E, B
                    inning_cells = inn_cells[:-4]
                    innings = [c for c in inning_cells if c]  # strip empty
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
            "venue":      venue,
            "time":       hdr["time"],
            "status":     hdr["status"],
            "linescore":  ls,
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

    if final and ls:
        with st.expander(f"Linescore — {away} @ {home}"):
            render_linescore(ls)


def scores_page_npb(date_str: str):
    year    = date_str[:4]
    compact = date_str.replace("-", "")

    with st.spinner("Fetching NPB game links…"):
        game_links, err = get_npb_game_links(date_str)

    if err:
        st.markdown(f"<div class='err-box'>⚠ {err}</div>", unsafe_allow_html=True)
        return

    if not game_links:
        # No individual game pages yet — show scheduled games from day page
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

    # Fetch each individual game page
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
    with st.spinner("Fetching KBO scores from MyKBOStats…"):
        games, err, src_url = fetch_kbo(date_str)

    if err:
        st.markdown(f"<div class='err-box'>⚠ {err}</div>", unsafe_allow_html=True)
        st.markdown(f"[View on MyKBOStats ↗]({src_url})")

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
  NPB data from <strong>NPB.jp</strong> (official individual game pages) ·
  KBO data from <strong>MyKBOStats.com</strong> · Cache: 5 min
</div>""", unsafe_allow_html=True)

t_npb, t_kbo = st.tabs(["🇯🇵  NPB Scores", "🇰🇷  KBO Scores"])

with t_npb:
    scores_page_npb(selected_str)

with t_kbo:
    scores_page_kbo(selected_str)

st.markdown("---")
st.markdown(
    f"<span style='font-family:IBM Plex Mono,monospace;font-size:.58rem;color:#222;letter-spacing:.1em'>"
    f"NPB.jp · MyKBOStats.com · {datetime.now(JST).year} season</span>",
    unsafe_allow_html=True
)
