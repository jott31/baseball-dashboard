import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
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
    padding: 1.2rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.main-header h1 {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2rem;
    font-weight: 900;
    color: white;
    margin: 0;
    letter-spacing: 0.04em;
}
.main-header p {
    color: rgba(255,255,255,0.7);
    font-size: 0.75rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin: 0;
}

.section-card {
    background: white;
    border-radius: 10px;
    padding: 1rem;
    border-left: 4px solid #C8102E;
    margin-bottom: 0.75rem;
    box-shadow: 0 1px 8px rgba(0,0,0,0.06);
}
.section-card.npb { border-left-color: #003087; }

.score-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0.8rem;
    border-radius: 8px;
    margin-bottom: 0.4rem;
    background: #f8f7f5;
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1rem;
}
.score-row:hover { background: #f0ede8; }
.score-num { font-weight: 800; font-size: 1.1rem; color: #C8102E; }
.score-num.npb { color: #003087; }
.team-name { font-weight: 700; font-size: 0.95rem; }
.game-status { font-size: 0.72rem; color: #aaa; letter-spacing: 0.06em; text-transform: uppercase; }

.stat-header {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #888;
    padding: 0.3rem 0;
    border-bottom: 2px solid #eee;
    margin-bottom: 0.5rem;
}

.updated-tag {
    font-size: 0.68rem;
    color: #bbb;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    letter-spacing: 0.06em;
    font-size: 0.95rem;
}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
KBO_LEAGUE_ID = "4830"
NPB_LEAGUE_ID = "4831"
TSDB_BASE = "https://www.thesportsdb.com/api/v1/json/123"
BREF_BASE = "https://www.baseball-reference.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

KBO_TEAMS = {
    "Samsung Lions": "🦁", "Lotte Giants": "🦅", "Kia Tigers": "🐯",
    "Doosan Bears": "🐻", "LG Twins": "⚡", "SSG Landers": "🚀",
    "KT Wiz": "🧙", "NC Dinos": "🦕", "Hanwha Eagles": "🦅",
    "Kiwoom Heroes": "⚔️",
}
NPB_TEAMS = {
    "Yomiuri Giants": "🗼", "Hanshin Tigers": "🐯", "SoftBank Hawks": "🦅",
    "Orix Buffaloes": "🐃", "Lotte Marines": "⚓", "Seibu Lions": "🦁",
    "Yakult Swallows": "🐦", "DeNA BayStars": "⭐", "Hiroshima Carp": "🎏",
    "Chunichi Dragons": "🐉", "Nippon-Ham Fighters": "🥊", "Rakuten Eagles": "🦅",
}

# ── DATA FETCHING ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)  # Cache 5 minutes
def fetch_tsdb_scores(league_id: str, mode: str = "past") -> list:
    """Fetch recent or upcoming games from TheSportsDB."""
    endpoint = "eventspastleague" if mode == "past" else "eventsnextleague"
    url = f"{TSDB_BASE}/{endpoint}.php?id={league_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("events") or []
    except Exception as e:
        return []


@st.cache_data(ttl=300)
def fetch_tsdb_day(date_str: str, league_id: str) -> list:
    """Fetch games for a specific date."""
    url = f"{TSDB_BASE}/eventsday.php?d={date_str}&l={league_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("events") or []
    except Exception:
        return []


@st.cache_data(ttl=1800)  # Cache 30 minutes for standings
def fetch_bref_kbo_standings() -> pd.DataFrame | None:
    """Scrape KBO standings from Baseball Reference."""
    url = f"{BREF_BASE}/international/KOR/KBO-standings.shtml"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", {"id": lambda x: x and "standings" in x.lower()})
        if not table:
            tables = soup.find_all("table")
            table = tables[0] if tables else None
        if table:
            df = pd.read_html(str(table))[0]
            return df
    except Exception as e:
        st.warning(f"Could not fetch BBRef standings: {e}")
    return None


@st.cache_data(ttl=1800)
def fetch_bref_kbo_batting() -> pd.DataFrame | None:
    """Scrape KBO batting leaders from Baseball Reference."""
    url = f"{BREF_BASE}/international/KOR/KBO-batting.shtml"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        tables = pd.read_html(r.text)
        if tables:
            df = tables[0]
            # Clean up multi-level columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [' '.join(c).strip() for c in df.columns]
            return df
    except Exception as e:
        st.warning(f"Could not fetch BBRef batting: {e}")
    return None


@st.cache_data(ttl=1800)
def fetch_bref_kbo_pitching() -> pd.DataFrame | None:
    """Scrape KBO pitching leaders from Baseball Reference."""
    url = f"{BREF_BASE}/international/KOR/KBO-pitching.shtml"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        tables = pd.read_html(r.text)
        if tables:
            df = tables[0]
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [' '.join(c).strip() for c in df.columns]
            return df
    except Exception as e:
        st.warning(f"Could not fetch BBRef pitching: {e}")
    return None


@st.cache_data(ttl=1800)
def fetch_bref_npb_standings() -> pd.DataFrame | None:
    """Scrape NPB standings from Baseball Reference."""
    url = f"{BREF_BASE}/international/JPN/NPB-standings.shtml"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tables = pd.read_html(r.text)
        if tables:
            return tables[0]
    except Exception as e:
        st.warning(f"Could not fetch NPB standings: {e}")
    return None


@st.cache_data(ttl=1800)
def fetch_fangraphs_kbo_batting() -> pd.DataFrame | None:
    """Scrape KBO batting leaderboard from FanGraphs."""
    url = "https://www.fangraphs.com/leaders/international/kbo"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        tables = pd.read_html(r.text)
        if tables:
            # Find the main stats table (usually largest)
            df = max(tables, key=len)
            return df
    except Exception as e:
        st.warning(f"Could not fetch FanGraphs KBO batting: {e}")
    return None


@st.cache_data(ttl=1800)
def fetch_fangraphs_npb_batting() -> pd.DataFrame | None:
    """Scrape NPB batting leaderboard from FanGraphs."""
    url = "https://www.fangraphs.com/leaders/international/npb"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        tables = pd.read_html(r.text)
        if tables:
            df = max(tables, key=len)
            return df
    except Exception as e:
        st.warning(f"Could not fetch FanGraphs NPB batting: {e}")
    return None


# ── UI HELPERS ────────────────────────────────────────────────────────────────

def render_score_card(event: dict, league: str = "KBO"):
    """Render a single game result as a styled card."""
    home = event.get("strHomeTeam", "?")
    away = event.get("strAwayTeam", "?")
    hs = event.get("intHomeScore")
    as_ = event.get("intAwayScore")
    status = event.get("strStatus", "")
    date = event.get("dateEvent", "")
    color_class = "" if league == "KBO" else " npb"

    if hs is not None and as_ is not None:
        score_str = f'<span class="score-num{color_class}">{hs}</span> – <span class="score-num{color_class}">{as_}</span>'
        status_display = f"FINAL · {date}"
    else:
        score_str = '<span class="game-status">UPCOMING</span>'
        t = event.get("strTime", "")
        status_display = f"{date} · {t[:5] if t else 'TBD'}"

    teams = KBO_TEAMS if league == "KBO" else NPB_TEAMS
    home_icon = teams.get(home, "⚾")
    away_icon = teams.get(away, "⚾")

    st.markdown(f"""
    <div class="score-row">
        <div>
            <span class="team-name">{home_icon} {home}</span><br>
            <span class="team-name">{away_icon} {away}</span>
        </div>
        <div style="text-align:right">
            {score_str}<br>
            <span class="game-status">{status_display}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_dataframe(df: pd.DataFrame, max_rows: int = 20):
    """Render a clean dataframe with Streamlit's native table."""
    if df is None or df.empty:
        st.info("No data available.")
        return
    # Drop unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    # Drop separator rows (rows where all values are same or NaN-heavy)
    df = df.dropna(how='all')
    st.dataframe(
        df.head(max_rows),
        use_container_width=True,
        hide_index=True,
    )


def show_fallback_links(league: str):
    """Show direct links to data sources as fallback."""
    st.markdown("---")
    st.markdown("**📊 View full stats directly:**")
    if league == "KBO":
        col1, col2, col3 = st.columns(3)
        col1.link_button("FanGraphs KBO", "https://www.fangraphs.com/leaders/international/kbo")
        col2.link_button("Baseball Reference KBO", "https://www.baseball-reference.com/international/KOR/")
        col3.link_button("Official KBO Site", "https://eng.koreabaseball.com")
    else:
        col1, col2, col3 = st.columns(3)
        col1.link_button("FanGraphs NPB", "https://www.fangraphs.com/leaders/international/npb")
        col2.link_button("Baseball Reference NPB", "https://www.baseball-reference.com/international/JPN/")
        col3.link_button("Official NPB Site", "https://npb.jp/eng/")


# ── MAIN APP ──────────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header">
    <div style="font-size:2.5rem">⚾</div>
    <div>
        <h1>ASIA BASEBALL DASHBOARD</h1>
        <p>KBO · NPB · Scores · Standings · Stats</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Refresh button + last updated
col_r1, col_r2 = st.columns([4, 1])
with col_r2:
    if st.button("🔄 Refresh All", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col_r1:
    st.markdown(f'<span class="updated-tag">Last loaded: {datetime.now().strftime("%b %d, %Y %I:%M %p")}</span>',
                unsafe_allow_html=True)

st.markdown("---")

# ── LEAGUE TABS ───────────────────────────────────────────────────────────────
league_tab_kbo, league_tab_npb = st.tabs(["🇰🇷  KBO — Korea", "🇯🇵  NPB — Japan"])

# ══════════════════════════════════════════════════════════════════════════════
# KBO TAB
# ══════════════════════════════════════════════════════════════════════════════
with league_tab_kbo:
    scores_tab, standings_tab, batting_tab, pitching_tab = st.tabs(
        ["⚾ Scores", "🏆 Standings", "🥎 Batting Leaders", "💪 Pitching Leaders"]
    )

    # ── KBO SCORES ──
    with scores_tab:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Recent Results")

        today = datetime.now()
        past_events = fetch_tsdb_scores(KBO_LEAGUE_ID, "past")
        upcoming_events = fetch_tsdb_scores(KBO_LEAGUE_ID, "next")

        if past_events:
            for e in past_events[:5]:
                render_score_card(e, "KBO")
        else:
            st.info("⚠️ Score data unavailable from TheSportsDB right now.")
            show_fallback_links("KBO")

        st.markdown("### Upcoming Games")
        if upcoming_events:
            for e in upcoming_events[:5]:
                render_score_card(e, "KBO")
        else:
            st.info("No upcoming game data available.")

        st.markdown('</div>', unsafe_allow_html=True)

    # ── KBO STANDINGS ──
    with standings_tab:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 2026 KBO Standings")
        st.caption("Source: Baseball Reference · Updated daily")

        with st.spinner("Loading standings..."):
            df_standings = fetch_bref_kbo_standings()

        if df_standings is not None:
            render_dataframe(df_standings)
        else:
            st.warning("Could not load standings automatically.")

        show_fallback_links("KBO")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── KBO BATTING ──
    with batting_tab:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 2026 KBO Batting Leaders")

        source = st.radio("Data source:", ["FanGraphs", "Baseball Reference"],
                          horizontal=True, key="kbo_bat_source")

        with st.spinner("Loading batting stats..."):
            if source == "FanGraphs":
                df_bat = fetch_fangraphs_kbo_batting()
            else:
                df_bat = fetch_bref_kbo_batting()

        if df_bat is not None:
            # Filter controls
            col1, col2 = st.columns(2)
            with col1:
                sort_col = st.selectbox("Sort by:", df_bat.columns.tolist()[:15], key="kbo_bat_sort")
            with col2:
                max_rows = st.slider("Rows to show:", 10, 50, 20, key="kbo_bat_rows")

            df_sorted = df_bat.sort_values(sort_col, ascending=False).reset_index(drop=True) \
                if sort_col in df_bat.columns else df_bat
            render_dataframe(df_sorted, max_rows)
        else:
            st.warning("Could not load batting data automatically.")

        show_fallback_links("KBO")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── KBO PITCHING ──
    with pitching_tab:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 2026 KBO Pitching Leaders")
        st.caption("Source: Baseball Reference")

        with st.spinner("Loading pitching stats..."):
            df_pitch = fetch_bref_kbo_pitching()

        if df_pitch is not None:
            col1, col2 = st.columns(2)
            with col1:
                sort_col_p = st.selectbox("Sort by:", df_pitch.columns.tolist()[:15], key="kbo_pit_sort")
            with col2:
                max_rows_p = st.slider("Rows to show:", 10, 50, 20, key="kbo_pit_rows")

            asc = sort_col_p in ["ERA", "BB", "HR", "WHIP"]
            df_sorted_p = df_pitch.sort_values(sort_col_p, ascending=asc).reset_index(drop=True) \
                if sort_col_p in df_pitch.columns else df_pitch
            render_dataframe(df_sorted_p, max_rows_p)
        else:
            st.warning("Could not load pitching data automatically.")

        show_fallback_links("KBO")
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# NPB TAB
# ══════════════════════════════════════════════════════════════════════════════
with league_tab_npb:
    npb_scores_tab, npb_standings_tab, npb_batting_tab = st.tabs(
        ["⚾ Scores", "🏆 Standings", "🥎 Batting Leaders"]
    )

    # ── NPB SCORES ──
    with npb_scores_tab:
        st.markdown('<div class="section-card npb">', unsafe_allow_html=True)
        st.markdown("### Recent Results")

        past_npb = fetch_tsdb_scores(NPB_LEAGUE_ID, "past")
        upcoming_npb = fetch_tsdb_scores(NPB_LEAGUE_ID, "next")

        if past_npb:
            for e in past_npb[:5]:
                render_score_card(e, "NPB")
        else:
            st.info("⚠️ NPB score data unavailable right now.")
            show_fallback_links("NPB")

        st.markdown("### Upcoming Games")
        if upcoming_npb:
            for e in upcoming_npb[:5]:
                render_score_card(e, "NPB")
        else:
            st.info("No upcoming game data available.")

        st.markdown('</div>', unsafe_allow_html=True)

    # ── NPB STANDINGS ──
    with npb_standings_tab:
        st.markdown('<div class="section-card npb">', unsafe_allow_html=True)
        st.markdown("### 2026 NPB Standings")
        st.caption("Source: Baseball Reference · Updated daily")

        with st.spinner("Loading NPB standings..."):
            df_npb_stand = fetch_bref_npb_standings()

        if df_npb_stand is not None:
            render_dataframe(df_npb_stand)
        else:
            st.warning("Could not load NPB standings automatically.")

        show_fallback_links("NPB")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── NPB BATTING ──
    with npb_batting_tab:
        st.markdown('<div class="section-card npb">', unsafe_allow_html=True)
        st.markdown("### 2026 NPB Batting Leaders")
        st.caption("Source: FanGraphs · Updated nightly")

        with st.spinner("Loading NPB batting stats..."):
            df_npb_bat = fetch_fangraphs_npb_batting()

        if df_npb_bat is not None:
            col1, col2 = st.columns(2)
            with col1:
                sort_npb = st.selectbox("Sort by:", df_npb_bat.columns.tolist()[:15], key="npb_bat_sort")
            with col2:
                rows_npb = st.slider("Rows to show:", 10, 50, 20, key="npb_bat_rows")

            df_npb_sorted = df_npb_bat.sort_values(sort_npb, ascending=False).reset_index(drop=True) \
                if sort_npb in df_npb_bat.columns else df_npb_bat
            render_dataframe(df_npb_sorted, rows_npb)
        else:
            st.warning("Could not load NPB batting data automatically.")

        show_fallback_links("NPB")
        st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<span class="updated-tag">Data sources: TheSportsDB · Baseball Reference · FanGraphs · '
    'Scores cache: 5min · Stats cache: 30min</span>',
    unsafe_allow_html=True
)
