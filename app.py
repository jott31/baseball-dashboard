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
.no-games { font-family:'IBM Plex Mono',monospace; font-size:.75rem; color:#2a2a2a; letter-spacing:.12em; padding:28px 0; text-align:center; border:1px dashed #181818; border-radius:6px; margin:8px 0; }
.err-box { font-family:'IBM Plex Mono',monospace; font-size:.7rem; color:#555; letter-spacing:.1em; background:#111; border:1px solid #1e1e1e; border-radius:5px; padding:10px 14px; margin-bottom:12px; line-height:1.7; }
.sched-date-hdr { font-family:'IBM Plex Mono',monospace; font-size:.6rem; color:#333; letter-spacing:.2em; text-transform:uppercase; margin:14px 0 6px 0; }
.sched-card { background:#0d0d0d; border:1px solid #181818; border-radius:6px; padding:12px 16px; margin-bottom:6px; }
.sched-matchup { display:flex; justify-content:space-between; align-items:center; }
.sched-teams { font-family:'Bebas Neue',sans-serif; font-size:1.3rem; letter-spacing:.05em; color:#bbb; }
.sched-at { color:#2a2a2a; margin:0 8px; }
.sched-time { font-family:'IBM Plex Mono',monospace; font-size:.68rem; color:#444; letter-spacing:.1em; }
.sched-venue { font-family:'IBM Plex Mono',monospace; font-size:.58rem; color:#2a2a2a; margin-top:3px; }
#MainMenu, footer, header { visibility:hidden; }
div[data-testid="stDecoration"] { display:none; }
div[data-baseweb="tab-list"] { gap:2px; border-bottom:1px solid #1a1a1a !important; }
div[data-baseweb="tab"] { background:transparent !important; font-family:'IBM Plex Mono',monospace !important; font-size:.7rem !important; letter-spacing:.12em !important; color:#444 !important; padding:8px 16px !important; border-bottom:2px solid transparent !important; }
div[aria-selected="true"][data-baseweb="tab"] { color:#ddd !important; border-bottom:2px solid #ddd !important; background:transparent !important; }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ──────────────────────────────────────────────────────────────────
JST = ZoneInfo("Asia/Tokyo")
KST = ZoneInfo("Asia/Seoul")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
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


# ══════════════════════════════════════════════════════════════════════════════
# NPB  —  scrape npb.jp/bis/eng
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def fetch_npb_games(date_str: str) -> tuple[list, str]:
    """
    Scrape npb.jp/bis/eng/YYYY/games/gmYYYYMMDD.html
    Returns (games_list, error_msg).
    Each game dict: away, home, away_score, home_score, venue, time, status, detail_url
    """
    year = date_str[:4]
    compact = date_str.replace("-", "")
    url = f"https://npb.jp/bis/eng/{year}/games/gm{compact}.html"

    try:
        r = requests.get(url, headers={**HEADERS, "Referer": "https://npb.jp/bis/eng/"}, timeout=12)
        if r.status_code == 404:
            return [], "No games page found for this date (off-day or pre-season)."
        if r.status_code != 200:
            return [], f"NPB.jp returned HTTP {r.status_code}. Try a different date."
    except Exception as e:
        return [], f"Network error fetching NPB data: {e}"

    soup = BeautifulSoup(r.text, "lxml")
    games = []

    # npb.jp game rows: each game is a <div class="largeScore"> or a <table> row
    # The page uses <section class="gameSchedule"> with game blocks inside
    # Each game block has: away team, score (if final), home team, venue, time
    # Structure: <div class="gameBox"> or <li> items under schedule section

    # Primary structure: tables with class containing "score" or game data
    # Try multiple known selectors for robustness

    # Method 1: look for the standard npb game result table rows
    # Each game is a <tr> inside a results table, with td elements for teams/scores
    game_blocks = soup.select("div.largeScore, div.scoreBoard, table.scoreTable tr.game")

    if not game_blocks:
        # Method 2: find by the pattern of team name links next to score spans
        # The page layout has a section per game with home/away teams
        # Look for divs that contain both team names and a score separator
        game_blocks = soup.select("section.gameSection, div.gameBlock, li.gameRow")

    if not game_blocks:
        # Method 3: parse the raw structure — npb.jp uses a specific layout
        # Each game is wrapped in a container; teams are in <p> or <span class="teamName">
        # Scores are in <span class="score"> or <strong>
        # Fall back to finding all score-like patterns in the page
        score_pattern = soup.find_all(string=re.compile(r"^\s*\d+\s*$"))

        # Last resort: find game containers by looking for venue/stadium references
        containers = []
        for tag in soup.find_all(["div", "section", "article"]):
            text = tag.get_text(" ", strip=True)
            # A game block will have two team names and either a score or a time
            if re.search(r"\d+:\d+", text) or re.search(r"\d+\s*[-–]\s*\d+", text):
                if len(text) < 400:  # avoid matching the whole page
                    containers.append(tag)
        game_blocks = containers[:12]  # cap at 12 games max

    # Parse whichever blocks we found
    for block in game_blocks:
        text = block.get_text(" ", strip=True)
        # Extract teams (capitalized words) and scores (digits)
        # This is a best-effort parse; npb.jp structure is consistent enough
        teams = re.findall(r"([A-Z][a-zA-Z\-]+(?:\s[A-Z][a-zA-Z\-]+)*)", text)
        scores = re.findall(r"\b(\d{1,2})\b", text)
        time_m = re.search(r"(\d{1,2}:\d{2})", text)
        venue_tag = block.find(class_=re.compile(r"stadium|venue|ball.?park", re.I))
        venue = venue_tag.get_text(strip=True) if venue_tag else ""

        if len(teams) >= 2 and len(scores) >= 2:
            games.append({
                "away": teams[0], "home": teams[1],
                "away_score": scores[0], "home_score": scores[1],
                "venue": venue, "time": time_m.group(1) if time_m else "",
                "status": "FINAL", "detail_url": url,
            })
        elif len(teams) >= 2 and time_m:
            games.append({
                "away": teams[0], "home": teams[1],
                "away_score": None, "home_score": None,
                "venue": venue, "time": time_m.group(1),
                "status": "SCHEDULED", "detail_url": url,
            })

    if not games:
        return [], (
            "Could not parse games from NPB.jp for this date. "
            "The page may use JavaScript rendering or the layout may have changed. "
            "Check the source directly: " + url
        )

    return games, ""


@st.cache_data(ttl=300)
def fetch_npb_games_v2(date_str: str) -> tuple[list, str]:
    """
    Improved NPB scraper targeting the actual npb.jp HTML structure.
    npb.jp game pages have a very specific table layout:
      - Game rows contain: away_team | away_score | '-' | home_score | home_team | venue | time/status
    """
    year = date_str[:4]
    compact = date_str.replace("-", "")
    url = f"https://npb.jp/bis/eng/{year}/games/gm{compact}.html"

    try:
        r = requests.get(url, headers={**HEADERS, "Referer": "https://npb.jp/bis/eng/"}, timeout=12)
        if r.status_code == 404:
            return [], f"No games found for {fmt_date(date_str)} (off-day or pre-season)."
        if r.status_code != 200:
            return [], f"NPB.jp returned HTTP {r.status_code}."
    except Exception as e:
        return [], f"Could not reach NPB.jp: {e}"

    soup = BeautifulSoup(r.text, "lxml")
    games = []

    # npb.jp uses a <div id="contentsMain"> with game score blocks
    # Each game: <div class="scoreWrap"> or similar, containing team names + scores
    # The English page at gm*.html has a consistent table-based layout

    # Find all tables in the main content
    main = soup.find(id="contentsMain") or soup.find(id="contents") or soup.body

    # Look for the score tables — they have a specific pattern:
    # TD with team name, TD with score digits, TD with '-', TD with score, TD with team name
    all_rows = main.find_all("tr") if main else []

    i = 0
    current_venue = ""
    current_time = ""

    for row in all_rows:
        cells = row.find_all("td")
        if not cells:
            continue

        texts = [c.get_text(strip=True) for c in cells]
        full_row = " ".join(texts)

        # Detect venue/time row (contains stadium name + time like "18:00")
        time_m = re.search(r"(\d{1,2}:\d{2})", full_row)
        if time_m and len(cells) <= 3:
            current_time = time_m.group(1)
            current_venue = texts[0] if texts else ""
            continue

        # Detect score row: should have at least 4 cells with team-score-sep-score-team pattern
        if len(cells) >= 4:
            # Check if any cell looks like a score (1-2 digit number)
            score_cells = [t for t in texts if re.match(r"^\d{1,2}$", t)]
            # Check if we have two team-like names
            team_cells = [t for t in texts if len(t) > 2 and not re.match(r"^[\d\-–]+$", t)]

            if len(score_cells) >= 2 and len(team_cells) >= 2:
                away_team = team_cells[0]
                home_team = team_cells[1]
                away_score = score_cells[0]
                home_score = score_cells[1]

                games.append({
                    "away": away_team,
                    "home": home_team,
                    "away_score": away_score,
                    "home_score": home_score,
                    "venue": current_venue,
                    "time": current_time,
                    "status": "FINAL",
                    "detail_url": url,
                })
                current_venue = ""
                current_time = ""

    # If table parsing found nothing, try div-based parsing
    if not games:
        # npb.jp wraps each game in a div with class like "scoreBoard" or "gameScore"
        for div in (main.find_all("div") if main else []):
            cls = " ".join(div.get("class", []))
            if not re.search(r"score|game|match", cls, re.I):
                continue
            text = div.get_text(" ", strip=True)
            if len(text) > 300 or len(text) < 10:
                continue

            teams = [w for w in re.findall(r"[A-Z][a-z]+(?:[A-Z][a-z]+|\s[A-Z][a-z]+)*", text)
                     if len(w) > 3]
            scores = re.findall(r"\b(\d{1,2})\b", text)
            time_m = re.search(r"(\d{1,2}:\d{2})", text)

            if len(teams) >= 2 and len(scores) >= 2:
                games.append({
                    "away": teams[0], "home": teams[1],
                    "away_score": scores[0], "home_score": scores[1],
                    "venue": "", "time": "",
                    "status": "FINAL", "detail_url": url,
                })
            elif len(teams) >= 2 and time_m:
                games.append({
                    "away": teams[0], "home": teams[1],
                    "away_score": None, "home_score": None,
                    "venue": "", "time": time_m.group(1),
                    "status": "SCHEDULED", "detail_url": url,
                })

    if not games:
        return [], (
            f"Scraped NPB.jp but could not extract game data for {fmt_date(date_str)}. "
            f"The page structure may have changed — check directly: {url}"
        )

    return games, ""


# ══════════════════════════════════════════════════════════════════════════════
# KBO  —  scrape mykbostats.com
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def fetch_kbo_games(date_str: str) -> tuple[list, str]:
    """
    Scrape mykbostats.com/games/YYYY-MM-DD
    Returns (games_list, error_msg)
    """
    url = f"https://mykbostats.com/games/{date_str}"

    try:
        r = requests.get(url, headers={**HEADERS, "Referer": "https://mykbostats.com/"}, timeout=12)
        if r.status_code == 404:
            return [], f"No KBO games found for {fmt_date(date_str)}."
        if r.status_code != 200:
            return [], f"MyKBOStats returned HTTP {r.status_code}."
    except Exception as e:
        return [], f"Could not reach MyKBOStats: {e}"

    soup = BeautifulSoup(r.text, "lxml")
    games = []

    # mykbostats.com game cards have a consistent structure:
    # <div class="game-card"> or <div class="game"> containing:
    #   - away team name + score
    #   - home team name + score
    #   - status (Final / time)
    #   - venue

    game_cards = soup.select("div.game-card, div.game-box, article.game, div.game")

    if not game_cards:
        # Try table-based layout
        game_cards = soup.select("table.games tr.game-row, tr.game")

    if not game_cards:
        # Broad fallback: find divs that look like game containers
        for div in soup.find_all("div"):
            cls = " ".join(div.get("class", []))
            if re.search(r"game", cls, re.I) and 20 < len(div.get_text(strip=True)) < 300:
                game_cards.append(div)

    for card in game_cards:
        text = card.get_text(" ", strip=True)

        # Extract team names and scores
        # mykbostats typically shows: "TeamA  5  TeamB  3  Final"
        # or "TeamA  TeamB  7:00 PM KST"
        
        # Try to find score pattern: digits surrounded by team names
        score_m = re.search(
            r"([A-Za-z][A-Za-z\s]+?)\s+(\d{1,2})\s+([A-Za-z][A-Za-z\s]+?)\s+(\d{1,2})\s*(Final|F\b)?",
            text, re.IGNORECASE
        )
        sched_m = re.search(
            r"([A-Za-z][A-Za-z\s]+?)\s+(?:@|vs\.?)\s+([A-Za-z][A-Za-z\s]+?)\s+(\d{1,2}:\d{2})",
            text, re.IGNORECASE
        )
        time_m = re.search(r"(\d{1,2}:\d{2}\s*(?:AM|PM)?(?:\s*KST)?)", text, re.IGNORECASE)

        # Look for team name elements specifically
        team_els = card.select(".team-name, .team, span.name, a.team")
        score_els = card.select(".score, span.score, td.score")
        status_el = card.select_one(".status, .game-status, .result")

        if team_els and len(team_els) >= 2:
            away = team_els[0].get_text(strip=True)
            home = team_els[1].get_text(strip=True)
            scores = [s.get_text(strip=True) for s in score_els if re.match(r"^\d+$", s.get_text(strip=True))]
            status_text = status_el.get_text(strip=True) if status_el else ""
            final = bool(re.search(r"final|f\b", status_text, re.I))

            if len(scores) >= 2:
                games.append({
                    "away": away, "home": home,
                    "away_score": scores[0], "home_score": scores[1],
                    "venue": "", "time": "",
                    "status": "FINAL" if final else status_text,
                    "detail_url": url,
                })
            elif time_m:
                games.append({
                    "away": away, "home": home,
                    "away_score": None, "home_score": None,
                    "venue": "", "time": time_m.group(1),
                    "status": "SCHEDULED", "detail_url": url,
                })
        elif score_m:
            games.append({
                "away": score_m.group(1).strip(),
                "home": score_m.group(3).strip(),
                "away_score": score_m.group(2),
                "home_score": score_m.group(4),
                "venue": "", "time": "",
                "status": "FINAL", "detail_url": url,
            })
        elif sched_m:
            games.append({
                "away": sched_m.group(1).strip(),
                "home": sched_m.group(2).strip(),
                "away_score": None, "home_score": None,
                "venue": "", "time": sched_m.group(3),
                "status": "SCHEDULED", "detail_url": url,
            })

    if not games:
        return [], (
            f"Scraped MyKBOStats but could not extract game data for {fmt_date(date_str)}. "
            f"Check directly: {url}"
        )

    return games, ""


# ══════════════════════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════════════════════
def render_game_card(g: dict, league: str, date_str: str):
    away  = g.get("away", "?")
    home  = g.get("home", "?")
    as_   = g.get("away_score")
    hs    = g.get("home_score")
    venue = g.get("venue", "")
    time_ = g.get("time", "")
    status = g.get("status", "")
    detail = g.get("detail_url", "")
    final  = as_ is not None and hs is not None

    ac, hc = winner_cls(as_, hs) if final else ("neutral", "neutral")
    as_d = str(as_) if final else "–"
    hs_d = str(hs) if final else "–"

    if final:
        status_label = "FINAL"
    elif status.upper() in ("LIVE", "IN PROGRESS", "INPROGRESS"):
        status_label = f"🔴 LIVE"
    elif time_:
        status_label = f"{time_} JST" if league == "NPB" else f"{time_} KST"
    else:
        status_label = status or "SCHEDULED"

    year = date_str[:4]
    if league == "NPB":
        links = (
            f'<a class="ext-link" href="https://npb.jp/bis/eng/{year}/games/" target="_blank">NPB.jp</a>'
            f'<a class="ext-link" href="https://www.baseball-reference.com/leagues/NPB/{year}-schedule.shtml" target="_blank">BBRef</a>'
        )
    else:
        links = (
            f'<a class="ext-link" href="https://mykbostats.com/games/{date_str}" target="_blank">MyKBOStats</a>'
            f'<a class="ext-link" href="https://eng.koreabaseball.com/Schedule/GameCenter/Main.aspx" target="_blank">KBO Center</a>'
            f'<a class="ext-link" href="https://www.baseball-reference.com/leagues/KBO/{year}-schedule.shtml" target="_blank">BBRef</a>'
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
        <div class="card-meta">{status_label}</div>
        <div class="card-links">{links}</div>
      </div>
    </div>""", unsafe_allow_html=True)


def scores_page(league: str, date_str: str):
    if league == "NPB":
        with st.spinner("Fetching NPB scores from NPB.jp…"):
            games, err = fetch_npb_games_v2(date_str)
    else:
        with st.spinner("Fetching KBO scores from MyKBOStats…"):
            games, err = fetch_kbo_games(date_str)

    if err:
        st.markdown(f"<div class='err-box'>⚠ {err}</div>", unsafe_allow_html=True)
        # Show fallback link
        year = date_str[:4]
        if league == "NPB":
            compact = date_str.replace("-", "")
            fb_url = f"https://npb.jp/bis/eng/{year}/games/gm{compact}.html"
            st.markdown(f"[View on NPB.jp directly ↗]({fb_url})")
        else:
            st.markdown(f"[View on MyKBOStats directly ↗](https://mykbostats.com/games/{date_str})")

    if not games and not err:
        st.markdown(
            f"<div class='no-games'>No {league} games found for {fmt_date(date_str)}</div>",
            unsafe_allow_html=True
        )
        return

    for g in games:
        render_game_card(g, league, date_str)


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
if selected_str == today_s:
    dlabel = f"Today · {fmt_date(selected_str)}"
elif selected_str == yesterday_s:
    dlabel = f"Yesterday · {fmt_date(selected_str)}"
else:
    dlabel = fmt_date(selected_str)

st.markdown(
    f"<div class='section-label' style='margin-bottom:.8rem'>{dlabel}</div>",
    unsafe_allow_html=True
)

st.markdown("""
<div class='err-box'>
  Data scraped from <strong>NPB.jp</strong> (official) and <strong>MyKBOStats.com</strong> —
  no API key required. Results update every 5 min. Use the links on each card for full box scores.
</div>""", unsafe_allow_html=True)

t_npb, t_kbo = st.tabs([
    "🇯🇵  NPB Scores",
    "🇰🇷  KBO Scores",
])

with t_npb:
    scores_page("NPB", selected_str)

with t_kbo:
    scores_page("KBO", selected_str)

st.markdown("---")
st.markdown(
    f"<span style='font-family:IBM Plex Mono,monospace;font-size:.58rem;color:#222;letter-spacing:.1em'>"
    f"Sources: NPB.jp · MyKBOStats.com · Cache: 5 min · "
    f"{datetime.now(JST).year} season</span>",
    unsafe_allow_html=True
)
