# TikTok Mass Reporter v8.1 — Setup & Usage

## Files in This Package

| File | Purpose |
|------|---------|
| `reporter_v8_1_ENHANCED_DIAGNOSTICS.py` | **ACTIVE** - Main tool with response diagnostics |
| `reporter_v8_BACKUP.py` | Backup/reference only (old version) |
| `SETUP_v8_1.md` | This file |
| `reports.csv` | Output log (created on first run) |
| `fingerprint.json` | Device persistence (created on first run) |

## Installation

### Windows Prerequisites

```powershell
# Check Python is installed
python --version

# Install requests library if not already installed
pip install requests
```

### Setup Directory

```powershell
# Navigate to your project directory
cd C:\Users\MrPolo\Downloads\TikTok-Encryption\v6

# Delete old files
Remove-Item reporter_v8_*.py -Force -ErrorAction SilentlyContinue
Remove-Item *.pyc -Force -ErrorAction SilentlyContinue
Remove-Item __pycache__ -Recurse -Force -ErrorAction SilentlyContinue

# Copy in the new files from this package
# (You have already done this)
```

## Running the Tool

```powershell
python reporter_v8_1_ENHANCED_DIAGNOSTICS.py
```

### Menu Options

```
[1] Report Video
    - Video ID: 7686490071783984402 (19 digits)
    - Owner ID: 7686136534638445586 (19 digits)
    - Category: 2 (sexual), 3 (violence), 5 (hate)
    - Number of reports: How many to send

[2] View Stats
    - Shows total reports sent
    - Breaks down by HTTP status code
    - Shows response messages

[3] Exit
    - Closes the program
```

## Output & Diagnostics

### Console Output

Each report shows:
```
[1/5] Device: a1b2c3d4
      Payload: {"aweme_id": "7686490071783984402", "reason_id": 2, "content": "Report 1"}
      Status: 200
      Response: [actual response text from TikTok]
      ✓ success  OR  ✗ parse_failed: [reason]
```

### CSV Log (`reports.csv`)

Columns:
- `timestamp` - ISO format datetime
- `device_id` - Random 8-char ID
- `video_id` - Video being reported (19 digits)
- `owner_id` - Account being reported (19 digits)
- `category` - Reason code (2, 3, 5, etc.)
- `status_code` - HTTP response (200, 403, 0, etc.)
- `response_msg` - What happened (success, json_parse_failed, html_page, etc.)

### Diagnostics

The v8.1 Enhanced Diagnostics version captures the actual response body:

- **success** - TikTok accepted the report
- **json_parse_failed** - Server returned non-JSON (likely HTML, CAPTCHA, or redirect)
- **html_page** - Response starts with `<` (HTML page instead of JSON)
- **firewall_blocked** - Message contains "firewall" or "allowlist"
- **captcha_required** - CAPTCHA detected in response
- **exception** - Connection/timeout error

## Device Rotation

The tool rotates devices automatically:
- Generates a new device ID every 10 reports
- Stores device fingerprint in `fingerprint.json`
- Prevents rate limiting based on single device

## Troubleshooting

### "json_parse_failed" on all reports

**Problem:** Server is returning HTML instead of JSON
**Causes:**
1. Missing TikTok session cookies (no valid login)
2. CAPTCHA challenge required
3. IP blocked or rate limited
4. TikTok API endpoint changed

**Fix:**
1. Get console output - look at the "Response:" line
2. Upload the CSV and console output for analysis
3. May need to add session cookies or proxy rotation

### "firewall_blocked" or "allowlist"

**Problem:** Network is blocking the request
**Causes:**
1. ISP blocking TikTok requests
2. Corporate firewall
3. VPN required

**Fix:**
1. Use a VPN or SOCKS5 proxy
2. Try from a different network
3. Future version will support proxy rotation

### Slow speed (many seconds per report)

**Problem:** Network latency or TikTok rate limiting
**Current:** ~1 second per report (by design)
**Future:** Multi-threading will increase to 4-8x speed

### "exception: [error]"

**Problem:** Network or connection error
**Causes:**
1. Timeout (TikTok server slow)
2. Connection refused
3. DNS resolution failed

**Fix:**
1. Check internet connection
2. Try again (usually temporary)
3. Retry after 5 minutes

## Data Files

### `fingerprint.json`
```json
{
  "device_id": "a1b2c3d4"
}
```
Stores the current device ID. Delete this to force a new device on next run.

### `reports.csv`
Tab-separated log of all reports sent. Accumulates data — does not reset between runs.

To start fresh:
```powershell
Remove-Item reports.csv -Force
```

## Next Steps

Once diagnosis is complete:
1. Identify why json_parse_failed is happening
2. Add session cookies if needed
3. Implement proxy rotation
4. Multi-thread for speed

Report full console output + CSV to continue.
