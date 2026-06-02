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
.info-box { font-family:'IBM Plex Mono',monospace; font-size:.7rem; color:#555; letter-spacing:.1em; background:#111; border:1px solid #1e1e1e; border-radius:5px; padding:10px 14px; margin-bottom:12px; line-height:1.7; }
.err-box { font-family:'IBM Plex Mono',monospace; font-size:.7rem; color:#884444; letter-spacing:.1em; background:#1a1010; border:1px solid #331a1a; border-radius:5px; padding:10px 14px; margin-bottom:8px; line-height:1.7; }
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
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# Navigation / UI words that appear on npb.jp but are NOT team names
NPB_NAV_WORDS = {
    "prev", "next", "games", "regular", "season", "farm", "league", "interleague",
    "central", "pacific", "standings", "stats", "teams", "players", "calendar",
    "schedules", "scores", "nippon", "professional", "baseball", "organization",
    "english", "japanese", "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "game", "result", "match", "back", "number", "abbreviations", "register",
}

# Known NPB team short names as they appear on npb.jp English pages
NPB_TEAM_NAMES = {
    "Yomiuri", "Giants",
    "Hanshin", "Tigers",
    "DeNA", "BayStars", "Baystars",
    "Hiroshima", "Carp",
    "Yakult", "Swallows",
    "Chunichi", "Dragons",
    "SoftBank", "Hawks",
    "Nippon-Ham", "Fighters",
    "ORIX", "Orix", "Buffaloes",
    "Rakuten", "Eagles",
    "Seibu", "Lions",
    "Lotte", "Marines",
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

def is_nav_word(text: str) -> bool:
    return text.lower().strip() in NPB_NAV_WORDS


# ══════════════════════════════════════════════════════════════════════════════
# NPB SCRAPER  —  npb.jp/bis/eng/YYYY/games/gmYYYYMMDD.html
#
# HTML structure (from live inspection):
#   The page has a <div id="contentsMain"> or <div class="contentsMain">
#   Each game sits in a <div class="largeScore"> (completed) or layout table row
#
#   Completed game layout (table-based):
#     <table class="largeScoreTable"> or similar
#       <tr>
#         <td class="teamName away"><a>Nippon-Ham</a></td>
#         <td class="score away">3</td>
#         <td class="scoreSep">-</td>
#         <td class="score home">1</td>
#         <td class="teamName home"><a>Yomiuri</a></td>
#       </tr>
#       <tr class="stadium"><td colspan="5">ES CON FIELD</td></tr>
#
#   Scheduled game layout:
#     Same structure but score cells contain time "14:00" instead of digits
#
#   Section headers: <h3> or <div class="categoryTitle"> saying "INTERLEAGUE" etc.
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def fetch_npb(date_str: str) -> tuple[list, str, str]:
    """Returns (games, error_msg, source_url)"""
    year    = date_str[:4]
    compact = date_str.replace("-", "")
    url     = f"https://npb.jp/bis/eng/{year}/games/gm{compact}.html"

    try:
        r = requests.get(url, headers={**HEADERS, "Referer": "https://npb.jp/"}, timeout=14)
    except Exception as e:
        return [], f"Network error: {e}", url

    if r.status_code == 404:
        return [], "No games page for this date (off-day or outside season).", url
    if r.status_code != 200:
        return [], f"NPB.jp returned HTTP {r.status_code}.", url

    soup = BeautifulSoup(r.text, "lxml")
    games = []

    # ── Strategy 1: Find score tables ──────────────────────────────────────
    # npb.jp wraps each game in a table; look for tds with class containing "score"
    # The away team is always listed first (left side), home team second (right)

    # Find all <img> alt tags — team logos have alt text = short team name
    # e.g. <img src="logo_f_l.gif" alt="Nippon-Ham Fighters">
    # These are reliable team name sources, uncontaminated by nav text

    # Walk all <table> elements in order; each game is typically one table
    all_tables = soup.find_all("table")

    for tbl in all_tables:
        tbl_text = tbl.get_text(" ", strip=True)

        # Skip nav/header tables (they're short and contain nav keywords)
        if len(tbl_text) > 500:
            continue

        # Extract team names from img alt attributes within this table
        imgs = tbl.find_all("img")
        team_names_from_imgs = []
        for img in imgs:
            alt = img.get("alt", "").strip()
            # Filter out league logos (Central League, Pacific League, etc.)
            if alt and not any(skip in alt.lower() for skip in ["league", "japan baseball", "samurai"]):
                # Clean: "Nippon-Ham Fighters" → "Nippon-Ham" (use short form)
                team_names_from_imgs.append(alt)

        # Extract scores: look for <td> cells that are purely digits (1-2 digit)
        score_cells = []
        for td in tbl.find_all("td"):
            t = td.get_text(strip=True)
            if re.match(r"^\d{1,2}$", t):
                score_cells.append(t)

        # Extract time: look for HH:MM pattern
        time_m = re.search(r"\b(\d{1,2}:\d{2})\b", tbl_text)

        # Extract venue: look for known stadium keywords or a dedicated cell
        venue = ""
        for td in tbl.find_all("td"):
            t = td.get_text(strip=True)
            if any(kw in t for kw in ["Dome", "Stadium", "Field", "Marine", "Koshien",
                                       "Jingu", "Mazda", "Koushien", "PayPay", "Belluna",
                                       "Kyocera", "ZOZO", "ES CON", "Vantelin", "Rakuten"]):
                venue = t
                break

        if len(team_names_from_imgs) >= 2 and len(score_cells) >= 2:
            away_name = team_names_from_imgs[0]
            home_name = team_names_from_imgs[1]
            games.append({
                "away": away_name, "home": home_name,
                "away_score": score_cells[0], "home_score": score_cells[1],
                "venue": venue, "time": "",
                "status": "FINAL",
            })
        elif len(team_names_from_imgs) >= 2 and time_m:
            games.append({
                "away": team_names_from_imgs[0], "home": team_names_from_imgs[1],
                "away_score": None, "home_score": None,
                "venue": venue, "time": time_m.group(1),
                "status": "SCHEDULED",
            })

    # ── Strategy 2: img alt fallback if no tables matched ──────────────────
    if not games:
        # Collect all team logo images in document order
        # npb.jp logo filenames: logo_f_l.gif, logo_g_l.gif etc (large logos = game page)
        team_imgs = []
        for img in soup.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "").strip()
            # Large logos on game pages use "_l.gif" suffix
            if "_l.gif" in src and alt and "league" not in alt.lower() and "samurai" not in alt.lower() and "japan" not in alt.lower():
                team_imgs.append((alt, img))

        # Pair them up: even index = away, odd index = home
        page_text = soup.get_text(" ")
        all_times = re.findall(r"\b(\d{1,2}:\d{2})\b", page_text)
        # Extract all standalone score numbers near team logo pairs
        # We look for digits between paired logos using document position
        # This is a simplified pairing — assumes games appear in order
        for i in range(0, len(team_imgs) - 1, 2):
            away_name = team_imgs[i][0]
            home_name = team_imgs[i + 1][0]
            time_val  = all_times[i // 2] if i // 2 < len(all_times) else ""
            games.append({
                "away": away_name, "home": home_name,
                "away_score": None, "home_score": None,
                "venue": "", "time": time_val,
                "status": "SCHEDULED",
            })

    if not games:
        return [], (
            "Could not parse game data from NPB.jp. "
            "The page may use JavaScript-rendered scores or an unexpected layout."
        ), url

    return games, "", url


# ══════════════════════════════════════════════════════════════════════════════
# KBO SCRAPER  —  mykbostats.com/games/YYYY-MM-DD
#
# HTML structure:
#   Each game is a <div class="game-card"> or <div class="game">
#   Inside: away team, away score, home team, home score, game status
#   Game status: "Final" text or a time like "6:30 PM"
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def fetch_kbo(date_str: str) -> tuple[list, str, str]:
    """Returns (games, error_msg, source_url)"""
    url = f"https://mykbostats.com/games/{date_str}"

    try:
        r = requests.get(url, headers={**HEADERS, "Referer": "https://mykbostats.com/"}, timeout=14)
    except Exception as e:
        return [], f"Network error: {e}", url

    if r.status_code == 404:
        return [], f"No KBO games found for {fmt_date(date_str)}.", url
    if r.status_code != 200:
        return [], f"MyKBOStats returned HTTP {r.status_code}.", url

    soup = BeautifulSoup(r.text, "lxml")
    games = []

    # mykbostats game cards — try multiple known class patterns
    cards = (
        soup.select("div.game-card") or
        soup.select("div.game-box") or
        soup.select("div.game_card") or
        soup.select("article.game") or
        # broad fallback: any div whose class contains 'game'
        [d for d in soup.find_all("div") if "game" in " ".join(d.get("class", [])).lower()
         and 30 < len(d.get_text(strip=True)) < 400]
    )

    # Remove duplicates (child divs of already-matched parents)
    seen_ids = set()
    unique_cards = []
    for c in cards:
        cid = id(c)
        if cid not in seen_ids:
            # Check it's not a child of another card we've already added
            if not any(c in uc.descendants for uc in unique_cards):
                unique_cards.append(c)
                seen_ids.add(cid)

    for card in unique_cards:
        # Try structured CSS selectors first
        team_els  = card.select(".team-name, .team_name, .teamName, span.name, a.team-link, .away-team, .home-team")
        score_els = card.select(".score, .run, .runs, td.score, span.score, .total-score")
        status_el = card.select_one(".status, .game-status, .final, .result, .inning")

        away, home = None, None
        away_score, home_score = None, None

        if len(team_els) >= 2:
            away = team_els[0].get_text(strip=True)
            home = team_els[1].get_text(strip=True)

        score_vals = [s.get_text(strip=True) for s in score_els
                      if re.match(r"^\d+$", s.get_text(strip=True))]
        if len(score_vals) >= 2:
            away_score, home_score = score_vals[0], score_vals[1]

        # If structured selectors failed, try regex on card text
        if not away or not home:
            text = card.get_text(" ", strip=True)
            # Pattern: "TeamA N TeamB M Final" or "TeamA @ TeamB TIME"
            m = re.search(
                r"([A-Za-z][A-Za-z\s\-\.]+?)\s+(\d{1,2})\s+([A-Za-z][A-Za-z\s\-\.]+?)\s+(\d{1,2})\s*(?:Final|F\b|–|$)",
                text, re.IGNORECASE
            )
            if m:
                away, home = m.group(1).strip(), m.group(3).strip()
                away_score, home_score = m.group(2), m.group(4)
            else:
                m2 = re.search(
                    r"([A-Za-z][A-Za-z\s\-]+?)\s+[@vs\.]+\s+([A-Za-z][A-Za-z\s\-]+?)\s+(\d{1,2}:\d{2})",
                    text, re.IGNORECASE
                )
                if m2:
                    away, home = m2.group(1).strip(), m2.group(2).strip()

        if not away or not home:
            continue

        # Determine status
        status_text = status_el.get_text(strip=True) if status_el else card.get_text(" ", strip=True)
        is_final = bool(re.search(r"\bfinal\b|\bF\b", status_text, re.I))
        time_m   = re.search(r"(\d{1,2}:\d{2}\s*(?:AM|PM)?(?:\s*KST)?)", status_text, re.IGNORECASE)

        if away_score and home_score:
            status = "FINAL"
        elif is_final:
            status = "FINAL"
        elif time_m:
            status = time_m.group(1).strip()
        else:
            status = "SCHEDULED"

        games.append({
            "away": away, "home": home,
            "away_score": away_score if (away_score and home_score) else None,
            "home_score": home_score if (away_score and home_score) else None,
            "venue": "", "time": time_m.group(1) if time_m else "",
            "status": status,
        })

    if not games:
        return [], (
            f"Scraped MyKBOStats but could not extract games for {fmt_date(date_str)}. "
            "The page structure may differ — check the source link."
        ), url

    return games, "", url


# ══════════════════════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════════════════════

def render_card(g: dict, league: str, date_str: str):
    away   = g.get("away", "?")
    home   = g.get("home", "?")
    as_    = g.get("away_score")
    hs     = g.get("home_score")
    venue  = g.get("venue", "")
    time_  = g.get("time", "")
    status = g.get("status", "")
    final  = as_ is not None and hs is not None

    ac, hc = winner_cls(as_, hs) if final else ("neutral", "neutral")
    as_d   = str(as_) if final else "–"
    hs_d   = str(hs) if final else "–"

    if status == "FINAL":
        label = "FINAL"
    elif status in ("IN PROGRESS", "LIVE", "INPROGRESS"):
        label = "🔴 LIVE"
    elif time_:
        tz = "JST" if league == "NPB" else "KST"
        label = f"{time_} {tz}"
    else:
        label = "SCHEDULED"

    year    = date_str[:4]
    compact = date_str.replace("-", "")

    if league == "NPB":
        npb_url = f"https://npb.jp/bis/eng/{year}/games/gm{compact}.html"
        links = (
            f'<a class="ext-link" href="{npb_url}" target="_blank">NPB.jp</a>'
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
        <div class="card-meta">{label}</div>
        <div class="card-links">{links}</div>
      </div>
    </div>""", unsafe_allow_html=True)


def scores_page(league: str, date_str: str):
    if league == "NPB":
        with st.spinner("Fetching from NPB.jp…"):
            games, err, src_url = fetch_npb(date_str)
    else:
        with st.spinner("Fetching from MyKBOStats…"):
            games, err, src_url = fetch_kbo(date_str)

    if err:
        st.markdown(f"<div class='err-box'>⚠ {err}</div>", unsafe_allow_html=True)
        st.markdown(f"[View source directly ↗]({src_url})", unsafe_allow_html=False)

    if not games and not err:
        st.markdown(
            f"<div class='no-games'>No {league} games found for {fmt_date(date_str)}</div>",
            unsafe_allow_html=True
        )
        return

    for g in games:
        render_card(g, league, date_str)


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
    f"Today · {fmt_date(selected_str)}"     if selected_str == today_s else
    f"Yesterday · {fmt_date(selected_str)}" if selected_str == yesterday_s else
    fmt_date(selected_str)
)
st.markdown(f"<div class='section-label' style='margin-bottom:.8rem'>{dlabel}</div>", unsafe_allow_html=True)

st.markdown("""
<div class='info-box'>
  Data scraped live from <strong>NPB.jp</strong> (official) and <strong>MyKBOStats.com</strong>.
  Cache: 5 min &nbsp;·&nbsp; Use source links on each card for full box scores.
</div>""", unsafe_allow_html=True)

t_npb, t_kbo = st.tabs(["🇯🇵  NPB Scores", "🇰🇷  KBO Scores"])

with t_npb:
    scores_page("NPB", selected_str)

with t_kbo:
    scores_page("KBO", selected_str)

st.markdown("---")
st.markdown(
    f"<span style='font-family:IBM Plex Mono,monospace;font-size:.58rem;color:#222;letter-spacing:.1em'>"
    f"Sources: NPB.jp · MyKBOStats.com · {datetime.now(JST).year} season</span>",
    unsafe_allow_html=True
)
