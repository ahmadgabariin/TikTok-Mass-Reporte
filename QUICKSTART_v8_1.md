# TikTok Mass Reporter v8.1 — QUICKSTART

## Download These Files

1. `reporter_v8_1_ENHANCED_DIAGNOSTICS.py` — **MAIN TOOL**
2. `CLEANUP_OLD_FILES.ps1` — Setup script
3. `SETUP_v8_1.md` — Full guide
4. `FEATURES_v8_1.md` — Features list
5. `QUICKSTART_v8_1.md` — This file

## One-Time Setup

```powershell
# Go to your directory
cd C:\Users\MrPolo\Downloads\TikTok-Encryption\v6

# Copy all 5 files to this directory

# Run cleanup
.\CLEANUP_OLD_FILES.ps1
# Type: yes

# Wait for completion
```

## Run Tool

```powershell
python reporter_v8_1_ENHANCED_DIAGNOSTICS.py
```

## First Use Workflow

```
Menu appears with 9 options

[2] → Fetch Proxies
      (downloads free SOCKS5 proxies)

[3] → List Proxies
      (verify loaded, see stats)

[1] → Report Video
      Video ID: 7686490071783984402
      Owner ID: 7686136534638445586
      Category: 2
      Reports: 100
      (runs 100 reports using proxies)

[5] → View Stats
      (shows success rate, speed, breakdown)

[8] → View Cookies
      (shows captured TikTok session cookies)

[7] → Export CSV
      (confirms reports.csv saved)

[9] → Exit
```

## Output Files Created

- `reports.csv` — Log of all reports (timestamp, device, status, proxy used)
- `fingerprint.json` — Device IDs (persisted across runs)
- `proxies_with_stats.json` — Proxy list with success/failure stats
- `session_cookies.json` — TikTok session cookies (auto-captured)

## Speed & Behavior

- 1 report ≈ 1 second (includes random delays)
- 100 reports ≈ 1.5-2 minutes
- Device rotates every 10 reports (prevents rate limiting)
- Proxy rotates per request (if proxies loaded)
- User-Agent rotates per request (4 variants)
- Cookies auto-captured and reused

## Troubleshooting

**"json_parse_failed"** — Proxy blocked or session invalid
→ Try [4] to clear proxies, then re-fetch [2]

**"captcha_required"** — TikTok asking for CAPTCHA
→ Wait 5-10 minutes, retry, or use different proxies

**"firewall_blocked"** — Network blocking requests
→ Use [2] to load proxies

**Slow speed** — Network latency
→ Check [3] proxy stats, try different proxies

**No proxies work** — Proxies dead/blocked
→ [4] Clear proxies, [2] Fetch new batch

## Next Steps

1. Run 100-200 reports with proxies
2. Check stats [5]
3. Upload reports.csv for analysis
4. Adjust strategy based on success rate

---

**That's it. Tool is ready to go.**
