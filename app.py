import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

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
.main-header p { color: rgba(255,255,255,0.7); font-size: 0.75rem; letter-spacing: 0.15em; text-transform: uppercase; margin: 0; }
.score-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.6rem 0.8rem; border-radius: 8px; margin-bottom: 0.4rem;
    background: #f8f7f5; font-family: 'Barlow Condensed', sans-serif; font-size: 1rem;
}
.score-num-kbo { font-weight: 800; font-size: 1.1rem; color: #C8102E; }
.score-num-npb { font-weight: 800; font-size: 1.1rem; color: #003087; }
.team-name { font-weight: 700; font-size: 0.95rem; }
.game-status { font-size: 0.72rem; color: #aaa; letter-spacing: 0.06em; text-transform: uppercase; }
.updated-tag { font-size: 0.68rem; color: #bbb; letter-spacing: 0.06em; text-transform: uppercase; }
.source-note { font-size: 0.72rem; color: #aaa; font-style: italic; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
# TheSportsDB — corrected IDs
KBO_LEAGUE_ID  = "4830"   # Korean KBO League ✅
NPB_LEAGUE_ID  = "4591"   # Nippon Baseball League ✅ (was 4831 = basketball!)

TSDB_BASE = "https://www.thesportsdb.com/api/v1/json/123"

# FanGraphs international leaderboard pages (full HTML, parseable)
FG_KBO_BAT  = "https://www.fangraphs.com/leaders/international/kbo"
FG_KBO_PIT  = "https://www.fangraphs.com/leaders/international/kbo?stats=pit"
FG_NPB_BAT  = "https://www.fangraphs.com/leaders/international/npb"
FG_NPB_PIT  = "https://www.fangraphs.com/leaders/international/npb?stats=pit"

# Flashscore standings (more scrape-friendly than BBRef)
FS_KBO_STANDINGS = "https://www.flashscoreusa.com/baseball/south-korea/kbo/standings/"
FS_NPB_STANDINGS = "https://www.flashscoreusa.com/baseball/japan/npb/standings/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Drop unnamed columns, all-NaN rows, and reset index."""
    df = df.loc[:, ~df.columns.astype(str).str.contains(r'^Unnamed|^#$', regex=True)]
    df = df.dropna(how="all")
    # Drop rows that are just repeated headers (common in BBRef/FG scraped tables)
    if "Name" in df.columns:
        df = df[df["Name"] != "Name"]
    df = df.reset_index(drop=True)
    # Add 1-based rank column
    df.insert(0, "#", range(1, len(df) + 1))
    return df


def safe_sort(df: pd.DataFrame, col: str, ascending: bool = False) -> pd.DataFrame:
    if col in df.columns:
        try:
            df = df.copy()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            return df.sort_values(col, ascending=ascending).reset_index(drop=True)
        except Exception:
            pass
    return df


def render_df(df: pd.DataFrame, max_rows: int = 30):
    if df is None or df.empty:
        st.info("No data to display.")
        return
    st.dataframe(df.head(max_rows), use_container_width=True, hide_index=True)


def fallback_links(league: str):
    st.markdown("---")
    st.markdown("**📊 View full stats directly on:**")
    if league == "KBO":
        c1, c2, c3 = st.columns(3)
        c1.link_button("FanGraphs KBO", FG_KBO_BAT)
        c2.link_button("FanGraphs KBO Pitching", FG_KBO_PIT)
        c3.link_button("Official KBO Site", "https://eng.koreabaseball.com")
    else:
        c1, c2, c3 = st.columns(3)
        c1.link_button("FanGraphs NPB", FG_NPB_BAT)
        c2.link_button("FanGraphs NPB Pitching", FG_NPB_PIT)
        c3.link_button("Official NPB Site", "https://npb.jp/eng/")

# ── DATA FETCHING ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_tsdb(league_id: str, mode: str = "past") -> list:
    """TheSportsDB: recent results or upcoming games."""
    endpoint = "eventspastleague" if mode == "past" else "eventsnextleague"
    url = f"{TSDB_BASE}/{endpoint}.php?id={league_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        return r.json().get("events") or []
    except Exception as e:
        return []


@st.cache_data(ttl=1800)
def fetch_fg_table(url: str) -> pd.DataFrame | None:
    """
    Fetch a FanGraphs international leaderboard page and parse the stats table.
    FanGraphs renders the table as plain HTML — pd.read_html works reliably.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        tables = pd.read_html(r.text)
        if not tables:
            return None
        # The stats table is the largest one with a 'Name' column
        for df in sorted(tables, key=len, reverse=True):
            if "Name" in df.columns or "name" in [c.lower() for c in df.columns]:
                return clean_df(df)
        # Fallback: just use the biggest table
        return clean_df(max(tables, key=len))
    except Exception as e:
        return None


@st.cache_data(ttl=600)
def fetch_standings_flashscore(league: str) -> pd.DataFrame | None:
    """
    Flashscore standings via JavaScript-rendered page.
    Since Flashscore is JS-heavy, we fall back to a static Wikipedia scrape
    which is reliably available and updated frequently during the season.
    """
    wiki_urls = {
        "KBO":  "https://en.wikipedia.org/wiki/2026_KBO_League_season",
        "NPB":  "https://en.wikipedia.org/wiki/2026_NPB_season",
    }
    url = wiki_urls.get(league, "")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        tables = pd.read_html(r.text)
        # Find the table most likely to be standings (has W, L, or Pct columns)
        standing_keywords = {"w", "l", "pct", "gb", "win", "loss", "team", "club"}
        best = None
        best_score = 0
        for df in tables:
            cols_lower = {str(c).lower() for c in df.columns}
            score = len(cols_lower & standing_keywords)
            if score > best_score and len(df) >= 5:
                best_score = score
                best = df
        if best is not None:
            return clean_df(best)
    except Exception as e:
        pass
    return None


@st.cache_data(ttl=600)
def fetch_npb_standings_detailed() -> dict[str, pd.DataFrame]:
    """NPB has Central + Pacific leagues. Try Wikipedia for both."""
    result = {}
    url = "https://en.wikipedia.org/wiki/2026_NPB_season"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        tables = pd.read_html(r.text)
        standing_keywords = {"w", "l", "pct", "gb", "team", "club"}
        candidates = []
        for df in tables:
            cols_lower = {str(c).lower() for c in df.columns}
            score = len(cols_lower & standing_keywords)
            if score >= 3 and 5 <= len(df) <= 10:
                candidates.append((score, df))
        candidates.sort(key=lambda x: -x[0])
        if len(candidates) >= 2:
            result["Central League"] = clean_df(candidates[0][1])
            result["Pacific League"] = clean_df(candidates[1][1])
        elif len(candidates) == 1:
            result["NPB Standings"] = clean_df(candidates[0][1])
    except Exception:
        pass
    return result

# ── SCORE RENDERING ───────────────────────────────────────────────────────────

def render_scores(events: list, league: str):
    color_cls = "score-num-kbo" if league == "KBO" else "score-num-npb"
    if not events:
        st.info("⚠️ No score data returned from TheSportsDB right now.")
        fallback_links(league)
        return
    for e in events[:8]:
        home  = e.get("strHomeTeam", "?")
        away  = e.get("strAwayTeam", "?")
        hs    = e.get("intHomeScore")
        as_   = e.get("intAwayScore")
        date  = e.get("dateEvent", "")
        time_ = e.get("strTime", "")

        if hs is not None and as_ is not None:
            score = f'<span class="{color_cls}">{hs} – {as_}</span>'
            status = f"FINAL · {date}"
        else:
            score = '<span class="game-status">UPCOMING</span>'
            status = f"{date}  {time_[:5] if time_ else 'TBD'}"

        st.markdown(f"""
        <div class="score-row">
            <div>
                <span class="team-name">{home}</span><br>
                <span class="team-name">{away}</span>
            </div>
            <div style="text-align:right">
                {score}<br>
                <span class="game-status">{status}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
    st.markdown(f'<span class="updated-tag">Loaded: {datetime.now().strftime("%b %d %Y %I:%M %p")}</span>', unsafe_allow_html=True)
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
    t_scores, t_stand, t_bat, t_pit = st.tabs(
        ["⚾ Scores", "🏆 Standings", "🥎 Batting Leaders", "💪 Pitching Leaders"]
    )

    with t_scores:
        st.subheader("Recent Results")
        st.markdown('<p class="source-note">Source: TheSportsDB · League ID 4830</p>', unsafe_allow_html=True)
        past = fetch_tsdb(KBO_LEAGUE_ID, "past")
        render_scores(past, "KBO")
        st.subheader("Upcoming Games")
        upcoming = fetch_tsdb(KBO_LEAGUE_ID, "next")
        render_scores(upcoming, "KBO")

    with t_stand:
        st.subheader("2026 KBO Standings")
        st.markdown('<p class="source-note">Source: Wikipedia 2026 KBO season · Updated throughout season</p>', unsafe_allow_html=True)
        with st.spinner("Loading standings..."):
            df_stand = fetch_standings_flashscore("KBO")
        if df_stand is not None and not df_stand.empty:
            render_df(df_stand)
        else:
            st.warning("Could not load standings table automatically.")
        fallback_links("KBO")

    with t_bat:
        st.subheader("2026 KBO Batting Leaders")
        st.markdown('<p class="source-note">Source: FanGraphs · Updated nightly</p>', unsafe_allow_html=True)
        with st.spinner("Loading KBO batting stats from FanGraphs..."):
            df_bat = fetch_fg_table(FG_KBO_BAT)
        if df_bat is not None and not df_bat.empty:
            col1, col2 = st.columns(2)
            with col1:
                stat_cols = [c for c in df_bat.columns if c not in ("#", "Name", "Team", "Age")]
                sort_col = st.selectbox("Sort by:", stat_cols, index=stat_cols.index("AVG") if "AVG" in stat_cols else 0, key="kbo_bat_sort")
            with col2:
                max_rows = st.slider("Rows:", 10, 100, 30, key="kbo_bat_rows")
            df_sorted = safe_sort(df_bat, sort_col)
            df_sorted.insert(0, "#", range(1, len(df_sorted) + 1))
            render_df(df_sorted, max_rows)
        else:
            st.warning("Could not load FanGraphs KBO batting data.")
        fallback_links("KBO")

    with t_pit:
        st.subheader("2026 KBO Pitching Leaders")
        st.markdown('<p class="source-note">Source: FanGraphs · Updated nightly</p>', unsafe_allow_html=True)
        with st.spinner("Loading KBO pitching stats from FanGraphs..."):
            df_pit = fetch_fg_table(FG_KBO_PIT)
        if df_pit is not None and not df_pit.empty:
            col1, col2 = st.columns(2)
            with col1:
                stat_cols_p = [c for c in df_pit.columns if c not in ("#", "Name", "Team", "Age")]
                default_p = "ERA" if "ERA" in stat_cols_p else stat_cols_p[0] if stat_cols_p else None
                sort_col_p = st.selectbox("Sort by:", stat_cols_p, index=stat_cols_p.index(default_p) if default_p in stat_cols_p else 0, key="kbo_pit_sort")
            with col2:
                max_rows_p = st.slider("Rows:", 10, 100, 30, key="kbo_pit_rows")
            low_is_better = sort_col_p in {"ERA", "WHIP", "BB", "BB9", "BB/9", "HR", "HR9"}
            df_pit_sorted = safe_sort(df_pit, sort_col_p, ascending=low_is_better)
            df_pit_sorted.insert(0, "#", range(1, len(df_pit_sorted) + 1))
            render_df(df_pit_sorted, max_rows_p)
        else:
            st.warning("Could not load FanGraphs KBO pitching data.")
        fallback_links("KBO")

# ══════════════════════════════════════════════════════════════════════════════
# NPB
# ══════════════════════════════════════════════════════════════════════════════
with npb_tab:
    t_npb_scores, t_npb_stand, t_npb_bat, t_npb_pit = st.tabs(
        ["⚾ Scores", "🏆 Standings", "🥎 Batting Leaders", "💪 Pitching Leaders"]
    )

    with t_npb_scores:
        st.subheader("Recent Results")
        st.markdown('<p class="source-note">Source: TheSportsDB · League ID 4591 (Nippon Baseball League) ✅</p>', unsafe_allow_html=True)
        past_npb = fetch_tsdb(NPB_LEAGUE_ID, "past")
        render_scores(past_npb, "NPB")
        st.subheader("Upcoming Games")
        upcoming_npb = fetch_tsdb(NPB_LEAGUE_ID, "next")
        render_scores(upcoming_npb, "NPB")

    with t_npb_stand:
        st.subheader("2026 NPB Standings")
        st.markdown('<p class="source-note">Source: Wikipedia 2026 NPB season · Central & Pacific leagues</p>', unsafe_allow_html=True)
        with st.spinner("Loading NPB standings..."):
            npb_stands = fetch_npb_standings_detailed()
        if npb_stands:
            for league_name, df_s in npb_stands.items():
                st.markdown(f"**{league_name}**")
                render_df(df_s)
        else:
            st.warning("Could not load NPB standings automatically.")
            st.info("NPB Wikipedia page may use a different URL format mid-season. Try the direct links below.")
        fallback_links("NPB")

    with t_npb_bat:
        st.subheader("2026 NPB Batting Leaders")
        st.markdown('<p class="source-note">Source: FanGraphs · Updated nightly</p>', unsafe_allow_html=True)
        with st.spinner("Loading NPB batting stats from FanGraphs..."):
            df_npb_bat = fetch_fg_table(FG_NPB_BAT)
        if df_npb_bat is not None and not df_npb_bat.empty:
            col1, col2 = st.columns(2)
            with col1:
                stat_cols_nb = [c for c in df_npb_bat.columns if c not in ("#", "Name", "Team", "Age")]
                default_nb = "AVG" if "AVG" in stat_cols_nb else stat_cols_nb[0] if stat_cols_nb else None
                sort_nb = st.selectbox("Sort by:", stat_cols_nb, index=stat_cols_nb.index(default_nb) if default_nb in stat_cols_nb else 0, key="npb_bat_sort")
            with col2:
                rows_nb = st.slider("Rows:", 10, 100, 30, key="npb_bat_rows")
            df_npb_bat_s = safe_sort(df_npb_bat, sort_nb)
            df_npb_bat_s.insert(0, "#", range(1, len(df_npb_bat_s) + 1))
            render_df(df_npb_bat_s, rows_nb)
        else:
            st.warning("Could not load FanGraphs NPB batting data.")
        fallback_links("NPB")

    with t_npb_pit:
        st.subheader("2026 NPB Pitching Leaders")
        st.markdown('<p class="source-note">Source: FanGraphs · Updated nightly</p>', unsafe_allow_html=True)
        with st.spinner("Loading NPB pitching stats from FanGraphs..."):
            df_npb_pit = fetch_fg_table(FG_NPB_PIT)
        if df_npb_pit is not None and not df_npb_pit.empty:
            col1, col2 = st.columns(2)
            with col1:
                stat_cols_np = [c for c in df_npb_pit.columns if c not in ("#", "Name", "Team", "Age")]
                default_np = "ERA" if "ERA" in stat_cols_np else stat_cols_np[0] if stat_cols_np else None
                sort_np = st.selectbox("Sort by:", stat_cols_np, index=stat_cols_np.index(default_np) if default_np in stat_cols_np else 0, key="npb_pit_sort")
            with col2:
                rows_np = st.slider("Rows:", 10, 100, 30, key="npb_pit_rows")
            low_np = sort_np in {"ERA", "WHIP", "BB", "BB9", "BB/9", "HR", "HR9"}
            df_npb_pit_s = safe_sort(df_npb_pit, sort_np, ascending=low_np)
            df_npb_pit_s.insert(0, "#", range(1, len(df_npb_pit_s) + 1))
            render_df(df_npb_pit_s, rows_np)
        else:
            st.warning("Could not load FanGraphs NPB pitching data.")
        fallback_links("NPB")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<span class="updated-tag">Sources: TheSportsDB (scores) · FanGraphs (batting/pitching) · Wikipedia (standings) · Scores cache 5min · Stats cache 30min</span>',
    unsafe_allow_html=True,
)
