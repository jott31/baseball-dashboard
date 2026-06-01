import streamlit as st
import requests
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NPB · KBO Scores",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── THEME ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0a0a0a;
    color: #e8e8e8;
}

/* Strip default Streamlit padding */
.block-container { padding-top: 1.5rem !important; max-width: 1200px; }

/* ── MASTHEAD ── */
.masthead {
    display: flex; align-items: baseline; gap: 14px;
    border-bottom: 2px solid #222; padding-bottom: 0.8rem; margin-bottom: 1.4rem;
}
.masthead-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.6rem; letter-spacing: 0.08em;
    color: #fff; line-height: 1;
}
.masthead-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem; color: #555; letter-spacing: 0.18em;
    text-transform: uppercase;
}

/* ── DATE PILL NAV ── */
.date-strip {
    display: flex; gap: 6px; margin-bottom: 1.2rem; flex-wrap: wrap;
}

/* ── SECTION HEADER ── */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem; letter-spacing: 0.22em; color: #555;
    text-transform: uppercase; margin-bottom: 0.7rem; margin-top: 0.2rem;
}

/* ── SCORE CARD ── */
.card {
    background: #111; border: 1px solid #1e1e1e;
    border-radius: 6px; padding: 14px 18px;
    margin-bottom: 8px; transition: border-color 0.15s;
    position: relative;
}
.card:hover { border-color: #333; }

.card-league {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.58rem; letter-spacing: 0.2em; color: #555;
    text-transform: uppercase; margin-bottom: 8px;
}
.card-teams {
    display: flex; justify-content: space-between; align-items: center;
    gap: 8px;
}
.team-block { flex: 1; }
.team-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.45rem; letter-spacing: 0.05em;
    color: #e8e8e8; line-height: 1;
}
.team-name.winner { color: #fff; }
.team-name.loser  { color: #555; }

.score-block {
    display: flex; gap: 16px; align-items: center;
    font-family: 'IBM Plex Mono', monospace;
}
.score {
    font-size: 2rem; font-weight: 600; min-width: 2ch; text-align: right;
}
.score.winner { color: #f0f0f0; }
.score.loser  { color: #3a3a3a; }
.score-divider { color: #333; font-size: 1.2rem; }

.card-footer {
    display: flex; justify-content: space-between; align-items: center;
    margin-top: 10px; padding-top: 8px; border-top: 1px solid #1a1a1a;
}
.card-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem; color: #444; letter-spacing: 0.1em;
}
.card-links { display: flex; gap: 10px; }
.ext-link {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem; letter-spacing: 0.08em;
    color: #555; text-decoration: none; border-bottom: 1px solid #2a2a2a;
    transition: color 0.15s, border-color 0.15s; white-space: nowrap;
}
.ext-link:hover { color: #aaa; border-color: #555; }

/* ── LINESCORE TABLE ── */
.linescore-wrap {
    margin-top: 10px; overflow-x: auto;
}
.linescore {
    border-collapse: collapse; width: 100%;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem;
}
.linescore th {
    color: #444; font-weight: 400; letter-spacing: 0.12em;
    padding: 3px 8px; text-align: center; border-bottom: 1px solid #1e1e1e;
}
.linescore td {
    padding: 3px 8px; text-align: center; color: #888;
    border-bottom: 1px dotted #181818;
}
.linescore td.team-col { text-align: left; color: #555; }
.linescore td.total { font-weight: 600; color: #ccc; border-left: 1px solid #222; }

/* ── SCHEDULE CARD ── */
.sched-card {
    background: #0e0e0e; border: 1px solid #1a1a1a;
    border-radius: 6px; padding: 12px 18px; margin-bottom: 6px;
}
.sched-matchup {
    display: flex; justify-content: space-between; align-items: center;
}
.sched-teams {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.3rem; letter-spacing: 0.05em; color: #ccc;
}
.sched-at { color: #333; margin: 0 6px; }
.sched-time {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem; color: #555; letter-spacing: 0.1em;
}
.sched-venue {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem; color: #333; letter-spacing: 0.1em;
    margin-top: 3px;
}
.sched-league {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.58rem; color: #3a3a3a; letter-spacing: 0.2em;
    text-transform: uppercase; margin-bottom: 4px;
}

/* ── DATE TABS ── */
div[data-baseweb="tab-list"] { gap: 4px; }
div[data-baseweb="tab"] {
    background: #111 !important; border-radius: 4px !important;
    border: 1px solid #1e1e1e !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important; letter-spacing: 0.1em !important;
    padding: 6px 14px !important; color: #555 !important;
}
div[aria-selected="true"][data-baseweb="tab"] {
    background: #1a1a1a !important; color: #ddd !important;
    border-color: #333 !important;
}
button[data-testid="stBaseButton-secondary"] {
    background: #111; border: 1px solid #1e1e1e; color: #666;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem;
    letter-spacing: 0.1em; border-radius: 4px;
}
button[data-testid="stBaseButton-secondary"]:hover { border-color: #333; color: #aaa; }

/* ── EMPTY STATE ── */
.empty {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;
    color: #333; letter-spacing: 0.12em; padding: 24px 0;
    text-align: center;
}

/* hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
div[data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
TSDB      = "https://www.thesportsdb.com/api/v1/json/123"
HEADERS   = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
             "Accept": "application/json"}

LEAGUES = {
    "NPB": {"id": "4591", "flag": "🇯🇵", "bbref_prefix": "jpn"},
    "KBO": {"id": "4830", "flag": "🇰🇷", "bbref_prefix": "kor"},
}

# Japan Standard Time / Korea Standard Time (both UTC+9)
JST = ZoneInfo("Asia/Tokyo")


# ── HELPERS ───────────────────────────────────────────────────────────────────

def now_jst() -> datetime:
    return datetime.now(JST)


def jst_today() -> str:
    return now_jst().strftime("%Y-%m-%d")


def jst_yesterday() -> str:
    return (now_jst() - timedelta(days=1)).strftime("%Y-%m-%d")


def fmt_display_date(d: str) -> str:
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%b %-d")
    except Exception:
        return d


def winner_loser(home_score, away_score):
    if home_score is None or away_score is None:
        return None, None
    h, a = int(home_score), int(away_score)
    if h > a:
        return "home", "away"
    elif a > h:
        return "away", "home"
    return "tie", "tie"


def bbref_search_url(player_name: str, league_prefix: str) -> str:
    slug = player_name.lower().replace(" ", "+")
    return f"https://www.baseball-reference.com/search/search.fcgi?search={slug}"


def proeyekyuu_game_url(event_id: str) -> str:
    return f"https://proeyekyuu.com/game/"


def kbo_schedule_url() -> str:
    return "https://eng.koreabaseball.com/Schedule/Schedule.aspx"


# ── API CALLS ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=120)
def fetch_past_events(league_id: str) -> list:
    try:
        r = requests.get(f"{TSDB}/eventspastleague.php?id={league_id}",
                         headers=HEADERS, timeout=12)
        r.raise_for_status()
        return r.json().get("events") or []
    except Exception:
        return []


@st.cache_data(ttl=120)
def fetch_next_events(league_id: str) -> list:
    try:
        r = requests.get(f"{TSDB}/eventsnextleague.php?id={league_id}",
                         headers=HEADERS, timeout=12)
        r.raise_for_status()
        return r.json().get("events") or []
    except Exception:
        return []


@st.cache_data(ttl=300)
def fetch_event_stats(event_id: str) -> list:
    """Returns list of stat dicts: {strTeam, strStat, intValue}"""
    try:
        r = requests.get(f"{TSDB}/lookupeventstats.php?id={event_id}",
                         headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("eventstats") or []
    except Exception:
        return []


@st.cache_data(ttl=300)
def fetch_event_lineup(event_id: str) -> list:
    """Returns lineup/roster entries for the event."""
    try:
        r = requests.get(f"{TSDB}/lookuplineup.php?id={event_id}",
                         headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("lineup") or []
    except Exception:
        return []


@st.cache_data(ttl=300)
def fetch_event_detail(event_id: str) -> dict:
    try:
        r = requests.get(f"{TSDB}/lookupevent.php?id={event_id}",
                         headers=HEADERS, timeout=10)
        r.raise_for_status()
        events = r.json().get("events") or []
        return events[0] if events else {}
    except Exception:
        return {}


# ── LINESCORE PARSER ──────────────────────────────────────────────────────────

def parse_linescore(stats: list, home: str, away: str):
    """
    TSDB event stats may contain inning-by-inning entries labeled
    'Inning 1', 'Inning 2', ... plus 'Runs','Hits','Errors' totals.
    Returns dict with innings + totals per team, or None if unavailable.
    """
    if not stats:
        return None

    innings = {}
    totals  = {}

    for s in stats:
        team = s.get("strTeam", "")
        stat = s.get("strStat", "")
        val  = s.get("intValue", "")

        # Normalise team label — TSDB uses full names
        t = "home" if any(x in team for x in [home[:4], "home", "Home"]) else "away"

        m = re.match(r"^Inning\s+(\d+)$", stat, re.IGNORECASE)
        if m:
            inn = int(m.group(1))
            innings.setdefault(t, {})[inn] = val
        elif stat in ("Runs", "Hits", "Errors"):
            totals.setdefault(t, {})[stat[0]] = val  # R, H, E

    if not innings:
        return None

    max_inn = max(
        (max(d.keys()) for d in innings.values() if d),
        default=0
    )
    if max_inn == 0:
        return None

    return {"innings": innings, "totals": totals, "max_inn": max_inn,
            "home": home, "away": away}


def render_linescore(ls):
    if not ls:
        return
    max_inn = ls["max_inn"]
    inn_nums = list(range(1, max_inn + 1))

    header_cells = "<th class='team-col'></th>" + \
        "".join(f"<th>{i}</th>" for i in inn_nums) + \
        "<th class='total'>R</th><th class='total'>H</th><th class='total'>E</th>"

    rows = ""
    for side in ("away", "home"):
        team_name = ls[side][:12]
        inn_data  = ls["innings"].get(side, {})
        tot_data  = ls["totals"].get(side, {})
        cells = f"<td class='team-col'>{team_name}</td>"
        for i in inn_nums:
            v = inn_data.get(i, "")
            cells += f"<td>{v if v != '' else '–'}</td>"
        cells += f"<td class='total'>{tot_data.get('R','')}</td>"
        cells += f"<td class='total'>{tot_data.get('H','')}</td>"
        cells += f"<td class='total'>{tot_data.get('E','')}</td>"
        rows += f"<tr>{cells}</tr>"

    st.markdown(f"""
    <div class='linescore-wrap'>
      <table class='linescore'>
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)


# ── LINEUP / BOX SCORE DISPLAY ────────────────────────────────────────────────

def render_lineup(lineup: list, home: str, away: str, league: str, bbref_prefix: str):
    """
    Render TSDB lineup entries split by team, with links to Baseball Reference
    and (for NPB) ProEyeKyuu.
    """
    if not lineup:
        st.markdown("<div class='empty'>No lineup data available from TheSportsDB for this game.</div>",
                    unsafe_allow_html=True)
        return

    # Split by team
    away_players, home_players = [], []
    for p in lineup:
        team = p.get("strTeam", "")
        if any(x in team for x in [home[:5], "home", "Home"]):
            home_players.append(p)
        else:
            away_players.append(p)

    # Fallback: split first half / second half
    if not away_players and not home_players:
        mid = len(lineup) // 2
        away_players = lineup[:mid]
        home_players = lineup[mid:]

    def player_row(p: dict) -> str:
        name     = p.get("strPlayer", p.get("strName", "Unknown"))
        position = p.get("strPosition", "")
        number   = p.get("strNumber", "")
        bbref    = bbref_search_url(name, bbref_prefix)
        pek_link = ""
        if league == "NPB":
            pek_link = f' <a class="ext-link" href="https://proeyekyuu.com/player-registry/" target="_blank">PEK</a>'
        num_str  = f"#{number} " if number else ""
        pos_str  = f" <span style='color:#3a3a3a;font-size:0.62rem'>{position}</span>" if position else ""
        return (
            f"<div style='padding:5px 0; border-bottom:1px dotted #161616; "
            f"font-family:IBM Plex Sans,sans-serif; font-size:0.82rem;'>"
            f"<span style='color:#444;font-family:IBM Plex Mono,monospace;font-size:0.62rem'>{num_str}</span>"
            f"<span style='color:#ccc'>{name}</span>{pos_str} "
            f"<a class='ext-link' href='{bbref}' target='_blank'>BBRef</a>"
            f"{pek_link}</div>"
        )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='section-label'>{away} lineup</div>", unsafe_allow_html=True)
        if away_players:
            st.markdown("".join(player_row(p) for p in away_players), unsafe_allow_html=True)
        else:
            st.markdown("<div class='empty'>—</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='section-label'>{home} lineup</div>", unsafe_allow_html=True)
        if home_players:
            st.markdown("".join(player_row(p) for p in home_players), unsafe_allow_html=True)
        else:
            st.markdown("<div class='empty'>—</div>", unsafe_allow_html=True)


# ── SCORE CARD RENDERER ───────────────────────────────────────────────────────

def render_score_card(event: dict, league: str, league_info: dict, show_detail: bool = False):
    home     = event.get("strHomeTeam", "?")
    away     = event.get("strAwayTeam", "?")
    hs_raw   = event.get("intHomeScore")
    as_raw   = event.get("intAwayScore")
    date     = event.get("dateEvent", "")
    venue    = event.get("strVenue", "")
    event_id = event.get("idEvent", "")
    flag     = league_info["flag"]
    bbpfx    = league_info["bbref_prefix"]

    final    = hs_raw is not None and as_raw is not None
    win_side, lose_side = winner_loser(hs_raw, as_raw)

    home_cls = "winner" if win_side == "home" else ("loser" if lose_side == "home" else "")
    away_cls = "winner" if win_side == "away" else ("loser" if lose_side == "away" else "")
    h_cls    = "winner" if win_side == "home" else ("loser" if lose_side == "home" else "")
    a_cls    = "winner" if win_side == "away" else ("loser" if lose_side == "away" else "")

    hs_display = str(hs_raw) if final else "—"
    as_display = str(as_raw) if final else "—"

    # External links
    bbref_game = f"https://www.baseball-reference.com/search/search.fcgi?search={away.replace(' ','+')}+{home.replace(' ','+')}"
    if league == "NPB":
        year_str = date[:4] if date else "2026"
        ext_links = (
            f'<a class="ext-link" href="https://proeyekyuu.com/game/" target="_blank">ProEyeKyuu</a>'
            f'<a class="ext-link" href="https://npb.jp/bis/eng/{year_str}/games/" target="_blank">NPB.jp</a>'
        )
    else:
        ext_links = (
            f'<a class="ext-link" href="https://eng.koreabaseball.com/Schedule/GameCenter/Main.aspx" target="_blank">KBO</a>'
        )
    ext_links += f'<a class="ext-link" href="{bbref_game}" target="_blank">BBRef</a>'

    venue_str = f" · {venue}" if venue else ""

    st.markdown(f"""
    <div class="card">
      <div class="card-league">{flag} {league}{venue_str}</div>
      <div class="card-teams">
        <div class="team-block">
          <div class="team-name {away_cls}">{away}</div>
        </div>
        <div class="score-block">
          <span class="score {a_cls}">{as_display}</span>
          <span class="score-divider">·</span>
          <span class="score {h_cls}">{hs_display}</span>
        </div>
        <div class="team-block" style="text-align:right">
          <div class="team-name {home_cls}" style="text-align:right">{home}</div>
        </div>
      </div>
      <div class="card-footer">
        <div class="card-meta">{date}</div>
        <div class="card-links">{ext_links}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Expandable box score
    if final and event_id:
        with st.expander("Box score / Lineup", expanded=show_detail):
            # Linescore
            stats = fetch_event_stats(event_id)
            ls    = parse_linescore(stats, home, away)
            if ls:
                st.markdown("<div class='section-label'>linescore</div>", unsafe_allow_html=True)
                render_linescore(ls)
            else:
                # Fallback: show R/H/E from intHomeScore etc. with a clean table
                col_names = ["", "R"]
                rows_data = [
                    [away, as_display],
                    [home, hs_display],
                ]
                # Try to get H and E from event detail
                detail = fetch_event_detail(event_id)
                hh = detail.get("intHomeHits", "")
                ah = detail.get("intAwayHits", "")
                he = detail.get("intHomeErrors", "")
                ae = detail.get("intAwayErrors", "")
                if hh or ah:
                    col_names = ["", "R", "H", "E"]
                    rows_data = [
                        [away, as_display, ah, ae],
                        [home, hs_display, hh, he],
                    ]
                header = "".join(f"<th{'  class=\"team-col\"' if i==0 else ''}>{c}</th>"
                                 for i, c in enumerate(col_names))
                body   = ""
                for row in rows_data:
                    cells = "".join(f"<td{'  class=\"team-col\"' if i==0 else ''}>{v}</td>"
                                    for i, v in enumerate(row))
                    body += f"<tr>{cells}</tr>"
                st.markdown(f"""
                <div class='section-label'>final score</div>
                <div class='linescore-wrap'>
                  <table class='linescore'>
                    <thead><tr>{header}</tr></thead>
                    <tbody>{body}</tbody>
                  </table>
                </div>""", unsafe_allow_html=True)

            # Lineup
            st.markdown("<div class='section-label' style='margin-top:12px'>lineup / players</div>",
                        unsafe_allow_html=True)
            lineup = fetch_event_lineup(event_id)
            render_lineup(lineup, home, away, league, bbpfx)


# ── SCHEDULE CARD ─────────────────────────────────────────────────────────────

def render_schedule_card(event: dict, league: str, league_info: dict):
    home  = event.get("strHomeTeam", "?")
    away  = event.get("strAwayTeam", "?")
    date  = event.get("dateEvent", "")
    time_ = (event.get("strTime") or "")[:5]
    venue = event.get("strVenue", "")
    flag  = league_info["flag"]

    # Convert UTC time to JST
    time_display = ""
    if time_:
        try:
            dt_utc = datetime.strptime(f"{date} {time_}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            dt_jst = dt_utc.astimezone(JST)
            time_display = dt_jst.strftime("%-I:%M %p JST")
        except Exception:
            time_display = time_ + " UTC"

    venue_str = f"<div class='sched-venue'>{venue}</div>" if venue else ""
    st.markdown(f"""
    <div class="sched-card">
      <div class="sched-league">{flag} {league} · {date}</div>
      <div class="sched-matchup">
        <div>
          <div class="sched-teams">
            {away}<span class="sched-at">@</span>{home}
          </div>
          {venue_str}
        </div>
        <div class="sched-time">{time_display}</div>
      </div>
    </div>""", unsafe_allow_html=True)


# ── MAIN LAYOUT ───────────────────────────────────────────────────────────────

# Masthead
st.markdown("""
<div class="masthead">
  <div class="masthead-title">NPB · KBO</div>
  <div class="masthead-sub">Scores · Schedule · Box Scores</div>
</div>""", unsafe_allow_html=True)

today     = jst_today()
yesterday = jst_yesterday()

# Refresh button
c_ref, c_time = st.columns([1, 5])
with c_ref:
    if st.button("↻ Refresh", key="refresh"):
        st.cache_data.clear()
        st.rerun()
with c_time:
    st.markdown(
        f"<span style='font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:#333;"
        f"letter-spacing:0.12em'>JST {now_jst().strftime('%b %-d %Y  %H:%M')}</span>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── SCORES TAB ───────────────────────────────────────────────────────────────
scores_tab, schedule_tab = st.tabs(["⚾  SCORES", "📅  SCHEDULE"])

with scores_tab:

    # Fetch all past events for both leagues
    all_past = []
    for lg, info in LEAGUES.items():
        for ev in fetch_past_events(info["id"]):
            ev["_league"] = lg
            ev["_info"]   = info
            all_past.append(ev)

    # Collect available dates
    dated = [(ev.get("dateEvent", ""), ev) for ev in all_past if ev.get("dateEvent")]
    available_dates = sorted(set(d for d, _ in dated), reverse=True)

    # Date selector: today, yesterday, then older
    date_labels = []
    for d in available_dates[:7]:
        if d == today:
            date_labels.append(("Today", d))
        elif d == yesterday:
            date_labels.append(("Yesterday", d))
        else:
            date_labels.append((fmt_display_date(d), d))

    if not date_labels:
        st.markdown("<div class='empty'>No recent scores available.</div>", unsafe_allow_html=True)
    else:
        tab_labels = [lbl for lbl, _ in date_labels]
        date_tabs  = st.tabs(tab_labels)

        for tab_obj, (lbl, sel_date) in zip(date_tabs, date_labels):
            with tab_obj:
                day_events = [(lg, info, ev) for lg, info, ev
                              in [(e["_league"], e["_info"], e) for e in all_past]
                              if ev.get("dateEvent") == sel_date]

                if not day_events:
                    st.markdown("<div class='empty'>No games found for this date.</div>",
                                unsafe_allow_html=True)
                    continue

                # Group by league
                for lg in ("NPB", "KBO"):
                    lg_events = [(l, i, e) for l, i, e in day_events if l == lg]
                    if not lg_events:
                        continue
                    info = LEAGUES[lg]
                    st.markdown(f"<div class='section-label'>{info['flag']} {lg}</div>",
                                unsafe_allow_html=True)
                    for _, _, ev in lg_events:
                        render_score_card(ev, lg, info)

with schedule_tab:

    all_next = []
    for lg, info in LEAGUES.items():
        for ev in fetch_next_events(info["id"]):
            ev["_league"] = lg
            ev["_info"]   = info
            all_next.append(ev)

    # Sort by date then time
    all_next.sort(key=lambda e: (e.get("dateEvent", ""), e.get("strTime", "")))

    # Group by date
    sched_dates: dict[str, list] = {}
    for ev in all_next:
        d = ev.get("dateEvent", "Unknown")
        sched_dates.setdefault(d, []).append(ev)

    if not sched_dates:
        st.markdown("<div class='empty'>No upcoming schedule data available.</div>",
                    unsafe_allow_html=True)
    else:
        for d in sorted(sched_dates.keys()):
            label = "Today" if d == today else ("Tomorrow" if d == (now_jst() + timedelta(days=1)).strftime("%Y-%m-%d") else fmt_display_date(d))
            st.markdown(f"<div class='section-label'>{label} — {d}</div>", unsafe_allow_html=True)
            for ev in sched_dates[d]:
                render_schedule_card(ev, ev["_league"], ev["_info"])
