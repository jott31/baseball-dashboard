import streamlit as st
import requests
import re
from datetime import datetime, timedelta, timezone, date as date_type
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
.team-name.neutral{ color:#999; }
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
.linescore-wrap { margin:8px 0; overflow-x:auto; }
.linescore { border-collapse:collapse; width:100%; font-family:'IBM Plex Mono',monospace; font-size:.68rem; }
.linescore th { color:#333; font-weight:400; letter-spacing:.12em; padding:3px 7px; text-align:center; border-bottom:1px solid #1a1a1a; }
.linescore td { padding:3px 7px; text-align:center; color:#777; }
.linescore td.team-col { text-align:left; color:#444; min-width:90px; }
.linescore td.total { font-weight:600; color:#bbb; border-left:1px solid #1e1e1e; }
.sched-card { background:#0d0d0d; border:1px solid #181818; border-radius:6px; padding:12px 16px; margin-bottom:6px; }
.sched-date-hdr { font-family:'IBM Plex Mono',monospace; font-size:.6rem; color:#333; letter-spacing:.2em; text-transform:uppercase; margin:14px 0 6px 0; }
.sched-matchup { display:flex; justify-content:space-between; align-items:center; }
.sched-teams { font-family:'Bebas Neue',sans-serif; font-size:1.3rem; letter-spacing:.05em; color:#bbb; }
.sched-at { color:#2a2a2a; margin:0 8px; }
.sched-time { font-family:'IBM Plex Mono',monospace; font-size:.68rem; color:#444; letter-spacing:.1em; }
.sched-venue { font-family:'IBM Plex Mono',monospace; font-size:.58rem; color:#2a2a2a; margin-top:3px; }
.no-games { font-family:'IBM Plex Mono',monospace; font-size:.75rem; color:#2a2a2a; letter-spacing:.12em; padding:28px 0; text-align:center; border:1px dashed #181818; border-radius:6px; margin:8px 0; }
.warn-box { font-family:'IBM Plex Mono',monospace; font-size:.7rem; color:#555; letter-spacing:.1em; background:#111; border:1px solid #222; border-radius:5px; padding:10px 14px; margin-bottom:12px; line-height:1.7; }
#MainMenu, footer, header { visibility:hidden; }
div[data-testid="stDecoration"] { display:none; }
div[data-baseweb="tab-list"] { gap:2px; border-bottom:1px solid #1a1a1a !important; }
div[data-baseweb="tab"] { background:transparent !important; font-family:'IBM Plex Mono',monospace !important; font-size:.7rem !important; letter-spacing:.12em !important; color:#444 !important; padding:8px 16px !important; border-bottom:2px solid transparent !important; }
div[aria-selected="true"][data-baseweb="tab"] { color:#ddd !important; border-bottom:2px solid #ddd !important; background:transparent !important; }
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

# All 12 NPB teams with their TSDB team IDs
NPB_TEAMS = {
    "Hanshin Tigers":              "135269",
    "Yomiuri Giants":              "135270",
    "Yokohama DeNA BayStars":      "135271",
    "Hiroshima Toyo Carp":         "135272",
    "Tokyo Yakult Swallows":       "135273",
    "Chunichi Dragons":            "135274",
    "Fukuoka SoftBank Hawks":      "135275",
    "Orix Buffaloes":              "135276",
    "Tohoku Rakuten Golden Eagles":"135277",
    "Chiba Lotte Marines":         "135278",
    "Saitama Seibu Lions":         "135279",
    "Hokkaido Nippon-Ham Fighters":"135280",
}

# All 10 KBO teams with their TSDB team IDs
KBO_TEAMS = {
    "Doosan Bears":   "139822",
    "Hanwha Eagles":  "139823",
    "Kia Tigers":     "139824",
    "Kiwoom Heroes":  "139825",
    "KT Wiz":         "139826",
    "LG Twins":       "139827",
    "Lotte Giants":   "139828",
    "NC Dinos":       "139829",
    "Samsung Lions":  "139830",
    "SSG Landers":    "139831",
}

NPB_LEAGUE_ID = "4591"
KBO_LEAGUE_ID = "4830"


# ── HELPERS ───────────────────────────────────────────────────────────────────
def now_jst() -> datetime:
    return datetime.now(JST)

def fmt_display_date(d: str) -> str:
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%A, %B %-d")
    except Exception:
        return d

def utc_to_jst(date_str: str, time_str: str) -> str:
    if not time_str:
        return ""
    try:
        dt = datetime.strptime(f"{date_str} {time_str[:5]}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        return dt.astimezone(JST).strftime("%-I:%M %p JST")
    except Exception:
        return time_str[:5]

def winner_cls(hs, as_):
    if hs is None or as_ is None:
        return "neutral", "neutral"
    h, a = int(hs), int(as_)
    if h > a:   return "winner", "loser"
    elif a > h: return "loser",  "winner"
    else:       return "neutral", "neutral"


# ── API ───────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_team_last(team_id: str) -> list:
    """eventslast.php — last ~5 results for a team. Free: returns home events only."""
    try:
        r = requests.get(f"{TSDB}/eventslast.php?id={team_id}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("results") or []
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_team_next(team_id: str) -> list:
    """eventsnext.php — next ~5 events for a team. Free: returns home events only."""
    try:
        r = requests.get(f"{TSDB}/eventsnext.php?id={team_id}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("events") or []
    except Exception:
        return []

@st.cache_data(ttl=600)
def fetch_season(league_id: str, season: str) -> list:
    """eventsseason.php — up to 15 events per call on free tier."""
    try:
        r = requests.get(f"{TSDB}/eventsseason.php?id={league_id}&s={season}",
                         headers=HEADERS, timeout=12)
        r.raise_for_status()
        return r.json().get("events") or []
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_event_stats(event_id: str) -> list:
    try:
        r = requests.get(f"{TSDB}/lookupeventstats.php?id={event_id}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("eventstats") or []
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_event_lineup(event_id: str) -> list:
    try:
        r = requests.get(f"{TSDB}/lookuplineup.php?id={event_id}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("lineup") or []
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_event_detail(event_id: str) -> dict:
    try:
        r = requests.get(f"{TSDB}/lookupevent.php?id={event_id}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        evs = r.json().get("events") or []
        return evs[0] if evs else {}
    except Exception:
        return {}


# ── COLLECT ALL GAMES FOR A LEAGUE ON A DATE ──────────────────────────────────
def get_games_on_date(teams: dict, date_str: str) -> list:
    """
    Fetches the last ~5 events for every team, deduplicates by idEvent,
    and returns those matching the requested date.
    This is the only approach that works reliably on the TSDB free tier —
    per-team lookups return real multi-game slates; league-level endpoints
    are capped at 1 event on the free key.
    """
    seen = set()
    games = []
    progress = st.progress(0, text="Fetching game data…")
    team_list = list(teams.items())
    for i, (name, tid) in enumerate(team_list):
        for ev in fetch_team_last(tid):
            eid = ev.get("idEvent")
            if eid and eid not in seen and ev.get("dateEvent") == date_str:
                seen.add(eid)
                games.append(ev)
        progress.progress((i + 1) / len(team_list),
                          text=f"Fetching… {name}")
    progress.empty()
    return sorted(games, key=lambda e: (e.get("strTime") or ""))


def get_upcoming_games(teams: dict) -> dict[str, list]:
    """
    Fetches next events per team, deduplicated, grouped by date.
    """
    seen = set()
    by_date: dict[str, list] = {}
    for name, tid in teams.items():
        for ev in fetch_team_next(tid):
            eid = ev.get("idEvent")
            if eid and eid not in seen:
                seen.add(eid)
                d = ev.get("dateEvent", "?")
                by_date.setdefault(d, []).append(ev)
    # Sort each day's games by time
    for d in by_date:
        by_date[d].sort(key=lambda e: e.get("strTime") or "")
    return dict(sorted(by_date.items()))


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
        side = "home" if home[:5].lower() in team.lower() else "away"
        m = re.match(r"^Inning\s+(\d+)$", stat, re.IGNORECASE)
        if m:
            innings.setdefault(side, {})[int(m.group(1))] = val
        elif stat in ("Runs", "Hits", "Errors"):
            totals.setdefault(side, {})[stat[0]] = val
    if not innings:
        return None
    max_inn = max((max(d.keys()) for d in innings.values() if d), default=0)
    return {"innings": innings, "totals": totals, "max_inn": max_inn,
            "home": home, "away": away} if max_inn else None

def render_linescore(ls: dict):
    inn_nums = list(range(1, ls["max_inn"] + 1))
    hdr = "<th class='team-col'></th>" + "".join(f"<th>{i}</th>" for i in inn_nums) + \
          "<th class='total'>R</th><th class='total'>H</th><th class='total'>E</th>"
    rows = ""
    for side in ("away", "home"):
        name = ls[side][:14]
        inn  = ls["innings"].get(side, {})
        tot  = ls["totals"].get(side, {})
        cells = f"<td class='team-col'>{name}</td>"
        cells += "".join(f"<td>{inn.get(i, '–')}</td>" for i in inn_nums)
        cells += f"<td class='total'>{tot.get('R','')}</td><td class='total'>{tot.get('H','')}</td><td class='total'>{tot.get('E','')}</td>"
        rows += f"<tr>{cells}</tr>"
    st.markdown(f"<div class='linescore-wrap'><table class='linescore'><thead><tr>{hdr}</tr></thead><tbody>{rows}</tbody></table></div>",
                unsafe_allow_html=True)


# ── LINEUP ────────────────────────────────────────────────────────────────────
def render_lineup(lineup: list, home: str, away: str, league: str):
    if not lineup:
        st.markdown("<div style='font-family:IBM Plex Mono,monospace;font-size:.65rem;color:#2e2e2e;padding:6px 0'>No lineup data available from TheSportsDB.</div>",
                    unsafe_allow_html=True)
        return
    away_p, home_p = [], []
    for p in lineup:
        team = p.get("strTeam", "")
        (home_p if home[:5].lower() in team.lower() else away_p).append(p)
    if not away_p and not home_p:
        mid = len(lineup) // 2
        away_p, home_p = lineup[:mid], lineup[mid:]

    def row(p):
        name  = p.get("strPlayer") or p.get("strName") or "Unknown"
        pos   = p.get("strPosition", "")
        num   = p.get("strNumber", "")
        bbref = f"https://www.baseball-reference.com/search/search.fcgi?search={name.replace(' ', '+')}"
        pek   = ' <a class="ext-link" href="https://proeyekyuu.com/player-registry/" target="_blank">ProEyeKyuu</a>' if league == "NPB" else ""
        num_s = f"<span style='color:#2a2a2a;font-size:.6rem;margin-right:4px'>#{num}</span>" if num else ""
        pos_s = f"<span style='color:#2a2a2a;font-size:.6rem;margin-left:4px'>{pos}</span>" if pos else ""
        return (f"<div style='padding:5px 0;border-bottom:1px solid #141414;font-size:.82rem'>"
                f"{num_s}<span style='color:#ccc'>{name}</span>{pos_s} "
                f"<a class='ext-link' href='{bbref}' target='_blank'>BBRef</a>{pek}</div>")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='section-label'>{away[:20]}</div>", unsafe_allow_html=True)
        st.markdown("".join(row(p) for p in away_p) or "<div style='color:#2a2a2a;font-size:.7rem'>—</div>",
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='section-label'>{home[:20]}</div>", unsafe_allow_html=True)
        st.markdown("".join(row(p) for p in home_p) or "<div style='color:#2a2a2a;font-size:.7rem'>—</div>",
                    unsafe_allow_html=True)


# ── SCORE CARD ────────────────────────────────────────────────────────────────
def render_score_card(ev: dict, league: str):
    home     = ev.get("strHomeTeam", "?")
    away     = ev.get("strAwayTeam", "?")
    hs       = ev.get("intHomeScore")
    as_      = ev.get("intAwayScore")
    date_str = ev.get("dateEvent", "")
    venue    = ev.get("strVenue", "")
    eid      = ev.get("idEvent", "")
    final    = hs is not None and as_ is not None

    hc, ac = winner_cls(hs, as_)
    hs_d = str(hs) if final else "–"
    as_d = str(as_) if final else "–"

    venue_str = venue or ""
    year      = date_str[:4] if date_str else "2026"
    bbref_url = f"https://www.baseball-reference.com/search/search.fcgi?search={away.replace(' ','+')}+{home.replace(' ','+')}"

    if league == "NPB":
        links = (f'<a class="ext-link" href="https://proeyekyuu.com/game/" target="_blank">ProEyeKyuu</a>'
                 f'<a class="ext-link" href="https://npb.jp/bis/eng/{year}/games/" target="_blank">NPB.jp</a>'
                 f'<a class="ext-link" href="{bbref_url}" target="_blank">BBRef</a>')
    else:
        links = (f'<a class="ext-link" href="https://eng.koreabaseball.com/Schedule/GameCenter/Main.aspx" target="_blank">KBO Official</a>'
                 f'<a class="ext-link" href="{bbref_url}" target="_blank">BBRef</a>')

    st.markdown(f"""
    <div class="card">
      <div class="card-venue">{venue_str}</div>
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
        <div class="card-meta">{'FINAL' if final else 'SCHEDULED'}</div>
        <div class="card-links">{links}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    if final and eid:
        with st.expander(f"Box score — {away} @ {home}"):
            stats = fetch_event_stats(eid)
            ls    = parse_linescore(stats, home, away)
            st.markdown("<div class='section-label'>linescore</div>", unsafe_allow_html=True)
            if ls:
                render_linescore(ls)
            else:
                detail = fetch_event_detail(eid)
                hh = detail.get("intHomeHits",""); ah = detail.get("intAwayHits","")
                he = detail.get("intHomeErrors",""); ae = detail.get("intAwayErrors","")
                cols = ["","R","H","E"] if (hh or ah) else ["","R"]
                rows_data = [[away, as_d, ah, ae],[home, hs_d, hh, he]] if (hh or ah) else [[away, as_d],[home, hs_d]]
                hdr = "".join(f"<th{'  class=\"team-col\"' if i==0 else ''}>{c}</th>" for i,c in enumerate(cols))
                bdy = "".join("<tr>"+"".join(f"<td{'  class=\"team-col\"' if i==0 else ''}>{v}</td>" for i,v in enumerate(r))+"</tr>" for r in rows_data)
                st.markdown(f"<div class='linescore-wrap'><table class='linescore'><thead><tr>{hdr}</tr></thead><tbody>{bdy}</tbody></table></div>",
                            unsafe_allow_html=True)
            st.markdown("<div class='section-label' style='margin-top:12px'>lineup / players</div>", unsafe_allow_html=True)
            render_lineup(fetch_event_lineup(eid), home, away, league)


# ── SCHEDULE CARD ─────────────────────────────────────────────────────────────
def render_sched_card(ev: dict):
    home  = ev.get("strHomeTeam", "?")
    away  = ev.get("strAwayTeam", "?")
    date  = ev.get("dateEvent", "")
    time_ = ev.get("strTime", "")
    venue = ev.get("strVenue", "")
    time_disp = utc_to_jst(date, time_)
    venue_str = f"<div class='sched-venue'>{venue}</div>" if venue else ""
    st.markdown(f"""
    <div class="sched-card">
      <div class="sched-matchup">
        <div>
          <div class="sched-teams">{away}<span class="sched-at">@</span>{home}</div>
          {venue_str}
        </div>
        <div class="sched-time">{time_disp}</div>
      </div>
    </div>""", unsafe_allow_html=True)


# ── SCORES PAGE ───────────────────────────────────────────────────────────────
def scores_page(teams: dict, league: str, date_str: str):
    games = get_games_on_date(teams, date_str)
    if not games:
        st.markdown(
            f"<div class='no-games'>No {league} games found for {fmt_display_date(date_str)}<br>"
            f"<span style='font-size:.6rem'>Try yesterday or another date — TSDB data can lag by ~24 hours</span></div>",
            unsafe_allow_html=True)
        return
    for ev in games:
        render_score_card(ev, league)


# ── SCHEDULE PAGE ─────────────────────────────────────────────────────────────
def schedule_page(teams: dict, league: str):
    jst_now = now_jst()
    today_s = jst_now.strftime("%Y-%m-%d")
    tmrw_s  = (jst_now + timedelta(days=1)).strftime("%Y-%m-%d")

    by_date = get_upcoming_games(teams)
    # Filter to only future dates
    by_date = {d: v for d, v in by_date.items() if d >= today_s}

    if not by_date:
        st.markdown(f"<div class='no-games'>No upcoming {league} schedule data available</div>",
                    unsafe_allow_html=True)
        return

    for d in sorted(by_date.keys()):
        if d == today_s:
            label = f"Today — {fmt_display_date(d)}"
        elif d == tmrw_s:
            label = f"Tomorrow — {fmt_display_date(d)}"
        else:
            label = fmt_display_date(d)
        st.markdown(f"<div class='sched-date-hdr'>{label}</div>", unsafe_allow_html=True)
        for ev in by_date[d]:
            render_sched_card(ev)


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="masthead">
  <div class="masthead-title">NPB · KBO</div>
  <div class="masthead-sub">Scores · Schedule · Box Scores</div>
</div>""", unsafe_allow_html=True)

jst_now = now_jst()

# Controls row
c1, c2, c3 = st.columns([3, 1, 1])
with c1:
    selected_date = st.date_input(
        "Date (JST)",
        value=(jst_now - timedelta(days=1)).date(),
        max_value=jst_now.date(),
        min_value=date_type(2020, 1, 1),
        label_visibility="collapsed",
        format="YYYY-MM-DD",
    )
    selected_str = selected_date.strftime("%Y-%m-%d")
with c2:
    st.markdown(f"<div style='font-family:IBM Plex Mono,monospace;font-size:.62rem;color:#333;padding-top:10px'>JST {jst_now.strftime('%H:%M')}</div>",
                unsafe_allow_html=True)
with c3:
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Date label
today_s     = jst_now.strftime("%Y-%m-%d")
yesterday_s = (jst_now - timedelta(days=1)).strftime("%Y-%m-%d")
if selected_str == today_s:
    dlabel = f"Today · {fmt_display_date(selected_str)}"
elif selected_str == yesterday_s:
    dlabel = f"Yesterday · {fmt_display_date(selected_str)}"
else:
    dlabel = fmt_display_date(selected_str)
st.markdown(f"<div class='section-label' style='margin-bottom:.8rem'>{dlabel}</div>", unsafe_allow_html=True)

# Note about data source
st.markdown("""
<div class='warn-box'>
  ⚠ Data via TheSportsDB free API — fetches last 5 results per team to build each day's slate.
  Results may lag 12–24 hours. Box scores and lineups are best-effort (coverage varies by game).
</div>""", unsafe_allow_html=True)

# Tabs
t_npb, t_kbo, t_npb_s, t_kbo_s = st.tabs([
    "🇯🇵  NPB Scores", "🇰🇷  KBO Scores",
    "🇯🇵  NPB Schedule", "🇰🇷  KBO Schedule",
])

with t_npb:
    scores_page(NPB_TEAMS, "NPB", selected_str)

with t_kbo:
    scores_page(KBO_TEAMS, "KBO", selected_str)

with t_npb_s:
    schedule_page(NPB_TEAMS, "NPB")

with t_kbo_s:
    schedule_page(KBO_TEAMS, "KBO")

st.markdown("---")
st.markdown("<span style='font-family:IBM Plex Mono,monospace;font-size:.58rem;color:#222;letter-spacing:.1em'>"
            "Data: TheSportsDB · All times JST (UTC+9) · Score cache 5min · Schedule cache 10min</span>",
            unsafe_allow_html=True)
