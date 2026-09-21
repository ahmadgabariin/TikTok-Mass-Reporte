import json
import csv
import os
import time
import uuid
import random
from datetime import datetime, timezone
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import shutil
import subprocess
import sys

CSV_FILE = "reports.csv"
PROXIES_FILE = "proxies_with_stats.json"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

CATEGORIES = {
    "1": "Spam or misleading",
    "2": "Sexual content / Nudity",
    "3": "Illegal activity / Sale of illegal goods",
    "4": "Child safety",
    "5": "Harassment or bullying",
    "6": "Hateful behavior or symbols",
    "7": "Violent or repulsive content",
    "8": "Eating disorder",
    "9": "Suicide or self-harm",
    "10": "Terrorism or violent extremism",
    "11": "False information / Misinformation",
    "12": "Infringement of intellectual property",
    "13": "Minors in dangerous situations"
}

class ProxyManager:
    def __init__(self):
        self.proxies = {}
        self.load()
    
    def load(self):
        if os.path.exists(PROXIES_FILE):
            try:
                with open(PROXIES_FILE, 'r') as f:
                    data = json.load(f)
                    self.proxies = data.get('proxies', {})
            except:
                self.proxies = {}
    
    def save(self):
        with open(PROXIES_FILE, 'w') as f:
            json.dump({'proxies': self.proxies}, f)
    
    def add_proxy(self, proxy):
        if proxy not in self.proxies:
            self.proxies[proxy] = {'uses': 0}
    
    def get_random_proxy(self):
        return random.choice(list(self.proxies.keys())) if self.proxies else None
    
    def get_proxy_count(self):
        return len(self.proxies)
    
    def fetch_public_proxies(self):
        print("\n>>> Fetching SOCKS5 proxies from multiple sources...\n")
        
        total_added = 0
        
        # Source 1: proxy-list.download
        print("[Source 1] proxy-list.download...")
        try:
            response = requests.get('https://www.proxy-list.download/api/v1/get?type=socks5', timeout=10)
            proxies = response.text.strip().split('\r\n')
            count = 0
            for proxy in proxies:
                if proxy.strip():
                    self.add_proxy(f"socks5://{proxy.strip()}")
                    count += 1
            print(f"  ✓ Added {count} proxies")
            total_added += count
        except Exception as e:
            print(f"  ✗ Failed: {str(e)[:50]}")
        
        # Source 2: Free Proxy List API
        print("[Source 2] Free Proxy List...")
        try:
            response = requests.get('https://www.proxy-list.download/api/v1/get?type=http', timeout=10)
            proxies = response.text.strip().split('\r\n')
            count = 0
            for proxy in proxies[:500]:
                if proxy.strip():
                    self.add_proxy(f"http://{proxy.strip()}")
                    count += 1
            print(f"  ✓ Added {count} proxies")
            total_added += count
        except Exception as e:
            print(f"  ✗ Failed: {str(e)[:50]}")
        
        # Source 3: Gather Proxy
        print("[Source 3] Gather Proxy...")
        try:
            response = requests.get('https://api.gatherproxy.com/api/getproxy?country=all&type=http', 
                                  timeout=10, headers={'User-Agent': USER_AGENTS[0]})
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                count = 0
                for line in lines[:300]:
                    if ':' in line:
                        ip = line.split(':')[0]
                        port = line.split(':')[1] if len(line.split(':')) > 1 else '80'
                        if ip and port:
                            self.add_proxy(f"http://{ip}:{port}")
                            count += 1
                print(f"  ✓ Added {count} proxies")
                total_added += count
            else:
                print(f"  ✗ Status {response.status_code}")
        except Exception as e:
            print(f"  ✗ Failed: {str(e)[:50]}")
        
        # Source 4: Proxy Nova
        print("[Source 4] Proxy Nova (HTTP)...")
        try:
            response = requests.get('https://www.proxynova.com/proxy-server-list/country-us/', 
                                  timeout=10, headers={'User-Agent': USER_AGENTS[0]})
            if response.status_code == 200:
                # Extract IPs from HTML (simple regex)
                import re
                ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', response.text)
                count = 0
                for ip in ips[:200]:
                    self.add_proxy(f"http://{ip}:80")
                    count += 1
                print(f"  ✓ Added {count} proxies")
                total_added += count
            else:
                print(f"  ✗ Status {response.status_code}")
        except Exception as e:
            print(f"  ✗ Failed: {str(e)[:50]}")
        
        # Source 5: Public Proxy List
        print("[Source 5] Public Proxy List...")
        try:
            response = requests.get('https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
                                  timeout=10)
            if response.status_code == 200:
                proxies = response.text.strip().split('\n')
                count = 0
                for proxy in proxies[:500]:
                    if proxy.strip() and ':' in proxy:
                        self.add_proxy(f"http://{proxy.strip()}")
                        count += 1
                print(f"  ✓ Added {count} proxies")
                total_added += count
            else:
                print(f"  ✗ Status {response.status_code}")
        except Exception as e:
            print(f"  ✗ Failed: {str(e)[:50]}")
        
        self.save()
        print(f"\n{'='*60}")
        print(f"✓ TOTAL PROXIES LOADED: {self.get_proxy_count()}")
        print(f"  Added this session: {total_added}")
        print(f"{'='*60}\n")
    
    def list_proxies(self):
        if self.proxies:
            print(f"\n=== PROXIES ({len(self.proxies)}) ===")
            for i, proxy in enumerate(list(self.proxies.keys())[:20]):
                print(f"{i+1}. {proxy}")
            if len(self.proxies) > 20:
                print(f"... and {len(self.proxies) - 20} more")
        else:
            print("No proxies loaded")
    
    def clear_proxies(self):
        self.proxies = {}
        self.save()
        print("Proxies cleared")
    
    def fetch_with_getproxies_pro(self):
        """Integrated getproxies_pro fetcher: asks user for count & protocol"""
        print("\n" + "="*70)
        print("  Integrated Proxy Fetcher (getproxies_pro)")
        print("="*70)
        
        try:
            count = input("How many proxies to fetch? (default 50): ").strip()
            count = int(count) if count else 50
            
            print("\nSelect protocol:")
            print("[1] HTTP")
            print("[2] SOCKS4")
            print("[3] SOCKS5")
            print("[4] ALL (mixed)")
            
            proto_choice = input("Choice (1-4, default 3): ").strip()
            
            protocol_map = {
                "1": "http",
                "2": "socks4",
                "3": "socks5",
                "4": "all"
            }
            protocol = protocol_map.get(proto_choice, "socks5")
            
            print(f"\n>>> Starting getproxies_pro with -p {protocol} -m {count} --target https://www.tiktok.com ...")
            print(f"    (Fetching up to {count} proxies, this may take 1-3 minutes)\n")
            
            # Run getproxies_pro
            result = subprocess.run(
                [sys.executable, "getproxies_pro.py", "-p", protocol, "-m", str(count), "--target", "https://www.tiktok.com"],
                capture_output=False,
                text=True,
                timeout=300  # 5 min max
            )
            
            if result.returncode != 0:
                print(f"✗ getproxies_pro failed with code {result.returncode}")
                return
            
            # Determine output file
            if protocol == "all":
                outfile = "working_all.txt"
            else:
                outfile = f"working_{protocol}.txt"
            
            if not os.path.exists(outfile):
                print(f"✗ Output file not found: {outfile}")
                return
            
            # Read and load proxies (cap at requested count)
            loaded = 0
            scheme_map = {"http": "http", "socks4": "socks4", "socks5": "socks5h", "all": "socks5h"}
            scheme = scheme_map.get(protocol, "socks5h")
            
            with open(outfile, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and loaded < count:
                        # getproxies_pro outputs bare ip:port, add scheme prefix
                        if "://" not in line:
                            line = f"{scheme}://{line}"
                        self.add_proxy(line)
                        loaded += 1
                    if loaded >= count:
                        break
            
            self.save()
            
            print(f"\n{'='*60}")
            print(f"✓ LOADED: {loaded} {protocol} proxies from {outfile}")
            print(f"  Total proxies in pool: {self.get_proxy_count()}")
            print(f"{'='*60}\n")
        
        except KeyboardInterrupt:
            print("\n\n✗ Fetch cancelled by user")
        except subprocess.TimeoutExpired:
            print("\n✗ Fetch timed out (>5 min)")
        except ValueError:
            print("✗ Invalid input")
        except Exception as e:
            print(f"✗ Error: {str(e)[:80]}")

class DeepValidator:
    @staticmethod
    def validate_config(video_id, owner_id, categories, num_reports, proxy_count):
        """Deep check on all config before launch"""
        print(f"\n{'='*70}")
        print(f"DEEP VALIDATION CHECK")
        print(f"{'='*70}\n")
        
        checks = []
        
        # Check 1: Video ID format
        if not video_id or not video_id.isdigit():
            checks.append(("Video ID format", "FAIL", "Must be numeric"))
        elif len(video_id) != 19:
            checks.append(("Video ID length", "WARN", f"Expected 19 digits, got {len(video_id)}"))
        else:
            checks.append(("Video ID format", "PASS", f"19 digits: {video_id}"))
        
        # Check 2: Owner ID format
        if not owner_id or not owner_id.isdigit():
            checks.append(("Owner ID format", "FAIL", "Must be numeric"))
        elif len(owner_id) != 19:
            checks.append(("Owner ID length", "WARN", f"Expected 19 digits, got {len(owner_id)}"))
        else:
            checks.append(("Owner ID format", "PASS", f"19 digits: {owner_id}"))
        
        # Check 3: Categories
        if not categories:
            checks.append(("Categories", "FAIL", "No categories selected"))
        else:
            invalid = [c for c in categories if c not in CATEGORIES]
            if invalid:
                checks.append(("Categories validation", "FAIL", f"Invalid: {invalid}"))
            else:
                cat_names = ", ".join([CATEGORIES[c] for c in categories])
                checks.append(("Categories", "PASS", f"{len(categories)} selected: {cat_names[:50]}..."))
        
        # Check 4: Report count
        try:
            num = int(num_reports)
            if num < 1:
                checks.append(("Report count", "FAIL", "Must be >= 1"))
            elif num > 10000:
                checks.append(("Report count", "WARN", f"Very high: {num} reports"))
            else:
                checks.append(("Report count", "PASS", f"{num} reports"))
        except:
            checks.append(("Report count", "FAIL", "Must be numeric"))
        
        # Check 5: Endpoint
        endpoint = "https://www.tiktok.com/aweme/v2/aweme/feedback/"
        try:
            resp = requests.head(endpoint, timeout=5)
            checks.append(("Endpoint reachability", "PASS", f"Status {resp.status_code}"))
        except:
            checks.append(("Endpoint reachability", "WARN", "Cannot reach endpoint (network issue?)"))
        
        # Check 6: Proxies
        if proxy_count == 0:
            checks.append(("Proxy configuration", "WARN", "No proxies loaded (will use direct IP)"))
        else:
            checks.append(("Proxy configuration", "PASS", f"{proxy_count} proxies loaded"))
        
        # Check 7: Payload structure
        payload = {"aweme_id": str(video_id), "reason_id": int(categories[0]) if categories else 0}
        checks.append(("Payload structure", "PASS", f"Valid JSON: {payload}"))
        
        # Print results
        all_pass = True
        for check_name, status, detail in checks:
            if status == "PASS":
                symbol = "✓"
            elif status == "WARN":
                symbol = "⚠"
                all_pass = False
            else:
                symbol = "✗"
                all_pass = False
            
            print(f"{symbol} {check_name:30s} [{status:4s}] {detail}")
        
        print(f"\n{'='*70}")
        if all_pass:
            print("All checks passed. Ready to launch.\n")
            return True
        else:
            print("Some checks failed or warned. Review above before continuing.\n")
            confirm = input("Continue anyway? (yes/no): ").strip().lower()
            return confirm in ['yes', 'y']

class TikTokReporter:
    def __init__(self):
        self.session = requests.Session()
        self.proxy_mgr = ProxyManager()
        self.validator = DeepValidator()
        self.csv_lock = threading.Lock()
        self.total = 0
        self.success = 0
    
    def select_categories(self):
        """Multi-select categories with approval"""
        selected = []
        
        while True:
            print("\n" + "="*70)
            print("SELECT CATEGORIES TO REPORT")
            print("="*70)
            
            for code in sorted(CATEGORIES.keys(), key=lambda x: int(x)):
                marker = "✓" if code in selected else " "
                print(f"  [{marker}] {code:2s} = {CATEGORIES[code]}")
            
            print(f"\nCurrently selected: {', '.join([CATEGORIES[c] for c in selected]) if selected else 'None'}")
            print("\nOptions:")
            print("  [1-13]  Toggle category")
            print("  [all]   Select ALL 13 categories (will RANDOMIZE per report)")
            print("  [a]     Approve selection")
            print("  [c]     Clear all")
            print("="*70)
            
            choice = input("Choice: ").strip().lower()
            
            if choice in [str(i) for i in range(1, 14)]:
                if choice in selected:
                    selected.remove(choice)
                    print(f"✓ Deselected {choice}")
                else:
                    selected.append(choice)
                    print(f"✓ Selected {choice}")
            elif choice == 'all':
                selected = [str(i) for i in range(1, 14)]
                print(f"✓ Selected ALL 13 categories")
                print(f"   Reports will pick RANDOM categories from: {', '.join([CATEGORIES[c] for c in selected])}")
            elif choice == 'a':
                if selected:
                    print(f"\n✓ Approving: {len(selected)} categories")
                    for c in sorted(selected, key=lambda x: int(x)):
                        print(f"   {c}. {CATEGORIES[c]}")
                    return sorted(selected, key=lambda x: int(x))
                else:
                    print("Must select at least one category")
            elif choice == 'c':
                selected = []
                print("Cleared all selections")
            else:
                print("Invalid choice")
    
    def report_video(self, video_id, owner_id, categories, num_reports):
        proxy_count = self.proxy_mgr.get_proxy_count()
        use_proxies = proxy_count > 0
        
        # DEEP VALIDATION
        if not self.validator.validate_config(video_id, owner_id, categories, num_reports, proxy_count):
            print("Validation cancelled.\n")
            return
        
        if not use_proxies:
            print(f"⚠️  WARNING: NO PROXIES LOADED")
            print(f"    All {num_reports} reports will use your direct IP address")
            print(f"    Risk: account flagging, rate limiting, IP ban\n")
            confirm = input("Continue anyway? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("Cancelled.\n")
                return
        
        num_threads = input("Threads (default 50): ").strip()
        num_threads = int(num_threads) if num_threads else 50
        
        print(f"\n>>> Starting {num_reports} reports with {num_threads} threads...")
        print(f"    Video ID: {video_id}")
        print(f"    Owner ID: {owner_id}")
        print(f"    Categories: {len(categories)} selected")
        print(f"    Mode: RANDOM (each report picks random category)")
        print(f"    Proxies: {proxy_count if use_proxies else 'NONE (direct IP)'}")
        print(f"    Retry: 5 attempts, backoff 3-7s\n")
        
        endpoint = "https://www.tiktok.com/aweme/v2/aweme/feedback/"
        
        def send_report(report_index):
            """Worker function: sends one report with retries"""
            device_id = uuid.uuid4().hex[:8]
            category = random.choice(categories)
            
            headers = {"User-Agent": USER_AGENTS[report_index % len(USER_AGENTS)]}
            payload = {"aweme_id": str(video_id), "reason_id": int(category)}
            
            # Retry loop: 5 attempts with backoff
            for attempt in range(5):
                backoff_sec = 3 + attempt  # 3, 4, 5, 6, 7
                
                proxy = self.proxy_mgr.get_random_proxy() if use_proxies else None
                
                try:
                    proxies_dict = {"https": proxy, "http": proxy} if proxy else None
                    response = self.session.post(endpoint, json=payload, headers=headers, 
                                                 proxies=proxies_dict, timeout=10)
                    
                    status = response.status_code
                    success = status == 200
                    
                    # Print + update (no lock needed)
                    print(f"[{report_index+1}/{num_reports}] Device: {device_id} | Category: {category} ({CATEGORIES[category]}) | Attempt: {attempt+1}/5 | Status: {status} | {'✓' if success else '✗'}")
                    self.total += 1
                    if success:
                        self.success += 1
                    self._write_csv(device_id, video_id, owner_id, category, status)
                    
                    return  # Success, exit retry loop
                
                except Exception as e:
                    error_msg = str(e)[:40]
                    
                    if attempt < 4:  # Not the last attempt
                        print(f"[{report_index+1}/{num_reports}] Device: {device_id} | Category: {category} | Attempt: {attempt+1}/5 | ERROR: {error_msg} | Retry in {backoff_sec}s...")
                        sys.stdout.flush()
                        time.sleep(backoff_sec)
                    else:  # Last attempt failed
                        print(f"[{report_index+1}/{num_reports}] Device: {device_id} | Category: {category} | Attempt: {attempt+1}/5 | FAILED: {error_msg}")
                        sys.stdout.flush()
                        with self.csv_lock:
                            self.total += 1
                            self._write_csv(device_id, video_id, owner_id, category, 0)
                        return
        
        # Thread pool: run all reports in parallel
        executor = ThreadPoolExecutor(max_workers=num_threads)
        futures = [executor.submit(send_report, i) for i in range(int(num_reports))]
        
        for future in futures:
            try:
                future.result(timeout=30)
            except Exception:
                pass
        
        # Force exit without waiting for executor shutdown
        sys.stdout.flush()
        time.sleep(0.1)
        print(f"\n✓ All {num_reports} reports completed")
        sys.stdout.flush()
        time.sleep(0.05)
        os._exit(0)
    
    def _write_csv(self, device_id, video_id, owner_id, category, status_code):
        try:
            file_exists = os.path.exists(CSV_FILE)
            with open(CSV_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["timestamp", "device_id", "video_id", "owner_id", "category", "status_code"])
                ts = datetime.now(timezone.utc).isoformat()
                writer.writerow([ts, device_id, str(video_id), str(owner_id), category, status_code])
        except:
            pass  # Silent fail on CSV write contention
    
    def download_csv(self):
        if not os.path.exists(CSV_FILE):
            print("No reports yet")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_name = f"reports_{timestamp}.csv"
        shutil.copy(CSV_FILE, download_name)
        print(f"\n✓ Downloaded: {download_name}")
        print(f"  Path: {os.path.abspath(download_name)}")
    
    def view_stats(self):
        print(f"\n=== STATS ===")
        print(f"Total: {self.total}")
        print(f"Success: {self.success}")
        if self.total > 0:
            print(f"Rate: {100*self.success//self.total}%")
    
    def menu(self):
        while True:
            print("\n" + "="*70)
            print("  TikTok Mass Reporter v8.3 - Random Category Selection")
            print(f"  Proxies loaded: {self.proxy_mgr.get_proxy_count()}")
            print("="*70)
            print("[1] Report Video")
            print("[2] Fetch Proxies (Multiple Sources)")
            print("[3] List Proxies")
            print("[4] Clear Proxies")
            print("[5] View Stats")
            print("[6] Download CSV")
            print("[7] Exit")
            print("="*70)
            
            choice = input("Choice: ").strip()
            
            if choice == "1":
                print()
                video_id = input("Video ID: ").strip()
                owner_id = input("Owner ID: ").strip()
                
                if not video_id or not owner_id:
                    print("Missing IDs")
                    continue
                
                categories = self.select_categories()
                if not categories:
                    print("No categories selected")
                    continue
                
                num = input("Number of reports: ").strip()
                
                if not num:
                    print("Missing report count")
                    continue
                
                self.report_video(video_id, owner_id, categories, num)
            
            elif choice == "2":
                self.proxy_mgr.fetch_with_getproxies_pro()
            elif choice == "3":
                self.proxy_mgr.list_proxies()
            elif choice == "4":
                self.proxy_mgr.clear_proxies()
            elif choice == "5":
                self.view_stats()
            elif choice == "6":
                self.download_csv()
            elif choice == "7":
                break

if __name__ == "__main__":
    reporter = TikTokReporter()
    reporter.menu()
