import streamlit as st
import requests
import re
from datetime import datetime, timedelta, timezone, date as date_type
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
.block-container { padding-top: 1.5rem !important; max-width: 1100px; }

.masthead {
    display: flex; align-items: baseline; gap: 14px;
    border-bottom: 2px solid #1e1e1e; padding-bottom: 0.8rem; margin-bottom: 1.2rem;
}
.masthead-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.6rem; letter-spacing: 0.08em; color: #fff; line-height: 1;
}
.masthead-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem; color: #444; letter-spacing: 0.2em; text-transform: uppercase;
}

.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem; letter-spacing: 0.24em; color: #444;
    text-transform: uppercase; margin-bottom: 0.6rem; margin-top: 0.4rem;
}

/* ── SCORE CARD ── */
.card {
    background: #111; border: 1px solid #1e1e1e; border-radius: 6px;
    padding: 14px 18px; margin-bottom: 8px;
}
.card-league-row {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.58rem; letter-spacing: 0.2em; color: #3a3a3a;
    text-transform: uppercase; margin-bottom: 10px;
}
.card-teams {
    display: flex; justify-content: space-between;
    align-items: center; gap: 12px;
}
.team-block { flex: 1; }
.team-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem; letter-spacing: 0.04em; line-height: 1;
}
.team-name.winner { color: #f0f0f0; }
.team-name.loser  { color: #3a3a3a; }
.team-name.neutral { color: #999; }
.score-mid {
    display: flex; gap: 14px; align-items: center;
    font-family: 'IBM Plex Mono', monospace;
}
.score {
    font-size: 2.1rem; font-weight: 600; min-width: 1.8ch; text-align: center;
}
.score.winner { color: #f0f0f0; }
.score.loser  { color: #2e2e2e; }
.score.neutral { color: #888; }
.score-sep { color: #252525; font-size: 1.1rem; }
.card-footer {
    display: flex; justify-content: space-between; align-items: center;
    margin-top: 10px; padding-top: 8px; border-top: 1px solid #181818;
}
.card-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem; color: #333; letter-spacing: 0.1em;
}
.card-links { display: flex; gap: 10px; flex-wrap: wrap; }
.ext-link {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.6rem;
    letter-spacing: 0.08em; color: #444; text-decoration: none;
    border-bottom: 1px solid #222; transition: color 0.12s, border-color 0.12s;
    white-space: nowrap;
}
.ext-link:hover { color: #bbb; border-color: #555; }

/* ── LINESCORE ── */
.linescore-wrap { margin: 8px 0; overflow-x: auto; }
.linescore {
    border-collapse: collapse; width: 100%;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
}
.linescore th {
    color: #333; font-weight: 400; letter-spacing: 0.12em;
    padding: 3px 7px; text-align: center; border-bottom: 1px solid #1a1a1a;
}
.linescore td { padding: 3px 7px; text-align: center; color: #777; }
.linescore td.team-col { text-align: left; color: #444; min-width: 90px; }
.linescore td.total { font-weight: 600; color: #bbb; border-left: 1px solid #1e1e1e; }

/* ── SCHEDULE ── */
.sched-card {
    background: #0d0d0d; border: 1px solid #181818;
    border-radius: 6px; padding: 12px 16px; margin-bottom: 6px;
}
.sched-date-group {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem; color: #333; letter-spacing: 0.2em;
    text-transform: uppercase; margin: 14px 0 6px 0;
}
.sched-matchup {
    display: flex; justify-content: space-between; align-items: center;
}
.sched-teams {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.3rem; letter-spacing: 0.05em; color: #bbb;
}
.sched-at { color: #2a2a2a; margin: 0 8px; }
.sched-time {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem; color: #444; letter-spacing: 0.1em;
}
.sched-venue {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.58rem; color: #2a2a2a; margin-top: 3px;
}

.empty {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem;
    color: #2a2a2a; letter-spacing: 0.14em; padding: 30px 0; text-align: center;
}
.no-games {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
    color: #333; letter-spacing: 0.1em; padding: 24px 0; text-align: center;
    border: 1px dashed #1a1a1a; border-radius: 6px; margin: 8px 0;
}

/* Date pill */
.date-display {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem;
    color: #666; letter-spacing: 0.12em;
}

#MainMenu, footer, header { visibility: hidden; }
div[data-testid="stDecoration"] { display: none; }

/* Streamlit tab styling */
div[data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #1a1a1a !important; }
div[data-baseweb="tab"] {
    background: transparent !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important; letter-spacing: 0.12em !important;
    color: #444 !important; padding: 8px 16px !important;
    border-bottom: 2px solid transparent !important;
}
div[aria-selected="true"][data-baseweb="tab"] {
    color: #ddd !important; border-bottom: 2px solid #ddd !important;
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
TSDB    = "https://www.thesportsdb.com/api/v1/json/123"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

JST = ZoneInfo("Asia/Tokyo")

# TSDB league name strings (from strLeague field in API response)
NPB_LEAGUE_NAME = "Nippon Professional Baseball"
KBO_LEAGUE_NAME = "KBO League"
NPB_LEAGUE_ID   = "4591"
KBO_LEAGUE_ID   = "4830"


# ── TIME HELPERS ──────────────────────────────────────────────────────────────

def now_jst() -> datetime:
    return datetime.now(JST)

def jst_date_str(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")

def fmt_display_date(d: str) -> str:
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%A, %B %-d")
    except Exception:
        return d

def utc_time_to_jst(date_str: str, time_str: str) -> str:
    """Convert TSDB UTC time to JST display string."""
    if not time_str:
        return ""
    try:
        t = time_str[:5]
        dt_utc = datetime.strptime(f"{date_str} {t}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        return dt_utc.astimezone(JST).strftime("%-I:%M %p JST")
    except Exception:
        return time_str[:5] + " UTC"


# ── API CALLS ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=180)
def fetch_games_on_date(date_str: str) -> list:
    """
    Fetch ALL baseball events on a given date using eventsday.php.
    Returns the full list; caller filters by strLeague.
    """
    url = f"{TSDB}/eventsday.php?d={date_str}&s=Baseball"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        return r.json().get("events") or []
    except Exception:
        return []

@st.cache_data(ttl=180)
def fetch_next_events(league_id: str) -> list:
    """Upcoming games for a league (~15 events)."""
    try:
        r = requests.get(f"{TSDB}/eventsnextleague.php?id={league_id}",
                         headers=HEADERS, timeout=12)
        r.raise_for_status()
        return r.json().get("events") or []
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_event_stats(event_id: str) -> list:
    try:
        r = requests.get(f"{TSDB}/lookupeventstats.php?id={event_id}",
                         headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("eventstats") or []
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_event_lineup(event_id: str) -> list:
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


# ── LINESCORE ─────────────────────────────────────────────────────────────────

def parse_linescore(stats: list, home: str, away: str) -> dict | None:
    if not stats:
        return None
    innings: dict = {}
    totals: dict  = {}
    for s in stats:
        team = s.get("strTeam", "")
        stat = s.get("strStat", "")
        val  = s.get("intValue", "")
        # Map to home/away by partial name match
        side = "home" if home[:5].lower() in team.lower() else "away"
        m = re.match(r"^Inning\s+(\d+)$", stat, re.IGNORECASE)
        if m:
            innings.setdefault(side, {})[int(m.group(1))] = val
        elif stat in ("Runs", "Hits", "Errors"):
            totals.setdefault(side, {})[stat[0]] = val
    if not innings:
        return None
    max_inn = max((max(d.keys()) for d in innings.values() if d), default=0)
    if max_inn == 0:
        return None
    return {"innings": innings, "totals": totals, "max_inn": max_inn,
            "home": home, "away": away}

def render_linescore(ls: dict):
    max_inn   = ls["max_inn"]
    inn_nums  = list(range(1, max_inn + 1))
    header    = "<th class='team-col'></th>" + \
                "".join(f"<th>{i}</th>" for i in inn_nums) + \
                "<th class='total'>R</th><th class='total'>H</th><th class='total'>E</th>"
    rows = ""
    for side in ("away", "home"):
        name     = ls[side][:14]
        inn_data = ls["innings"].get(side, {})
        tot_data = ls["totals"].get(side, {})
        cells    = f"<td class='team-col'>{name}</td>"
        for i in inn_nums:
            v = inn_data.get(i, "")
            cells += f"<td>{v if v != '' else '–'}</td>"
        cells += f"<td class='total'>{tot_data.get('R', '')}</td>"
        cells += f"<td class='total'>{tot_data.get('H', '')}</td>"
        cells += f"<td class='total'>{tot_data.get('E', '')}</td>"
        rows += f"<tr>{cells}</tr>"
    st.markdown(
        f"<div class='linescore-wrap'><table class='linescore'>"
        f"<thead><tr>{header}</tr></thead><tbody>{rows}</tbody>"
        f"</table></div>",
        unsafe_allow_html=True,
    )


# ── LINEUP DISPLAY ─────────────────────────────────────────────────────────────

def render_lineup(lineup: list, home: str, away: str, league: str):
    if not lineup:
        st.markdown(
            "<div style='font-family:IBM Plex Mono,monospace;font-size:0.65rem;"
            "color:#2e2e2e;padding:8px 0'>No lineup data from TheSportsDB for this game.</div>",
            unsafe_allow_html=True,
        )
        return

    away_p, home_p = [], []
    for p in lineup:
        team = p.get("strTeam", "")
        if home[:5].lower() in team.lower():
            home_p.append(p)
        else:
            away_p.append(p)
    if not away_p and not home_p:
        mid = len(lineup) // 2
        away_p, home_p = lineup[:mid], lineup[mid:]

    def player_html(p: dict) -> str:
        name = p.get("strPlayer") or p.get("strName") or "Unknown"
        pos  = p.get("strPosition", "")
        num  = p.get("strNumber", "")
        bbref = f"https://www.baseball-reference.com/search/search.fcgi?search={name.replace(' ', '+')}"
        pek   = ' <a class="ext-link" href="https://proeyekyuu.com/player-registry/" target="_blank">ProEyeKyuu</a>' \
                if league == "NPB" else ""
        num_s = f"<span style='color:#2e2e2e;font-size:0.6rem;margin-right:4px'>#{num}</span>" if num else ""
        pos_s = f"<span style='color:#2e2e2e;font-size:0.6rem;margin-left:4px'>{pos}</span>" if pos else ""
        return (
            f"<div style='padding:5px 0;border-bottom:1px solid #141414;"
            f"font-size:0.82rem'>"
            f"{num_s}<span style='color:#ccc'>{name}</span>{pos_s} "
            f"<a class='ext-link' href='{bbref}' target='_blank'>BBRef</a>{pek}</div>"
        )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='section-label'>{away[:20]} lineup</div>", unsafe_allow_html=True)
        st.markdown("".join(player_html(p) for p in away_p) if away_p
                    else "<div style='color:#2e2e2e;font-size:0.7rem'>—</div>",
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='section-label'>{home[:20]} lineup</div>", unsafe_allow_html=True)
        st.markdown("".join(player_html(p) for p in home_p) if home_p
                    else "<div style='color:#2e2e2e;font-size:0.7rem'>—</div>",
                    unsafe_allow_html=True)


# ── SCORE CARD ────────────────────────────────────────────────────────────────

def render_score_card(event: dict, league: str):
    home     = event.get("strHomeTeam", "?")
    away     = event.get("strAwayTeam", "?")
    hs_raw   = event.get("intHomeScore")
    as_raw   = event.get("intAwayScore")
    date_str = event.get("dateEvent", "")
    venue    = event.get("strVenue", "")
    event_id = event.get("idEvent", "")

    final = hs_raw is not None and as_raw is not None

    # Winner/loser styling
    if final:
        hs, as_ = int(hs_raw), int(as_raw)
        if hs > as_:
            h_cls, a_cls = "winner", "loser"
        elif as_ > hs:
            h_cls, a_cls = "loser", "winner"
        else:
            h_cls = a_cls = "neutral"
        hs_disp, as_disp = str(hs_raw), str(as_raw)
    else:
        h_cls = a_cls = "neutral"
        hs_disp = as_disp = "–"

    # External links
    venue_str = f" · {venue}" if venue else ""
    away_q    = away.replace(" ", "+")
    home_q    = home.replace(" ", "+")
    bbref_url = f"https://www.baseball-reference.com/search/search.fcgi?search={away_q}+{home_q}"
    year      = date_str[:4] if date_str else "2026"

    if league == "NPB":
        links_html = (
            f'<a class="ext-link" href="https://proeyekyuu.com/game/" target="_blank">ProEyeKyuu</a>'
            f'<a class="ext-link" href="https://npb.jp/bis/eng/{year}/games/" target="_blank">NPB.jp</a>'
            f'<a class="ext-link" href="{bbref_url}" target="_blank">BBRef</a>'
        )
    else:
        links_html = (
            f'<a class="ext-link" href="https://eng.koreabaseball.com/Schedule/GameCenter/Main.aspx" target="_blank">KBO</a>'
            f'<a class="ext-link" href="{bbref_url}" target="_blank">BBRef</a>'
        )

    st.markdown(f"""
    <div class="card">
      <div class="card-league-row">{venue_str.strip(" · ")}</div>
      <div class="card-teams">
        <div class="team-block">
          <div class="team-name {a_cls}">{away}</div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#2e2e2e;margin-top:2px">AWAY</div>
        </div>
        <div class="score-mid">
          <span class="score {a_cls}">{as_disp}</span>
          <span class="score-sep">·</span>
          <span class="score {h_cls}">{hs_disp}</span>
        </div>
        <div class="team-block" style="text-align:right">
          <div class="team-name {h_cls}" style="text-align:right">{home}</div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#2e2e2e;margin-top:2px;text-align:right">HOME</div>
        </div>
      </div>
      <div class="card-footer">
        <div class="card-meta">{'FINAL' if final else 'SCHEDULED'}</div>
        <div class="card-links">{links_html}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Expandable box score (only for completed games)
    if final and event_id:
        with st.expander(f"Box score — {away} @ {home}"):
            # 1. Linescore from event stats
            stats = fetch_event_stats(event_id)
            ls    = parse_linescore(stats, home, away)
            st.markdown("<div class='section-label'>linescore</div>", unsafe_allow_html=True)
            if ls:
                render_linescore(ls)
            else:
                # Fallback: R/H/E from event detail
                detail = fetch_event_detail(event_id)
                hh = detail.get("intHomeHits",   "")
                ah = detail.get("intAwayHits",   "")
                he = detail.get("intHomeErrors", "")
                ae = detail.get("intAwayErrors", "")
                cols = ["", "R", "H", "E"] if (hh or ah) else ["", "R"]
                rows_data = (
                    [[away, as_disp, ah, ae], [home, hs_disp, hh, he]]
                    if (hh or ah) else
                    [[away, as_disp], [home, hs_disp]]
                )
                hdr = "".join(
                    f"<th{'  class=\"team-col\"' if i == 0 else ''}>{c}</th>"
                    for i, c in enumerate(cols)
                )
                bdy = "".join(
                    "<tr>" + "".join(
                        f"<td{'  class=\"team-col\"' if i == 0 else ''}>{v}</td>"
                        for i, v in enumerate(row)
                    ) + "</tr>"
                    for row in rows_data
                )
                st.markdown(
                    f"<div class='linescore-wrap'><table class='linescore'>"
                    f"<thead><tr>{hdr}</tr></thead><tbody>{bdy}</tbody>"
                    f"</table></div>",
                    unsafe_allow_html=True,
                )

            # 2. Lineup / players
            st.markdown("<div class='section-label' style='margin-top:12px'>lineup / players</div>",
                        unsafe_allow_html=True)
            lineup = fetch_event_lineup(event_id)
            render_lineup(lineup, home, away, league)


# ── SCHEDULE CARD ─────────────────────────────────────────────────────────────

def render_schedule_card(event: dict):
    home  = event.get("strHomeTeam", "?")
    away  = event.get("strAwayTeam", "?")
    date  = event.get("dateEvent", "")
    time_ = event.get("strTime", "")
    venue = event.get("strVenue", "")
    time_disp = utc_time_to_jst(date, time_)
    venue_str = f"<div class='sched-venue'>{venue}</div>" if venue else ""
    st.markdown(f"""
    <div class="sched-card">
      <div class="sched-matchup">
        <div>
          <div class="sched-teams">
            {away}<span class="sched-at">@</span>{home}
          </div>
          {venue_str}
        </div>
        <div class="sched-time">{time_disp}</div>
      </div>
    </div>""", unsafe_allow_html=True)


# ── LEAGUE SCORES PAGE ────────────────────────────────────────────────────────

def scores_page(league_name_filter: str, league_label: str, date_str: str):
    """Render all completed/live games for one league on a given date."""
    all_events = fetch_games_on_date(date_str)
    league_events = [
        e for e in all_events
        if league_name_filter.lower() in (e.get("strLeague") or "").lower()
    ]

    if not league_events:
        st.markdown(
            f"<div class='no-games'>No {league_label} games found for {fmt_display_date(date_str)}</div>",
            unsafe_allow_html=True,
        )
        return

    # Split into final vs upcoming (same day but not yet played)
    final_games = [e for e in league_events if e.get("intHomeScore") is not None]
    upcoming    = [e for e in league_events if e.get("intHomeScore") is None]

    if final_games:
        for ev in final_games:
            render_score_card(ev, league_label)

    if upcoming:
        st.markdown("<div class='section-label' style='margin-top:12px'>today — scheduled</div>",
                    unsafe_allow_html=True)
        for ev in upcoming:
            render_score_card(ev, league_label)

    if not final_games and not upcoming:
        st.markdown(
            f"<div class='no-games'>No games data available</div>",
            unsafe_allow_html=True,
        )


# ── SCHEDULE PAGE ─────────────────────────────────────────────────────────────

def schedule_page(league_id: str, league_name_filter: str, league_label: str):
    events = fetch_next_events(league_id)
    events = [e for e in events
              if league_name_filter.lower() in (e.get("strLeague") or "").lower()]
    events.sort(key=lambda e: (e.get("dateEvent", ""), e.get("strTime", "")))

    if not events:
        st.markdown(
            f"<div class='no-games'>No upcoming {league_label} schedule available</div>",
            unsafe_allow_html=True,
        )
        return

    # Group by date
    by_date: dict[str, list] = {}
    for e in events:
        by_date.setdefault(e.get("dateEvent", "?"), []).append(e)

    today_str    = jst_date_str(now_jst())
    tomorrow_str = jst_date_str(now_jst() + timedelta(days=1))

    for d in sorted(by_date.keys()):
        if d == today_str:
            label = f"Today — {fmt_display_date(d)}"
        elif d == tomorrow_str:
            label = f"Tomorrow — {fmt_display_date(d)}"
        else:
            label = fmt_display_date(d)
        st.markdown(f"<div class='sched-date-group'>{label}</div>", unsafe_allow_html=True)
        for ev in by_date[d]:
            render_schedule_card(ev)


# ════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════════════════════════

# Masthead
st.markdown("""
<div class="masthead">
  <div class="masthead-title">NPB · KBO</div>
  <div class="masthead-sub">Scores · Schedule · Box Scores</div>
</div>""", unsafe_allow_html=True)

# ── TOP CONTROLS ──────────────────────────────────────────────────────────────
ctrl_left, ctrl_mid, ctrl_right = st.columns([3, 1, 1])

with ctrl_left:
    # Calendar date picker — defaults to yesterday JST
    # (yesterday is most likely to have complete results)
    jst_now       = now_jst()
    default_date  = (jst_now - timedelta(days=1)).date()
    selected_date = st.date_input(
        "Date (JST)",
        value=default_date,
        max_value=jst_now.date(),
        min_value=date_type(2020, 1, 1),
        label_visibility="collapsed",
        format="YYYY-MM-DD",
    )
    selected_str  = selected_date.strftime("%Y-%m-%d")

with ctrl_right:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with ctrl_mid:
    st.markdown(
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.62rem;"
        f"color:#333;letter-spacing:0.1em;padding-top:10px'>"
        f"JST {jst_now.strftime('%H:%M')}</div>",
        unsafe_allow_html=True,
    )

# Date label
today_str     = jst_date_str(jst_now)
yesterday_str = jst_date_str(jst_now - timedelta(days=1))
if selected_str == today_str:
    date_label = f"Today · {fmt_display_date(selected_str)}"
elif selected_str == yesterday_str:
    date_label = f"Yesterday · {fmt_display_date(selected_str)}"
else:
    date_label = fmt_display_date(selected_str)

st.markdown(
    f"<div class='section-label' style='margin-bottom:1rem'>{date_label}</div>",
    unsafe_allow_html=True,
)

# ── LEAGUE TABS ───────────────────────────────────────────────────────────────
npb_scores_tab, kbo_scores_tab, npb_sched_tab, kbo_sched_tab = st.tabs([
    "🇯🇵  NPB Scores",
    "🇰🇷  KBO Scores",
    "🇯🇵  NPB Schedule",
    "🇰🇷  KBO Schedule",
])

with npb_scores_tab:
    scores_page(NPB_LEAGUE_NAME, "NPB", selected_str)

with kbo_scores_tab:
    scores_page(KBO_LEAGUE_NAME, "KBO", selected_str)

with npb_sched_tab:
    schedule_page(NPB_LEAGUE_ID, NPB_LEAGUE_NAME, "NPB")

with kbo_sched_tab:
    schedule_page(KBO_LEAGUE_ID, KBO_LEAGUE_NAME, "KBO")

# Footer
st.markdown("---")
st.markdown(
    "<span style='font-family:IBM Plex Mono,monospace;font-size:0.58rem;color:#2a2a2a;"
    "letter-spacing:0.12em'>Scores: TheSportsDB · Box scores: TheSportsDB · "
    "All times JST (UTC+9) · Cache 3min</span>",
    unsafe_allow_html=True,
)
