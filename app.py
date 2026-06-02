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

CURRENT_YEAR = str(datetime.now(JST).year)

NPB_TEAMS = {
    "Hanshin Tigers":               "135269",
    "Yomiuri Giants":               "135270",
    "Yokohama DeNA BayStars":       "135271",
    "Hiroshima Toyo Carp":          "135272",
    "Tokyo Yakult Swallows":        "135273",
    "Chunichi Dragons":             "135274",
    "Fukuoka SoftBank Hawks":       "135275",
    "Orix Buffaloes":               "135276",
    "Tohoku Rakuten Golden Eagles": "135277",
    "Chiba Lotte Marines":          "135278",
    "Saitama Seibu Lions":          "135279",
    "Hokkaido Nippon-Ham Fighters": "135280",
}

KBO_TEAMS = {
    "Doosan Bears":  "139822",
    "Hanwha Eagles": "139823",
    "Kia Tigers":    "139824",
    "Kiwoom Heroes": "139825",
    "KT Wiz":        "139826",
    "LG Twins":      "139827",
    "Lotte Giants":  "139828",
    "NC Dinos":      "139829",
    "Samsung Lions": "139830",
    "SSG Landers":   "139831",
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
    try:
        h, a = int(hs), int(as_)
    except (TypeError, ValueError):
        return "neutral", "neutral"
    if h > a:   return "winner", "loser"
    elif a > h: return "loser",  "winner"
    else:       return "neutral", "neutral"


# ── API ───────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_team_last(team_id: str) -> list:
    try:
        r = requests.get(f"{TSDB}/eventslast.php?id={team_id}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("results") or []
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_team_next(team_id: str) -> list:
    try:
        r = requests.get(f"{TSDB}/eventsnext.php?id={team_id}", headers=HEADERS, timeout=10)
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
def fetch_event_detail(event_id: str) -> dict:
    try:
        r = requests.get(f"{TSDB}/lookupevent.php?id={event_id}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        evs = r.json().get("events") or []
        return evs[0] if evs else {}
    except Exception:
        return {}

@st.cache_data(ttl=300)
def fetch_event_lineup(event_id: str) -> list:
    try:
        r = requests.get(f"{TSDB}/lookuplineup.php?id={event_id}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("lineup") or []
    except Exception:
        return []


# ── COLLECT GAMES FOR A DATE ──────────────────────────────────────────────────
def get_games_on_date(teams: dict, league_id: str, date_str: str) -> list:
    """
    Per-team eventslast.php — reliable on the TSDB free tier.
    Deduplicates by event ID and filters to the requested date.
    """
    seen: set = set()
    games: list = []
    progress = st.progress(0, text="Fetching game data…")
    team_list = list(teams.items())
    for i, (name, tid) in enumerate(team_list):
        for ev in fetch_team_last(tid):
            eid = ev.get("idEvent")
            if eid and eid not in seen and ev.get("dateEvent") == date_str:
                seen.add(eid)
                games.append(ev)
        progress.progress((i + 1) / len(team_list), text=f"Fetching… {name}")
    progress.empty()
    return sorted(games, key=lambda e: (e.get("strTime") or ""))


def get_upcoming_games(teams: dict) -> dict[str, list]:
    seen: set = set()
    by_date: dict[str, list] = {}
    for name, tid in teams.items():
        for ev in fetch_team_next(tid):
            eid = ev.get("idEvent")
            if eid and eid not in seen:
                seen.add(eid)
                d = ev.get("dateEvent", "?")
                by_date.setdefault(d, []).append(ev)
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
        name  = ls[side][:14]
        inn   = ls["innings"].get(side, {})
        tot   = ls["totals"].get(side, {})
        cells = f"<td class='team-col'>{name}</td>"
        cells += "".join(f"<td>{inn.get(i, '–')}</td>" for i in inn_nums)
        cells += (f"<td class='total'>{tot.get('R','–')}</td>"
                  f"<td class='total'>{tot.get('H','–')}</td>"
                  f"<td class='total'>{tot.get('E','–')}</td>")
        rows += f"<tr>{cells}</tr>"
    st.markdown(f"<div class='linescore-wrap'><table class='linescore'>"
                f"<thead><tr>{hdr}</tr></thead><tbody>{rows}</tbody></table></div>",
                unsafe_allow_html=True)


def render_simple_score_table(away: str, home: str, as_d: str, hs_d: str,
                               ah: str, hh: str, ae: str, he: str):
    show_rhe = any([ah, hh, ae, he])
    if show_rhe:
        hdr = "<th class='team-col'></th><th class='total'>R</th><th class='total'>H</th><th class='total'>E</th>"
        rows = (f"<tr><td class='team-col'>{away[:14]}</td>"
                f"<td class='total'>{as_d}</td><td class='total'>{ah or '–'}</td><td class='total'>{ae or '–'}</td></tr>"
                f"<tr><td class='team-col'>{home[:14]}</td>"
                f"<td class='total'>{hs_d}</td><td class='total'>{hh or '–'}</td><td class='total'>{he or '–'}</td></tr>")
    else:
        hdr  = "<th class='team-col'></th><th class='total'>R</th>"
        rows = (f"<tr><td class='team-col'>{away[:14]}</td><td class='total'>{as_d}</td></tr>"
                f"<tr><td class='team-col'>{home[:14]}</td><td class='total'>{hs_d}</td></tr>")
    st.markdown(f"<div class='linescore-wrap'><table class='linescore'>"
                f"<thead><tr>{hdr}</tr></thead><tbody>{rows}</tbody></table></div>",
                unsafe_allow_html=True)


# ── LINEUP ────────────────────────────────────────────────────────────────────
def render_lineup(lineup: list, home: str, away: str, league: str):
    if not lineup:
        st.markdown("<div style='font-family:IBM Plex Mono,monospace;font-size:.65rem;"
                    "color:#2e2e2e;padding:6px 0'>No lineup data available.</div>",
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
        num_s = f"<span style='color:#2a2a2a;font-size:.6rem;margin-right:4px'>#{num}</span>" if num else ""
        pos_s = f"<span style='color:#2a2a2a;font-size:.6rem;margin-left:4px'>{pos}</span>" if pos else ""
        return (f"<div style='padding:5px 0;border-bottom:1px solid #141414;font-size:.82rem'>"
                f"{num_s}<span style='color:#ccc'>{name}</span>{pos_s}</div>")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='section-label'>{away[:20]}</div>", unsafe_allow_html=True)
        st.markdown("".join(row(p) for p in away_p) or
                    "<div style='color:#2a2a2a;font-size:.7rem'>—</div>",
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='section-label'>{home[:20]}</div>", unsafe_allow_html=True)
        st.markdown("".join(row(p) for p in home_p) or
                    "<div style='color:#2a2a2a;font-size:.7rem'>—</div>",
                    unsafe_allow_html=True)


# ── EXTERNAL LINKS ────────────────────────────────────────────────────────────
def build_links(league: str, date_str: str, home: str, away: str) -> str:
    year      = date_str[:4] if date_str else CURRENT_YEAR
    date_dash = date_str

    if league == "NPB":
        npb_results = f"https://npb.jp/bis/eng/{year}/games/"
        bbref_sched = f"https://www.baseball-reference.com/leagues/NPB/{year}-schedule.shtml"
        return (
            f'<a class="ext-link" href="{npb_results}" target="_blank">NPB.jp Results</a>'
            f'<a class="ext-link" href="{bbref_sched}" target="_blank">BBRef Schedule</a>'
        )
    else:
        mykbo       = f"https://mykbostats.com/games/{date_dash}"
        bbref_sched = f"https://www.baseball-reference.com/leagues/KBO/{year}-schedule.shtml"
        kbo_center  = "https://eng.koreabaseball.com/Schedule/GameCenter/Main.aspx"
        return (
            f'<a class="ext-link" href="{mykbo}" target="_blank">MyKBOStats</a>'
            f'<a class="ext-link" href="{kbo_center}" target="_blank">KBO Game Center</a>'
            f'<a class="ext-link" href="{bbref_sched}" target="_blank">BBRef Schedule</a>'
        )


# ── SCORE CARD ────────────────────────────────────────────────────────────────
def render_score_card(ev: dict, league: str):
    home     = ev.get("strHomeTeam", "?")
    away     = ev.get("strAwayTeam", "?")
    hs       = ev.get("intHomeScore")
    as_      = ev.get("intAwayScore")
    date_str = ev.get("dateEvent", "")
    venue    = ev.get("strVenue", "") or ""
    eid      = ev.get("idEvent", "")
    status   = ev.get("strStatus", "") or ""
    final    = hs is not None and as_ is not None

    hc, ac = winner_cls(hs, as_)
    hs_d = str(hs) if final else "–"
    as_d = str(as_) if final else "–"

    if final:
        status_label = "FINAL"
    elif status.upper() in ("IN PROGRESS", "LIVE", "INPROGRESS"):
        status_label = f"LIVE · {status}"
    else:
        time_ = ev.get("strTime", "")
        status_label = utc_to_jst(date_str, time_) if time_ else "SCHEDULED"

    links = build_links(league, date_str, home, away)

    st.markdown(f"""
    <div class="card">
      <div class="card-venue">{venue}</div>
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

    if final and eid:
        with st.expander(f"Box score — {away} @ {home}"):
            st.markdown("<div class='section-label'>linescore</div>", unsafe_allow_html=True)
            stats  = fetch_event_stats(eid)
            ls     = parse_linescore(stats, home, away)
            if ls:
                render_linescore(ls)
            else:
                detail = fetch_event_detail(eid)
                hh = detail.get("intHomeHits",   "") or ""
                ah = detail.get("intAwayHits",   "") or ""
                he = detail.get("intHomeErrors", "") or ""
                ae = detail.get("intAwayErrors", "") or ""
                render_simple_score_table(away, home, as_d, hs_d, ah, hh, ae, he)
                st.markdown(
                    "<div style='font-family:IBM Plex Mono,monospace;font-size:.6rem;"
                    "color:#2a2a2a;margin-top:6px'>Inning-by-inning data not available "
                    "for this game — use the external links above for a full box score.</div>",
                    unsafe_allow_html=True)

            st.markdown("<div class='section-label' style='margin-top:12px'>lineup / players</div>",
                        unsafe_allow_html=True)
            render_lineup(fetch_event_lineup(eid), home, away, league)


# ── SCHEDULE CARD ─────────────────────────────────────────────────────────────
def render_sched_card(ev: dict, league: str):
    home  = ev.get("strHomeTeam", "?")
    away  = ev.get("strAwayTeam", "?")
    date  = ev.get("dateEvent", "")
    time_ = ev.get("strTime", "")
    venue = ev.get("strVenue", "")
    time_disp = utc_to_jst(date, time_)
    venue_str = f"<div class='sched-venue'>{venue}</div>" if venue else ""

    if league == "NPB":
        year = date[:4] if date else CURRENT_YEAR
        quick_link = f'<a class="ext-link" href="https://npb.jp/bis/eng/{year}/games/" target="_blank">NPB.jp</a>'
    else:
        quick_link = f'<a class="ext-link" href="https://mykbostats.com/games/{date}" target="_blank">MyKBOStats</a>'

    st.markdown(f"""
    <div class="sched-card">
      <div class="sched-matchup">
        <div>
          <div class="sched-teams">{away}<span class="sched-at">@</span>{home}</div>
          {venue_str}
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
          <div class="sched-time">{time_disp}</div>
          {quick_link}
        </div>
      </div>
    </div>""", unsafe_allow_html=True)


# ── SCORES PAGE ───────────────────────────────────────────────────────────────
def scores_page(teams: dict, league: str, league_id: str, date_str: str):
    games = get_games_on_date(teams, league_id, date_str)
    if not games:
        st.markdown(
            f"<div class='no-games'>No {league} games found for {fmt_display_date(date_str)}<br>"
            f"<span style='font-size:.6rem'>Try yesterday or a different date — "
            f"TSDB data may lag 12–24 hours</span></div>",
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
            render_sched_card(ev, league)


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="masthead">
  <div class="masthead-title">NPB · KBO</div>
  <div class="masthead-sub">Scores · Schedule · Box Scores</div>
</div>""", unsafe_allow_html=True)

jst_now = now_jst()

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
    st.markdown(f"<div style='font-family:IBM Plex Mono,monospace;font-size:.62rem;"
                f"color:#333;padding-top:10px'>JST {jst_now.strftime('%H:%M')}</div>",
                unsafe_allow_html=True)
with c3:
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

today_s     = jst_now.strftime("%Y-%m-%d")
yesterday_s = (jst_now - timedelta(days=1)).strftime("%Y-%m-%d")
if selected_str == today_s:
    dlabel = f"Today · {fmt_display_date(selected_str)}"
elif selected_str == yesterday_s:
    dlabel = f"Yesterday · {fmt_display_date(selected_str)}"
else:
    dlabel = fmt_display_date(selected_str)
st.markdown(f"<div class='section-label' style='margin-bottom:.8rem'>{dlabel}</div>",
            unsafe_allow_html=True)

st.markdown("""
<div class='warn-box'>
  Data via TheSportsDB free API — fetches last 5 results per team to build each day's slate.<br>
  Results may lag 12–24 hours. Inning-by-inning box scores depend on TSDB coverage for each game.<br>
  Use the external links on each card for full box scores on official / third-party sites.
</div>""", unsafe_allow_html=True)

t_npb, t_kbo, t_npb_s, t_kbo_s = st.tabs([
    "\U0001f1ef\U0001f1f5  NPB Scores", "\U0001f1f0\U0001f1f7  KBO Scores",
    "\U0001f1ef\U0001f1f5  NPB Schedule", "\U0001f1f0\U0001f1f7  KBO Schedule",
])

with t_npb:
    scores_page(NPB_TEAMS, "NPB", NPB_LEAGUE_ID, selected_str)

with t_kbo:
    scores_page(KBO_TEAMS, "KBO", KBO_LEAGUE_ID, selected_str)

with t_npb_s:
    schedule_page(NPB_TEAMS, "NPB")

with t_kbo_s:
    schedule_page(KBO_TEAMS, "KBO")

st.markdown("---")
st.markdown(
    "<span style='font-family:IBM Plex Mono,monospace;font-size:.58rem;color:#222;letter-spacing:.1em'>"
    f"Data: TheSportsDB · All times JST (UTC+9) · {CURRENT_YEAR} season · "
    "Score cache 5 min · Schedule cache 10 min</span>",
    unsafe_allow_html=True)
