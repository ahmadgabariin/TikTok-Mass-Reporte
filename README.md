# TikTok Mass Reporter v8.3

Automated TikTok video reporting tool using device randomization and multi-threading.

## Features

- **Unique Device IDs**: Each report from a different spoofed device
- **Multi-Category Support**: All 13 TikTok violation categories
- **Concurrent Reporting**: 50-thread execution for speed
- **Proxy Support**: Optional SOCKS5 proxy rotation
- **CSV Logging**: Full audit trail of all reports
- **No Blocks**: 10,000+ reports tested, 100% HTTP 200 success

## Installation

```bash
git clone https://github.com/ahmadgabariin/TikTok-Mass-Reporter.git
cd TikTok-Mass-Reporter
pip install -r requirements.txt
```

## Usage

```bash
python reporter_v8_1_ENHANCED_DIAGNOSTICS.py
```

**Note:** On Windows, use `python`. On Linux/Mac, use `python3` if `python` is not available.

### Menu Options

```
╔════════════════════════════════╗
║  TikTok Mass Reporter v8.3     ║
║  @#9002111185000               ║
╚════════════════════════════════╝

[1] Report a video
[2] Proxy settings
[3] About
[0] Exit
```

### Report a Video (Option 1)

**Required Inputs:**

- `Video ID` (19 digits)
  - Example: `7123456789012345678`
  - From URL: `https://www.tiktok.com/@user/video/7123456789012345678`

- `Owner ID` (optional, 19 digits)
  - Leave blank if unsure

- `Number of reports` (1-1000)
  - Example: `200`

- `Use proxies? (y/n)`
  - `n` = direct IP (faster, recommended)
  - `y` = free SOCKS5 (slower, less reliable)

### Example Run

```
$ python reporter_v8_1_ENHANCED_DIAGNOSTICS.py

Select: 1

Video ID: 7123456789012345678
Owner ID: [press enter]
Number of reports: 200
Use proxies (y/n): n

[1/200] Device: 74b05f55 | Category: 9 (Suicide or self-harm) | Status: 200 | ✓
[2/200] Device: 0936b991 | Category: 3 (Illegal activity) | Status: 200 | ✓
...
[200/200] Device: cab4b226 | Category: 10 (Terrorism) | Status: 200 | ✓

✓ All 200 reports completed
```

## Files

- `reporter_v8_1_ENHANCED_DIAGNOSTICS.py` - Main reporting tool
- `getproxies_pro.py` - Proxy fetcher (optional)
- `requirements.txt` - Python dependencies
- `reports.csv` - Log of all reports sent

## Requirements

- Python 3.8+
- requests
- urllib3

Install:
```bash
pip install -r requirements.txt
```

## Output (reports.csv)

```
timestamp,device_id,video_id,owner_id,category,status_code
2026-09-21T10:30:45.123Z,74b05f55,7123456789012345678,owner_id,9,200
2026-09-21T10:30:46.456Z,0936b991,7123456789012345678,owner_id,3,200
```

## Report Categories (1-13)

1. Spam or misleading
2. Sexual content / Nudity
3. Illegal activity / Sale of illegal goods
4. Child safety
5. Harassment or bullying
6. Hateful behavior or symbols
7. Violent or repulsive content
8. Eating disorder
9. Suicide or self-harm
10. Terrorism or violent extremism
11. False information / Misinformation
12. Infringement of intellectual property
13. Minors in dangerous situations

## Status Codes

- `200`: Report accepted ✓
- `429`: Rate limited (tool auto-retries with backoff)
- `403`: Blocked (rare, means device/IP flagged)
- Other: Connection error (tool retries 5 times)

## Proxy Mode

Optional. Free SOCKS5 proxies provided by tool, but they die quickly after validation.

1. Select menu option `[2] Proxy settings`
2. Choose `[1] Fetch free SOCKS5 proxies`
3. Tool downloads and tests proxies
4. Return to main menu, select `[1] Report a video`
5. When prompted, select `y` for proxies

**Note:** Free proxies slow down execution significantly. Direct IP recommended.

## Moderation Timeline

TikTok moderation:
- **24-48 hours**: Fast review (clear violation)
- **3-5 days**: Standard timeline
- **7+ days**: Backlog or edge case

Video deletion is NOT instant. Check back in 5 days.

## Troubleshooting

**"ModuleNotFoundError: No module named 'requests'"**
```bash
pip install requests
```

**"Connection timeout"**
- Check internet connection
- If using proxies, they may be dead

**"Video ID not found"**
- Ensure you copied all 19 digits
- Example: `7686490071783984402` (not `7686490071783984`)

**"Reports all status 429"**
- Too many requests from your IP
- Wait 30 minutes before retrying

**"All status 403"**
- Your IP is blocked
- Use proxy mode or wait 24 hours

## Architecture

- **Threading**: 50 concurrent threads via ThreadPoolExecutor
- **Device IDs**: UUID4 truncated to 8 chars (unique per report)
- **Categories**: Random selection from 1-13
- **Retry Logic**: 5 attempts per report, backoff 3-7 seconds
- **Exit**: Hard exit via `os._exit(0)` (avoids executor shutdown hang)

## Endpoint

```
POST https://www.tiktok.com/aweme/v2/aweme/feedback/

Payload:
{
  "aweme_id": "7123456789012345678",
  "reason_id": 9
}
```

## Performance

- **Speed**: ~200 reports in 2 seconds (50 threads)
- **Success Rate**: 100% HTTP 200 (10,000+ reports tested)
- **No Blocks**: Zero IP/device blocks in testing
- **Deduplication**: TikTok may deduplicate reports on same video

## Disclaimer

**For educational purposes only.** This tool demonstrates TikTok's reporting API mechanics. Users are responsible for complying with TikTok's Terms of Service and all applicable laws. Misuse of this tool to file false reports or harass users is prohibited.

## License

MIT License. See LICENSE file for details.

## Support

For issues or questions, open an issue on GitHub.
