# TikTok Mass Reporter v8.1 — FEATURES

## Core Reporting

✓ **Video Reporting** — HTTP POST to TikTok API endpoint
✓ **Multiple Categories** — Sexual (2), Violence (3), Hate (5), etc.
✓ **Batch Reporting** — Send 1-1000+ reports in one session
✓ **Real-time Feedback** — Console shows each report status
✓ **CSV Logging** — All reports stored with timestamp, device, proxy, status

## Device Management

✓ **Device Fingerprinting** — Random 8-char ID per device
✓ **Persistent Storage** — Device saved to `fingerprint.json`
✓ **Device Rotation** — New device every 10 reports
✓ **Device Listing** — View all generated devices

## Proxy Management

✓ **Public Proxy Fetch** — Download free SOCKS5 proxies automatically
✓ **Proxy Rotation** — Different proxy per request
✓ **Failure Tracking** — Records proxy failures, prefers working ones
✓ **Proxy Stats** — Uses/failures/success per proxy
✓ **Proxy Clearing** — Reset and re-fetch proxy list anytime
✓ **Multi-protocol** — SOCKS5, HTTP, HTTPS support

## Session Management

✓ **Cookie Extraction** — Auto-captures TikTok cookies from responses
✓ **Cookie Persistence** — Stores cookies in `session_cookies.json`
✓ **Cookie Reuse** — Automatically includes cookies in subsequent requests
✓ **Cookie Viewing** — List captured session cookies

## User-Agent Rotation

✓ **4 Random UAs** — Different browser/OS combinations
✓ **Per-Request Rotation** — Changes on every request
✓ **Browser Emulation** — Chrome, Firefox, Safari, Chromium variants

## Behavioral Intelligence

✓ **Natural Delays** — 0.8-1.5s random between reports (not robotic)
✓ **Rate Limiting** — 0.5s minimum between requests
✓ **Intelligent Rotation** — Timing-aware device/proxy changes
✓ **Error Handling** — Timeout, connection error, exception handling

## Response Diagnostics

✓ **Status Codes** — Shows HTTP 200, 403, 429, timeout, etc.
✓ **Response Parsing** — Detects JSON, HTML, captcha, firewall blocks
✓ **Detailed Messages** — success, json_parse_failed, html_page, firewall_blocked, captcha_required, rate_limited
✓ **Real Response Body** — Shows actual TikTok response text

## Statistics & Analytics

✓ **Live Stats** — Success rate, fail rate, reports/sec
✓ **Status Breakdown** — Count by HTTP status code (200, 403, etc.)
✓ **Message Breakdown** — Count by response type
✓ **Category Breakdown** — Count by report category (2, 3, 5, etc.)
✓ **Timing** — Elapsed time, speed (reports/second)

## Data Export

✓ **CSV Export** — Comma-separated reports log
✓ **Columns** — timestamp, device_id, video_id, owner_id, category, status_code, response_msg, proxy_used
✓ **CSV Viewing** — List row count and location
✓ **Persistent Log** — Accumulates across multiple runs

## Thread Safety

✓ **Concurrent Operations** — Thread-safe file writes
✓ **Lock Mechanisms** — Protects CSV, JSON, cookie files
✓ **Ready for Multi-threading** — Foundation for future parallelization

## Menu System

✓ **9 Options** — Full control of all features
✓ **Clear Navigation** — Menu shows at each step
✓ **Input Validation** — Checks required fields
✓ **Error Messages** — Clear feedback on failures

## File Management

| File | Purpose |
|------|---------|
| `reports.csv` | All reports log |
| `fingerprint.json` | Device storage |
| `proxies_with_stats.json` | Proxy list & stats |
| `session_cookies.json` | Captured TikTok cookies |

## Menu Options

```
[1] Report Video
    - Video ID input
    - Owner ID input
    - Category selection
    - Report count input
    - Live console feedback

[2] Fetch Proxies
    - Auto-downloads public SOCKS5 proxies
    - Reports count added

[3] List Proxies
    - Shows all loaded proxies
    - Per-proxy stats (uses, success, failures)
    - Top 15 shown, with count of remaining

[4] Clear Proxies
    - Removes all stored proxies
    - Clean slate for new fetch

[5] View Stats
    - Total reports sent
    - Success vs failed count
    - Reports/second speed
    - Breakdown by status code
    - Breakdown by response message
    - Breakdown by category

[6] List Devices
    - Shows all generated device IDs
    - Device tracking info

[7] Export CSV
    - Confirms reports.csv location
    - Shows row count

[8] View Cookies
    - Lists captured TikTok session cookies
    - Shows top 5, with count of remaining

[9] Exit
    - Clean shutdown
```

## Performance Characteristics

- **Speed**: ~1 report/second (with 0.8-1.5s natural delay)
- **Throughput**: 100 reports ≈ 100-150 seconds
- **Device Rotation**: Every 10 reports
- **Proxy Rotation**: Every request (if loaded)
- **UA Rotation**: Every request
- **Memory**: ~50-100 MB for 1000+ reports in session
- **CSV Size**: ~200 bytes per report

## Reliability Features

✓ Automatic retry on connection errors
✓ Timeout handling (10 second timeout per request)
✓ Proxy failure tracking (avoids dead proxies)
✓ Session persistence (maintains TikTok cookies)
✓ Persistent device IDs (survives restarts)
✓ CSV integrity (atomic writes with locks)

## Network Features

✓ HTTP/HTTPS support
✓ SOCKS5 proxy support
✓ Connection pooling
✓ Retry logic (3 retries with backoff)
✓ Custom headers (referer, user-agent, etc.)
✓ Accept language negotiation

## Security Features

✓ **No API Keys Stored** — Only uses public TikTok endpoint
✓ **Session Isolation** — Each device/proxy combo isolated
✓ **Local Storage Only** — Data never sent outside
✓ **No Credentials** — No passwords or tokens required
✓ **Cookie-based** — Uses TikTok's own session management

---

**Full v8.1 feature set. Production-ready.**
