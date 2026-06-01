import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import streamlit.components.v1 as components

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Asia Baseball Dashboard",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── STYLING ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800;900&family=Barlow:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
.main-header {
    background: linear-gradient(135deg, #C8102E 0%, #8B0000 100%);
    padding: 1.2rem 1.5rem; border-radius: 12px;
    margin-bottom: 1rem; display: flex; align-items: center; gap: 1rem;
}
.main-header h1 {
    font-family: 'Barlow Condensed', sans-serif; font-size: 2rem;
    font-weight: 900; color: white; margin: 0; letter-spacing: 0.04em;
}
.main-header p {
    color: rgba(255,255,255,0.7); font-size: 0.75rem;
    letter-spacing: 0.15em; text-transform: uppercase; margin: 0;
}
.score-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.65rem 0.9rem; border-radius: 8px; margin-bottom: 0.4rem;
    background: #f8f7f5;
}
.score-num-kbo { font-weight: 800; font-size: 1.15rem; color: #C8102E; font-family: 'Barlow Condensed', sans-serif; }
.score-num-npb { font-weight: 800; font-size: 1.15rem; color: #003087; font-family: 'Barlow Condensed', sans-serif; }
.team-name { font-weight: 700; font-size: 0.95rem; font-family: 'Barlow Condensed', sans-serif; }
.game-meta { font-size: 0.68rem; color: #aaa; letter-spacing: 0.06em; text-transform: uppercase; }
.updated-tag { font-size: 0.68rem; color: #bbb; letter-spacing: 0.06em; text-transform: uppercase; }
.source-note { font-size: 0.72rem; color: #999; font-style: italic; margin-bottom: 0.4rem; }
.standings-note {
    background: #fff8e1; border: 1px solid #ffe082; border-radius: 8px;
    padding: 0.6rem 0.9rem; font-size: 0.78rem; color: #5d4037;
    margin-bottom: 0.75rem; line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
KBO_LEAGUE_ID = "4830"
NPB_LEAGUE_ID = "4591"
TSDB_BASE     = "https://www.thesportsdb.com/api/v1/json/123"

# FanGraphs — these headers are required; FanGraphs checks Referer and Accept
FG_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.fangraphs.com/",
    "Origin": "https://www.fangraphs.com",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Cache-Control": "max-age=0",
}

TSDB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Standings iframes — official/reliable sources that render in browser
# KBO: official English standings page
# NPB: Baseball Reference international (renders fine as iframe)
KBO_STANDINGS_URL = "https://eng.koreabaseball.com/Record/Team/TeamRank/Regular.aspx"
NPB_CL_STANDINGS_URL = "https://npb.jp/eng/standings/"
NPB_PL_STANDINGS_URL = "https://npb.jp/eng/standings/"

# ── DATA FETCHING ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_tsdb(league_id: str, mode: str = "past") -> list:
    endpoint = "eventspastleague" if mode == "past" else "eventsnextleague"
    url = f"{TSDB_BASE}/{endpoint}.php?id={league_id}"
    try:
        r = requests.get(url, headers=TSDB_HEADERS, timeout=12)
        r.raise_for_status()
        return r.json().get("events") or []
    except Exception:
        return []


@st.cache_data(ttl=1800)
def fetch_fangraphs(league: str, stat: str = "bat") -> pd.DataFrame | None:
    """
    Fetch FanGraphs international leaderboard.
    league: 'kbo' or 'npb'
    stat: 'bat' or 'pit'
    
    FanGraphs requires:
      - Referer: https://www.fangraphs.com/
      - Full browser-like Accept headers
      - The stats param: ?stats=pit for pitching, default is batting
    """
    base = f"https://www.fangraphs.com/leaders/international/{league}"
    url  = base if stat == "bat" else f"{base}?stats=pit"

    try:
        session = requests.Session()
        # First visit the base FanGraphs page to get a session cookie,
        # which some CDN/bot-protection layers check for
        session.get("https://www.fangraphs.com/", headers=FG_HEADERS, timeout=10)

        r = session.get(url, headers=FG_HEADERS, timeout=20)
        r.raise_for_status()

        # Parse all tables from the HTML
        tables = pd.read_html(r.text, flavor="lxml")
        if not tables:
            return None

        # FanGraphs renders the stats table as the largest table
        # with a 'Name' column. Find it.
        for df in sorted(tables, key=len, reverse=True):
            cols_lower = [str(c).lower() for c in df.columns]
            if "name" in cols_lower and len(df) >= 5:
                df = _clean_fg_df(df)
                return df

        return _clean_fg_df(max(tables, key=len))

    except Exception as e:
        st.warning(f"FanGraphs fetch error ({league} {stat}): {e}")
        return None


def _clean_fg_df(df: pd.DataFrame) -> pd.DataFrame:
    """Clean up a FanGraphs scraped DataFrame."""
    # Drop unnamed index columns
    df = df.loc[:, ~df.columns.astype(str).str.match(r'^Unnamed|^#$')]
    # Drop all-NaN rows and repeated header rows
    df = df.dropna(how="all")
    if "Name" in df.columns:
        df = df[df["Name"].astype(str) != "Name"]
    # Strip Korean/Japanese characters from Name column for readability
    # (FanGraphs includes them like "Seong-han Park 박성한" — keep as-is, it's useful)
    df = df.reset_index(drop=True)
    df.insert(0, "#", range(1, len(df) + 1))
    return df


def _safe_sort(df: pd.DataFrame, col: str, ascending: bool = False) -> pd.DataFrame:
    if col not in df.columns:
        return df
    try:
        df = df.copy()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.sort_values(col, ascending=ascending).reset_index(drop=True)
    except Exception:
        return df


# ── UI HELPERS ────────────────────────────────────────────────────────────────

def render_scores(events: list, league: str):
    num_cls = "score-num-kbo" if league == "KBO" else "score-num-npb"
    if not events:
        st.info("⚠️ No score data from TheSportsDB right now.")
        return
    for e in events[:8]:
        home  = e.get("strHomeTeam", "?")
        away  = e.get("strAwayTeam", "?")
        hs    = e.get("intHomeScore")
        as_   = e.get("intAwayScore")
        date  = e.get("dateEvent", "")
        time_ = (e.get("strTime") or "")[:5]

        if hs is not None and as_ is not None:
            score_html = f'<span class="{num_cls}">{hs} – {as_}</span>'
            meta       = f"FINAL · {date}"
        else:
            score_html = '<span class="game-meta">UPCOMING</span>'
            meta       = f"{date}  {time_ or 'TBD'}"

        st.markdown(f"""
        <div class="score-row">
            <div>
                <span class="team-name">{home}</span><br>
                <span class="team-name">{away}</span>
            </div>
            <div style="text-align:right">
                {score_html}<br>
                <span class="game-meta">{meta}</span>
            </div>
        </div>""", unsafe_allow_html=True)


def render_fg_table(league: str, stat: str):
    """Load and display a FanGraphs leaderboard with sort/filter controls."""
    label = "Batting" if stat == "bat" else "Pitching"
    league_upper = league.upper()

    st.markdown(f'<p class="source-note">Source: FanGraphs · {league_upper} {label} · Updated nightly</p>',
                unsafe_allow_html=True)

    with st.spinner(f"Loading {league_upper} {label.lower()} stats from FanGraphs..."):
        df = fetch_fangraphs(league, stat)

    if df is not None and not df.empty:
        stat_cols = [c for c in df.columns if c not in ("#", "Name", "Team", "Age")]

        # Smart default sort column
        if stat == "bat":
            default = next((c for c in ["AVG", "HR", "RBI", "OPS"] if c in stat_cols), stat_cols[0] if stat_cols else None)
        else:
            default = next((c for c in ["ERA", "W", "SO", "WHIP"] if c in stat_cols), stat_cols[0] if stat_cols else None)

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            sort_col = st.selectbox(
                "Sort by:", stat_cols,
                index=stat_cols.index(default) if default in stat_cols else 0,
                key=f"{league}_{stat}_sort"
            )
        with col2:
            max_rows = st.slider("Rows:", 10, 100, 30, key=f"{league}_{stat}_rows")
        with col3:
            # Team filter
            if "Team" in df.columns:
                teams = ["All"] + sorted(df["Team"].dropna().unique().tolist())
                team_filter = st.selectbox("Team:", teams, key=f"{league}_{stat}_team")
            else:
                team_filter = "All"

        # Apply team filter
        if team_filter != "All" and "Team" in df.columns:
            df = df[df["Team"] == team_filter]

        # Sort — ERA/WHIP sort ascending (lower is better)
        low_better = sort_col in {"ERA", "WHIP", "BB", "BB9", "BB/9", "HR/9"}
        df_sorted = _safe_sort(df, sort_col, ascending=low_better)
        df_sorted["#"] = range(1, len(df_sorted) + 1)

        st.dataframe(df_sorted.head(max_rows), use_container_width=True, hide_index=True)
        st.caption(f"{len(df_sorted)} players · Sorted by {sort_col} · FanGraphs")
    else:
        st.error("Could not load FanGraphs data. Try the direct link below.")

    # Always show direct link as backup
    url = f"https://www.fangraphs.com/leaders/international/{league}" + ("?stats=pit" if stat == "pit" else "")
    st.link_button(f"Open on FanGraphs ↗", url)


def render_standings_iframe(league: str):
    """
    Render official standings as an iframe.
    This bypasses all scraping issues — the browser loads the page directly.
    """
    if league == "KBO":
        st.markdown("""
        <div class="standings-note">
            📊 Live KBO standings from the official English KBO website, loaded directly in your browser.
        </div>""", unsafe_allow_html=True)
        components.iframe(KBO_STANDINGS_URL, height=520, scrolling=True)
        st.link_button("Open KBO Standings full page ↗", KBO_STANDINGS_URL)

    else:  # NPB
        st.markdown("""
        <div class="standings-note">
            📊 Live NPB standings (Central & Pacific leagues) from NPB's official English site.
        </div>""", unsafe_allow_html=True)
        components.iframe(NPB_PL_STANDINGS_URL, height=600, scrolling=True)
        st.link_button("Open NPB Standings full page ↗", NPB_PL_STANDINGS_URL)


# ── HEADER ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <div style="font-size:2.5rem">⚾</div>
    <div>
        <h1>ASIA BASEBALL DASHBOARD</h1>
        <p>KBO · NPB · Scores · Standings · Stats</p>
    </div>
</div>
""", unsafe_allow_html=True)

col_info, col_btn = st.columns([5, 1])
with col_info:
    st.markdown(
        f'<span class="updated-tag">Loaded: {datetime.now().strftime("%b %d %Y %I:%M %p")}</span>',
        unsafe_allow_html=True
    )
with col_btn:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# ── LEAGUE TABS ───────────────────────────────────────────────────────────────
kbo_tab, npb_tab = st.tabs(["🇰🇷  KBO — Korea", "🇯🇵  NPB — Japan"])

# ══════════════════════════════════════════════════════════════════════════════
# KBO
# ══════════════════════════════════════════════════════════════════════════════
with kbo_tab:
    t1, t2, t3, t4 = st.tabs(["⚾ Scores", "🏆 Standings", "🥎 Batting", "💪 Pitching"])

    with t1:
        st.subheader("Recent Results")
        st.markdown('<p class="source-note">Source: TheSportsDB · KBO League ID 4830</p>', unsafe_allow_html=True)
        render_scores(fetch_tsdb(KBO_LEAGUE_ID, "past"), "KBO")
        st.subheader("Upcoming")
        render_scores(fetch_tsdb(KBO_LEAGUE_ID, "next"), "KBO")

    with t2:
        st.subheader("2026 KBO Standings")
        render_standings_iframe("KBO")

    with t3:
        st.subheader("2026 KBO Batting Leaders")
        render_fg_table("kbo", "bat")

    with t4:
        st.subheader("2026 KBO Pitching Leaders")
        render_fg_table("kbo", "pit")

# ══════════════════════════════════════════════════════════════════════════════
# NPB
# ══════════════════════════════════════════════════════════════════════════════
with npb_tab:
    t5, t6, t7, t8 = st.tabs(["⚾ Scores", "🏆 Standings", "🥎 Batting", "💪 Pitching"])

    with t5:
        st.subheader("Recent Results")
        st.markdown('<p class="source-note">Source: TheSportsDB · NPB League ID 4591</p>', unsafe_allow_html=True)
        render_scores(fetch_tsdb(NPB_LEAGUE_ID, "past"), "NPB")
        st.subheader("Upcoming")
        render_scores(fetch_tsdb(NPB_LEAGUE_ID, "next"), "NPB")

    with t6:
        st.subheader("2026 NPB Standings")
        render_standings_iframe("NPB")

    with t7:
        st.subheader("2026 NPB Batting Leaders")
        render_fg_table("npb", "bat")

    with t8:
        st.subheader("2026 NPB Pitching Leaders")
        render_fg_table("npb", "pit")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<span class="updated-tag">'
    'Scores: TheSportsDB · Stats: FanGraphs · Standings: Official KBO/NPB sites · '
    'Scores cache 5min · Stats cache 30min'
    '</span>',
    unsafe_allow_html=True,
)
