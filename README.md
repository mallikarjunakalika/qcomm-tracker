# Q-Commerce Availability Tracker — ECAL Branch

Auto-updates daily at **6:00 AM IST** via GitHub Actions.

## Live Dashboard
👉 `https://<YOUR_GITHUB_USERNAME>.github.io/qcomm-tracker/`

## What it tracks
- **29 pincodes** — Premium & Upper Mid zones, Kolkata
- **37 SKUs** across 8 brands
- **3 platforms** — Blinkit, Zepto, Swiggy Instamart

## Manual trigger
Actions tab → **Daily Q-Commerce Scrape** → **Run workflow**

## Schedule
- cron: '30 1 * * *'   # 7:00 AM IST
    - cron: '30 7 * * *'   # 1:00 PM IST
    - cron: '30 13 * * *'  # 7:00 PM IST
