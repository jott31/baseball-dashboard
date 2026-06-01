# ⚾ Asia Baseball Dashboard

A Streamlit dashboard for KBO and NPB stats, scores, and standings.

## Data Sources
- **Scores/Schedule**: TheSportsDB (free, no key needed)
- **Standings**: Baseball Reference
- **Batting/Pitching Leaders**: FanGraphs + Baseball Reference

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Deploy to Streamlit Cloud (Free)

1. Push this folder to a GitHub repo
2. Go to share.streamlit.io
3. Sign in with GitHub
4. Select your repo → `app.py` → Deploy

Your app gets a public URL like:
`https://yourusername-baseball-dashboard.streamlit.app`

Add that URL to your iPhone Home Screen via Safari → Share → Add to Home Screen.

## Add to iPhone Home Screen

1. Open your Streamlit Cloud URL in Safari
2. Tap the Share button (box with arrow)
3. Tap "Add to Home Screen"
4. Name it "Asia Baseball" → Add
