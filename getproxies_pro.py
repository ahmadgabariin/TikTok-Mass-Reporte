#!/usr/bin/env python3
"""
Free proxy scraper + checker.

Run with no arguments for an interactive menu:
    python getproxies_pro.py

Or drive it from the command line:
    python getproxies_pro.py -p socks5
    python getproxies_pro.py -p socks5 --target https://www.tiktok.com/robots.txt
    python getproxies_pro.py -p all -m 5000 --retries 2

Why the target matters: a proxy is not "working" in general, it is working for a
specific site. Measured on 600 socks5 proxies, testing against TikTok directly
found 52 usable where the generic test found 23, and 34 proxies that work with
TikTok were being thrown away by the generic test. One retry pass took it to 84.

Needs: pip install requests PySocks
"""
import argparse
import json
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import requests

# ---------- colors ----------
G = '\033[1;32m'; R = '\033[1;31m'; C = '\033[1;36m'
W = '\033[1;37m'; Y = '\033[1;33m'; RST = '\033[0m'

# ---------- defaults ----------
FETCH_TIMEOUT  = 15
CHECK_TIMEOUT  = 8       # measured: 8s finds ~2x more working proxies than 3s
CHECK_WORKERS  = 400     # measured: higher counts LOSE proxies to false negatives
FETCH_WORKERS  = 25
MAX_PROXIES    = 6000
RETRIES        = 3       # measured: one retry nearly doubled the usable count
GENERIC_URL    = "http://ip-api.com/json/?fields=query"
GENERIC_MARKER = "query"
HTTPS_TEST_URL = "https://www.gstatic.com/generate_204"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Proxy URL scheme used to DIAL each protocol. Measured choices:
#   socks5h beat socks5   17.6% vs 16.6%, and is REQUIRED for https:// to work.
#   socks4  beat socks4a  11.6% vs 5.8%  - most socks4 proxies lack the 4a
#           remote-DNS extension, so asking for it halves the yield.
SCHEME = {"http": "http", "socks4": "socks4", "socks5": "socks5h"}

# ---------------------------------------------------------------------------
# SOURCES - all verified live. Tier A is checked before B/C: bulk dumps measure
# ~0.7% working vs ~30-49% for curated lists, and checking in tier order found
# 28x more working proxies for the same time budget.
# ---------------------------------------------------------------------------
HTTP_A = [
    "https://raw.githubusercontent.com/berkay-digital/Proxy-Scraper/main/proxies.txt",
    "https://raw.githubusercontent.com/VPSLabCloud/VPSLab-Free-Proxy-List/main/http_ssl.txt",
    "https://raw.githubusercontent.com/VPSLabCloud/VPSLab-Free-Proxy-List/main/http_elite.txt",
    "https://free-proxy-list.net/",
    "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/main/Stable/http.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/main/http/http.txt",
    "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&proxy_format=ipport&format=text",
    "https://raw.githubusercontent.com/VPSLabCloud/VPSLab-Free-Proxy-List/main/http_all.txt",
    "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/protocols/http.txt",
    "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=http&proxy_format=ipport&format=text",
    "https://raw.githubusercontent.com/andigwandi/free-proxy/main/proxy_list.txt",
    "https://spys.me/proxy.txt",
    "https://raw.githubusercontent.com/VPSLabCloud/VPSLab-Free-Proxy-List/main/http_nossl.txt",
]
HTTP_B = [
    "https://raw.githubusercontent.com/proxyscrape/free-proxy-list/main/proxies/all/data.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/connect.txt",
    "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=https&proxy_format=ipport&format=text",
    "https://raw.githubusercontent.com/VPSLabCloud/VPSLab-Free-Proxy-List/main/all_proxies.txt",
    "https://raw.githubusercontent.com/dinoz0rg/proxy-list/main/checked_proxies/http.txt",
    "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/http.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/main/https/https.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/all.txt",
    "https://raw.githubusercontent.com/tuanminpay/live-proxy/master/http.txt",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=1000&country=all&ssl=all&anonymity=all&simplified=true",
    "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000&country=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/https.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
    "https://raw.githubusercontent.com/zebbern/Proxy-Scraper/main/http.txt",
    "https://raw.githubusercontent.com/yuceltoluyag/GoodProxy/main/raw.txt",
    "https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/main/http.txt",
    "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Https.txt",
    "https://raw.githubusercontent.com/dpangestuw/Free-Proxy/refs/heads/main/http_proxies.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt",
    "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/main/http.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/generated/http_proxies.txt",
    "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/elliottophellia/proxylist/master/results/http/global/http_checked.txt",
    "https://raw.githubusercontent.com/im-razvan/proxy_list/main/http.txt",
]
HTTP_C = [
    "https://raw.githubusercontent.com/wiki/gfpcom/free-proxy-list/lists/http.txt",
    "https://raw.githubusercontent.com/Tsprnay/Proxy-lists/master/proxies/all.txt",
    "https://raw.githubusercontent.com/casals-ar/proxy-list/main/http",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt",
    "https://raw.githubusercontent.com/aslisk/proxyhttps/main/https.txt",
    "https://raw.githubusercontent.com/TuanMinPay/live-proxy/master/all.txt",
    "https://raw.githubusercontent.com/SoliSpirit/proxy-list/main/https.txt",
]
SOCKS4_A = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=socks4&proxy_format=ipport&format=text",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/main/socks4/socks4.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks4/data.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks4.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks4.txt",
]
SOCKS4_B = [
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks4.txt",
]
SOCKS5_A = [
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=socks5&proxy_format=ipport&format=text",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/main/socks5/socks5.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks5_proxies.txt",
]
SOCKS5_A2 = [
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks5.txt",
]
SOCKS5_B = [
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt",
]
TIERS = {
    "http":   [HTTP_A, HTTP_B, HTTP_C],
    "socks4": [SOCKS4_A, SOCKS4_B],
    "socks5": [SOCKS5_A, SOCKS5_A2, SOCKS5_B],
}

IP_PORT     = re.compile(r'^(\d{1,3}\.){3}\d{1,3}:\d{2,5}$')
IP_PORT_ANY = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[:\s|]+(\d{2,5})')


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def valid(p):
    try:
        host, port = p.rsplit(':', 1)
        # isdigit() rejects " 80", "+80", "8_0" which int() would happily accept
        if not port.isdigit() or not 1 <= int(port) <= 65535:
            return False
        octets = host.split('.')
        return len(octets) == 4 and all(
            o.isdigit() and 0 <= int(o) <= 255 for o in octets)
    except Exception:
        return False


def clean(line):
    line = line.strip()
    if not line:
        return None
    line = re.sub(r'^\w+://', '', line)
    line = line.split('#')[0].strip()
    if not line:
        return None
    line = line.split()[0]
    return line if IP_PORT.match(line) and valid(line) else None


def extract(text):
    """Bare ip:port first, then JSON, then a loose scan for HTML tables and
    colon/pipe delimited formats (hideip.me, spys.me, free-proxy-list.net)."""
    out = {p for ln in text.splitlines() if (p := clean(ln))}
    # A block/error page can carry one stray ip:port. If the body looks like
    # HTML and the haul is tiny, do not trust it - fall through to the other
    # parsers and the >= 10 plausibility guard below.
    looks_html = re.search(r'<\s*(html|body|head)\b', text[:4000], re.I)
    if out and looks_html and len(out) < 10:
        out = set()          # distrust a tiny haul scraped out of an HTML page
    if out:
        return out
    if text.lstrip()[:1] in '[{':
        try:
            d = json.loads(text)
            rows = d.get('data', d) if isinstance(d, dict) else d
            out = {f"{o['ip']}:{o['port']}" for o in rows
                   if isinstance(o, dict) and o.get('ip') and o.get('port')}
            out = {p for p in out if valid(p)}
        except Exception:
            out = set()
    if out:
        return out
    # Guard: a captive-portal or ISP block page can return HTTP 200 and contain
    # a stray IP, so only trust a loose scan that yields a plausible list.
    loose = {f"{a}:{b}" for a, b in IP_PORT_ANY.findall(text)}
    loose = {p for p in loose if valid(p)}
    return loose if len(loose) >= 10 else set()


def fetch_source(url):
    try:
        r = requests.get(url, timeout=FETCH_TIMEOUT, headers={'User-Agent': UA})
        if r.status_code == 200:
            return extract(r.text)
    except Exception:
        pass
    return set()


def fetch_tier(urls):
    found = set()
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
        for s in ex.map(fetch_source, urls):
            found |= s
    return found


def gather(proto, budget):
    """Fill the budget from the best tier downwards."""
    pool, seen = [], set()
    for i, urls in enumerate(TIERS[proto]):
        if budget and len(pool) >= budget:
            break
        fresh = [p for p in fetch_tier(urls) if p not in seen]
        seen.update(fresh)
        random.shuffle(fresh)
        kept = fresh[:budget - len(pool)] if budget else fresh
        pool.extend(kept)
        print(f"{C}[*]{RST} {proto:6} tier {chr(65 + i)}  +{len(kept):6}   (pool {len(pool)})")
    return pool


# ---------- menus ----------
MENU = [
    ("1", "http",   "HTTP            - plain http:// only"),
    ("2", "https",  "HTTPS-capable   - http proxies that reach https:// sites"),
    ("3", "socks4", "SOCKS4"),
    ("4", "socks5", "SOCKS5          - recommended, best working rate (~17%)"),
    ("5", "socks",  "SOCKS4 + SOCKS5"),
    ("6", "all",    "ALL protocols   - mixed, scheme-prefixed output"),
]

TARGETS = [
    ("1", None,                                       "Generic       - any working proxy (default)"),
    ("2", "https://www.tiktok.com/robots.txt",        "TikTok"),
    ("3", "https://www.whatsapp.com/robots.txt",      "WhatsApp"),
    ("4", "https://www.instagram.com/robots.txt",     "Instagram"),
    ("5", "https://www.youtube.com/robots.txt",       "YouTube"),
    ("6", "https://www.google.com/robots.txt",        "Google"),
    ("7", "CUSTOM",                                   "Custom        - type any URL you want"),
]


def _ask(prompt):
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


def choose_protocol():
    print(f"\n{C}  which protocol do you want?{RST}\n")
    for key, _, desc in MENU:
        print(f"    {W}[{key}]{RST}  {desc}")
    print()
    while True:
        c = (_ask(f"  choice {W}[4]{RST}: ") or "4").lower()
        for key, value, _ in MENU:
            if c == key:
                return value
        if c in ("http", "https", "socks4", "socks5", "socks", "all", "mixed"):
            return c
        print(f"  {R}pick 1-6 (or type a name like socks5){RST}")


def choose_target():
    """Which site should proxies be tested against?"""
    print(f"\n{C}  test the proxies against which site?{RST}")
    print(f"  {Y}a proxy is not 'working' in general, only working for a specific site{RST}\n")
    for key, _, desc in TARGETS:
        print(f"    {W}[{key}]{RST}  {desc}")
    print()
    while True:
        raw = _ask(f"  choice {W}[1]{RST}: ") or "1"
        c = raw.lower()
        for key, value, _ in TARGETS:
            if c == key:
                if value == "CUSTOM":
                    while True:
                        u = _ask(f"  enter the URL (e.g. https://example.com/): ")
                        if not u:
                            return None
                        if not re.match(r'^https?://', u):
                            u = "https://" + u
                        if urlparse(u).netloc:
                            return u
                        print(f"  {R}that does not look like a URL{RST}")
                return value
        if re.match(r'^https?://', c):
            return raw          # raw, not lower-cased: paths/tokens are case sensitive
        print(f"  {R}pick 1-6, or paste a full URL{RST}")


def ask_max(default):
    c = _ask(f"  how many to check per protocol {W}[{default}]{RST} (0 = no limit): ")
    if not c:
        return default
    try:
        return max(0, int(c))
    except ValueError:
        print(f"  {Y}not a number, using {default}{RST}")
        return default


def ask_retries(default):
    c = _ask(f"  retry failed proxies how many times? {W}[{default}]{RST} "
             f"(recovers ~1.6x more): ")
    if not c:
        return default
    try:
        return max(0, int(c))
    except ValueError:
        print(f"  {Y}not a number, using {default}{RST}")
        return default


def parse_protocols(spec):
    """Turn the -p value into (protocols, want_https, mixed, https_only)."""
    sel = [s.strip().lower() for s in spec.split(",") if s.strip()]
    if "all" in sel or "mixed" in sel:
        return ["http", "socks4", "socks5"], True, True, False
    protos = []
    for s in sel:
        if s == "https":
            protos.append("http")
        elif s == "socks":
            protos += ["socks4", "socks5"]
        elif s in ("http", "socks4", "socks5"):
            protos.append(s)
        else:
            sys.exit(f"unknown protocol: {s}  (use http, https, socks4, socks5, socks, all)")
    protos = list(dict.fromkeys(protos))
    return protos, ("https" in sel), (len(protos) > 1), (sel == ["https"])


class LazyFile:
    """Truncates the real file only once there is something to write, so a
    crash or Ctrl+C during the slow fetch phase cannot destroy the results of
    the previous run."""

    def __init__(self, path):
        self.path = path
        self.f = None

    def write(self, text):
        if self.f is None:
            self.f = open(self.path, "w")
        self.f.write(text)

    def flush(self):
        if self.f is not None:
            self.f.flush()

    def close(self):
        if self.f is not None:
            self.f.close()
            self.f = None


# ---------- checking ----------
_lock = threading.Lock()
STATE = {"ok": 0, "dead": 0, "done": 0, "total": 0, "label": ""}


def _get(url, proxy, scheme, timeout):
    prox = {"http": f"{scheme}://{proxy}", "https": f"{scheme}://{proxy}"}
    return requests.get(url, proxies=prox, timeout=timeout,
                        headers={"User-Agent": UA})


def probe(proto, proxy, url, marker, timeout, host=None):
    """True if this proxy can actually fetch `url`."""
    try:
        r = _get(url, proxy, SCHEME[proto], timeout)
        if marker:
            return r.status_code == 200 and marker in r.text
        if not r.ok:          # 4xx/5xx: reached it but was rejected -> not usable
            return False
        if host:
            # Some proxies answer 200 with their own ad/block page. If we did
            # not end up on the host we asked for, it is not a real success.
            got = urlparse(r.url).netloc.lower()
            if got and host not in got and got not in host:
                return False
        return True
    except Exception:
        return False


def run_pass(proto, proxies, url, marker, sink=None, host=None):
    """Check every proxy once. Returns (working, failed)."""
    working, failed = [], []

    def one(p):
        ok = probe(proto, p, url, marker, CHECK_TIMEOUT, host)
        with _lock:
            if ok:
                STATE["ok"] += 1
                working.append(p)
                if sink:
                    sink(p)
            else:
                STATE["dead"] += 1
                failed.append(p)
            STATE["done"] += 1
            # written inside the lock: otherwise threads interleave and the
            # last line left on screen can show wrong totals
            sys.stdout.write(f'\r{C}[ {STATE["label"]} ]{RST} '
                             f'{G}ok: {STATE["ok"]}{RST}  '
                             f'{R}fail: {STATE["dead"]}{RST}  '
                             f'({STATE["done"]}/{STATE["total"]})   ')
            sys.stdout.flush()

    with ThreadPoolExecutor(max_workers=CHECK_WORKERS) as ex:
        list(ex.map(one, proxies))
    return working, failed



# ---------- churn control (measured additions) ----------
def probe_timed(proto, proxy, url, marker, timeout):
    """probe() but also returns how long the successful request took."""
    t0 = time.time()
    ok = probe(proto, proxy, url, marker, timeout)
    return ok, (time.time() - t0 if ok else None)


def check_map(proto, proxies, url, marker, timeout=None, workers=None):
    """One pass. Returns {proxy: latency} for the ones that answered."""
    timeout = timeout or CHECK_TIMEOUT
    workers = workers or CHECK_WORKERS
    lat, lk = {}, threading.Lock()

    def one(p):
        ok, dt = probe_timed(proto, p, url, marker, timeout)
        if ok:
            with lk:
                lat[p] = dt

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, proxies))
    return lat


def read_previous(path):
    """Lines of a previous output file, scheme prefixes stripped."""
    try:
        with open(path) as f:
            out = [ln.strip().split("://")[-1] for ln in f if ln.strip()]
    except OSError:
        return []
    return list(dict.fromkeys(q for q in out if valid(q)))


def seed_from_previous(proto, old, url, marker):
    """Re-validate the previous run's output. Measured 28-37% hit rate against
    5.5% for a fresh tier-A proxy: 5-7x more working proxies per check."""
    if not old:
        return [], {}
    lat = check_map(proto, old, url, marker)
    alive = sorted(lat, key=lat.get)
    pct = 100.0 * len(alive) / len(old)
    print(f"{C}[*]{RST} seeded from last run: {G}{len(alive)}{RST}/{len(old)} "
          f"still alive ({pct:.0f}%)")
    return alive, lat


HISTORY_NAME = "proxy_history.json"


def load_history(outdir):
    """Per-proxy success memory, shared with proxy_pool.py. Survives runs, so
    the ranking keeps improving instead of starting blind every time."""
    try:
        with open(os.path.join(outdir, HISTORY_NAME)) as f:
            h = json.load(f)
            return h if isinstance(h, dict) else {}
    except (OSError, ValueError):
        return {}


def save_history(outdir, hist):
    path = os.path.join(outdir, HISTORY_NAME)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(hist, f, separators=(",", ":"))
        os.replace(tmp, path)      # atomic: a crash cannot corrupt it
    except OSError:
        pass


def hist_score(hist, p):
    """Laplace-smoothed lifetime success rate. Unknown proxies sit at 0.5 so
    they are neither favoured nor buried."""
    h = hist.get(p)
    if not h:
        return 0.5
    ok, fail = h.get("ok", 0), h.get("fail", 0)
    return (ok + 1.0) / (ok + fail + 2.0)


def record(hist, proxy, ok, n=1):
    h = hist.setdefault(proxy, {"ok": 0, "fail": 0})
    h["ok" if ok else "fail"] += n
    if ok:
        h["last_ok"] = int(time.time())


def vote_rank(proto, proxies, url, marker, passes=3, lat_cap=None):
    """Re-check every proxy `passes` times and score it by how many times it
    answered. Returns (ranked, votes, lat) where `ranked` is sorted
    most-reliable-first (votes desc, then latency asc).

    Measured: a proxy that answers 3/3 back-to-back checks is alive 15 minutes
    later 57.1% of the time; 1/3 only 25.8%; 3/3 AND under 5s -> 78.1%
    (n=56/198/32 of a 382-proxy union). One check on its own is close to a coin
    flip even for a genuinely usable proxy, which is why 'validated' sets look
    like they churn 60%+ when they mostly do not.
    """
    cand = list(dict.fromkeys(proxies))
    votes = {q: 0 for q in cand}
    lat = {}
    for k in range(passes):
        got = check_map(proto, cand, url, marker)
        print(f"    vote pass {k + 1}/{passes}: {G}{len(got)}{RST}/{len(cand)} answered")
        for q, v in got.items():
            votes[q] += 1
            lat[q] = min(lat.get(q, 9e9), v)
    ranked = [q for q in cand if votes[q] > 0]
    if lat_cap:
        ranked = [q for q in ranked if lat.get(q, 9e9) <= lat_cap]
    ranked.sort(key=lambda q: (-votes[q], lat.get(q, 9e9), q))
    hi = [q for q in ranked if votes[q] == passes]
    print(f"    unanimous ({passes}/{passes}): {G}{len(hi)}{RST}   "
          f"partial: {len(ranked) - len(hi)}   never again: {len(cand) - len(ranked)}")
    return ranked, votes, lat


def keepalive(proto, path, url, marker, interval=600, strikes=2):
    """Re-check the output file forever so it keeps matching reality.
    strikes=2 because 87% of proxies that fail one check answer a later one."""
    fails = {}
    while True:
        cur = read_previous(path)
        if not cur:
            print(f"{Y}[keepalive] {path} is empty, stopping{RST}")
            return
        lat = check_map(proto, cur, url, marker)
        keep = []
        for q in cur:
            if q in lat:
                fails[q] = 0
                keep.append(q)
            else:
                fails[q] = fails.get(q, 0) + 1
                if fails[q] < strikes:
                    keep.append(q)
        keep.sort(key=lambda q: lat.get(q, 9e9))
        with open(path, "w") as f:
            if keep:
                f.write("\n".join(keep) + "\n")
        print(f"{C}[keepalive]{RST} {G}{len(lat)}{RST} answered, "
              f"file now {len(keep)} lines; next check in {interval}s")
        time.sleep(interval)


def main():
    global CHECK_TIMEOUT, CHECK_WORKERS
    ap = argparse.ArgumentParser(
        description="Free proxy scraper + checker with protocol and target options.")
    ap.add_argument("-p", "--protocol", default=None,
                    help="http | https | socks4 | socks5 | socks | all (comma separated). "
                         "Omit for an interactive menu.")
    ap.add_argument("--target", default=None,
                    help="URL to test proxies against, e.g. https://www.tiktok.com/robots.txt . "
                         "Default is a generic check. Testing against the site you actually "
                         "care about finds far more usable proxies.")
    ap.add_argument("-m", "--max", type=int, default=None,
                    help="max proxies to check per protocol (0 = no cap)")
    ap.add_argument("--retries", type=int, default=None,
                    help=f"extra passes over failed proxies (default {RETRIES})")
    ap.add_argument("-t", "--timeout", type=int, default=CHECK_TIMEOUT,
                    help="seconds per proxy test")
    ap.add_argument("-w", "--workers", type=int, default=CHECK_WORKERS,
                    help="concurrent checks")
    ap.add_argument("--no-seed", action="store_true",
                    help="do not re-validate the previous output file first")
    ap.add_argument("--confirm", type=int, default=3,
                    help="extra reliability-vote passes before writing (default 3, 0 = off)")
    ap.add_argument("--lat-cap", type=float, default=None,
                    help="drop confirmed proxies slower than this many seconds")
    ap.add_argument("--keepalive", type=int, default=0, metavar="SECS",
                    help="after the scan, keep re-checking the output file every SECS seconds")
    ap.add_argument("-o", "--out-dir", default=None,
                    help="where to write results (default: next to this script)")
    args = ap.parse_args()

    CHECK_TIMEOUT = max(1, args.timeout)
    CHECK_WORKERS = max(1, args.workers)      # 0 would crash ThreadPoolExecutor
    outdir = args.out_dir or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(outdir, exist_ok=True)

    clear()
    spec, target = args.protocol, args.target
    max_proxies, retries = args.max, args.retries

    # No -p given and we have a real terminal? Ask instead of assuming.
    if spec is None and sys.stdin.isatty():
        print(f"{C}=== free proxy scraper + checker ==={RST}")
        spec = choose_protocol()
        if target is None:
            target = choose_target()
        if max_proxies is None:
            max_proxies = ask_max(MAX_PROXIES)
        if retries is None:
            retries = ask_retries(RETRIES)
    spec = spec or "http"
    # a negative value means the user fat-fingered it: fall back to the default
    # rather than silently reading as "unlimited" (0 is the real unlimited)
    max_proxies = MAX_PROXIES if max_proxies is None or max_proxies < 0 else max_proxies
    retries = RETRIES if retries is None or retries < 0 else retries

    protos, want_https, mixed, https_only = parse_protocols(spec)
    if not protos:
        sys.exit(f"{R}[!] no protocols selected{RST}")

    # Pick what each proxy gets tested against.
    if target:
        if not re.match(r'^https?://', target, re.I):
            target = "https://" + target.lstrip("/")
        host_part = urlparse(target).netloc
        # a real hostname: letters/digits/dots/hyphens, optional :port. This
        # rejects things like "not a url" that urlparse otherwise accepts.
        if not re.match(r'^[A-Za-z0-9._\-]+(:\d+)?$', host_part):
            sys.exit(f"{R}[!] --target does not look like a URL: {target}{RST}")
        test_url, marker = target, None
        label = host_part
        # An https target already proves the proxy can do TLS.
        if target.lower().startswith("https://"):
            want_https = False
    else:
        test_url, marker, label = GENERIC_URL, GENERIC_MARKER, "generic"

    if any(p.startswith("socks") for p in protos):
        try:
            import socks  # noqa: F401
        except ImportError:
            sys.exit(f"{R}[!] socks support needs PySocks:   pip install PySocks{RST}")

    print(f"\n{C}[*]{RST} protocols : {W}{', '.join(protos)}{RST}"
          f"{'   (+ https capability test)' if want_https else ''}")
    print(f"{C}[*]{RST} testing vs : {W}{label}{RST}"
          f"{'' if target else '   (generic - use --target for a real site)'}")
    print(f"{C}[*]{RST} retries    : {W}{retries}{RST}")

    history = load_history(outdir)
    if history:
        print(f"{C}[*]{RST} memory     : {W}{len(history)}{RST} proxies with a track record")
    paths, files = {}, {}
    previous = {}
    for p in protos:
        paths[p] = os.path.join(outdir, f"working_{p}.txt")
        paths[p + "_stable"] = os.path.join(outdir, f"working_{p}_stable.txt")
        previous[p] = [] if args.no_seed else (
            read_previous(paths[p]) + read_previous(paths[p + "_stable"]))
        if want_https:
            paths[p + "_https"] = os.path.join(outdir, f"working_{p}_https.txt")
    if mixed:
        paths["all"] = os.path.join(outdir, "working_all.txt")
    for k, v in paths.items():
        files[k] = LazyFile(v)           # truncated only on first write

    results, https_ok = {}, {}
    stable_res, lat_res = {}, {}
    rank_res, vote_res = {}, {}
    start = time.time()
    try:
        for proto in protos:
            seeded, seed_lat = [], {}
            if previous.get(proto):
                print(f"\n{C}[*]{RST} re-validating {len(previous[proto])} "
                      f"proxies from the previous run ...")
                seeded, seed_lat = seed_from_previous(
                    proto, previous[proto], test_url, marker)
            print(f"\n{C}[*]{RST} fetching {proto} sources ...")
            pool = gather(proto, max_proxies)
            known = set(seeded)
            pool = seeded + [x for x in pool if x not in known]
            if not pool:
                print(f"{R}[!] no {proto} proxies fetched{RST}")
                results[proto] = []
                continue

            def sink(p, _proto=proto):
                files[_proto].write(p + "\n")
                files[_proto].flush()
                if "all" in files:
                    files["all"].write(f"{SCHEME[_proto]}://{p}\n")
                    files["all"].flush()

            found, pending = [], pool
            for attempt in range(retries + 1):
                if not pending:
                    break
                STATE.update(ok=0, dead=0, done=0, total=len(pending),
                             label=f"{proto} {'retry ' + str(attempt) if attempt else 'scan'}")
                print(f"{C}[*]{RST} {'retry pass ' + str(attempt) if attempt else 'checking'}"
                      f" {W}{len(pending)}{RST} {proto} proxies")
                got, pending = run_pass(proto, pending, test_url, marker, sink,
                                        host=(label if target else None))
                found += got
                print(f"\n    -> {G}{len(got)} working{RST}"
                      f"{' (recovered by retry)' if attempt else ''}")
            results[proto] = found
            # remember this run's outcome for next time
            found_set = set(found)
            for q in found_set:
                record(history, q, True)
            for q in pool:
                if q not in found_set:
                    record(history, q, False)

            if args.confirm and found:
                print(f"{C}[*]{RST} reliability vote: {args.confirm} extra passes "
                      f"over {W}{len(found)}{RST} proxies ...")
                ranked, votes, lat = vote_rank(proto, found, test_url, marker,
                                               passes=args.confirm,
                                               lat_cap=args.lat_cap)
                for k2, v2 in seed_lat.items():
                    lat.setdefault(k2, v2)
                stable = [q for q in ranked if votes[q] == args.confirm]
                with open(paths[proto + "_stable"], "w") as sf:
                    for q in stable:
                        sf.write(q + "\n")
                stable_res[proto] = stable
                rank_res[proto] = ranked
                vote_res[proto] = votes
                # the vote passes are extra evidence: fold them in too
                for q, v in votes.items():
                    if v:
                        record(history, q, True, v)
                    if args.confirm - v > 0:
                        record(history, q, False, args.confirm - v)
                lat_res[proto] = lat
                print(f"    -> {G}{len(stable)} unanimous{RST} -> "
                      f"{W}working_{proto}_stable.txt{RST}")

            # optional: which of the working ones can also do https
            if want_https and found:
                STATE.update(ok=0, dead=0, done=0, total=len(found),
                             label=f"{proto} https")
                print(f"{C}[*]{RST} testing https capability on {W}{len(found)}{RST} ...")
                def https_sink(p, _proto=proto):
                    files[_proto + "_https"].write(p + "\n")
                    files[_proto + "_https"].flush()

                sec, _ = run_pass(proto, found, HTTPS_TEST_URL, None,
                                  sink=https_sink)
                https_ok[proto] = sec
                print()
    finally:
        for f in files.values():
            f.close()

    # final rewrite: dedup + sorted
    for p in protos:
        # -p https means the user asked for https-capable proxies, so that is
        # what the main file should contain.
        primary = https_ok.get(p, []) if https_only else results.get(p, [])
        # Rank most-reliable-first: vote count desc, then latency asc. Measured:
        # a proxy that answered all 3 vote passes is alive 15 min later 57% of
        # the time (78% if also under 5s) against 26% for a 1-of-3 proxy, so the
        # head of this file is worth several times the tail. Nothing is dropped,
        # it is only ordered - the tail still works ~26% of the time.
        votes = vote_res.get(p, {})
        lat = lat_res.get(p, {})
        # Blend THIS run's votes with the proxy's lifetime record, so a proxy
        # that has answered reliably for days outranks one that got lucky once.
        ranked = sorted(set(primary),
                        key=lambda q: (-(votes.get(q, 0) + 2.0 * hist_score(history, q)),
                                       lat.get(q, 9e9), q))
        with open(paths[p], "w") as f:
            for x in ranked:
                f.write(x + "\n")
        if want_https:
            with open(paths[p + "_https"], "w") as f:
                for x in sorted(set(https_ok.get(p, []))):
                    f.write(x + "\n")
    if mixed:
        with open(paths["all"], "w") as f:
            for p in protos:
                src = https_ok.get(p, []) if https_only else results.get(p, [])
                for x in sorted(set(src)):
                    f.write(f"{SCHEME[p]}://{x}\n")

    save_history(outdir, history)

    dt = time.time() - start
    print(f"\n{G}[+] done in {dt:.0f}s{RST}   (tested against {W}{label}{RST})")
    print(f"{C}[*]{RST} memory saved: {W}{len(history)}{RST} proxies tracked in "
          f"{W}{HISTORY_NAME}{RST}  (ranking improves each run)")
    for p in protos:
        n = len(set(https_ok.get(p, []) if https_only else results.get(p, [])))
        line = f"{G}[+] {p:6} {n:5} working{RST} -> {W}{os.path.basename(paths[p])}{RST}"
        if want_https:
            s = len(set(https_ok.get(p, [])))
            pct = (100.0 * s / n) if n else 0.0
            line += (f"   {Y}{s} reach https ({pct:.0f}%){RST}"
                     f" -> {W}{os.path.basename(paths[p + '_https'])}{RST}")
        print(line)
        if args.confirm and p in stable_res:
            print(f"    {C}{len(set(stable_res[p]))} of them answered all "
                  f"{args.confirm} extra checks{RST} -> "
                  f"{W}working_{p}_stable.txt{RST}   "
                  f"(working_{p}.txt is ranked most-reliable-first)")
    if mixed:
        print(f"{G}[+] combined, scheme-prefixed{RST} -> {W}{os.path.basename(paths['all'])}{RST}")

    if args.keepalive:
        proto0 = protos[0]
        tgt = (paths[proto0 + "_stable"] if stable_res.get(proto0)
               else paths[proto0])
        print(f"\n{C}[*]{RST} keepalive: re-checking {os.path.basename(tgt)} "
              f"every {args.keepalive}s   (ctrl-c to stop)")
        try:
            keepalive(proto0, tgt, test_url, marker, args.keepalive)
        except KeyboardInterrupt:
            print(f"\n{Y}[*] keepalive stopped{RST}")


if __name__ == "__main__":
    main()
