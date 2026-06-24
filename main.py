import threading
import requests
import socket
import time
import re
import random
import webbrowser
import json
import os
from concurrent.futures import ThreadPoolExecutor

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.clock import mainthread, Clock
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.factory import Factory

# پس‌زمینه اصلی شفاف تا گرادیانِ KV دیده شود
Window.clearcolor = (0, 0, 0, 1)

# لینک‌های ضد فیلتر و کمکی برای دانلود از گیت‌هاب در ایران
GITHUB_MIRRORS = [
    "https://fastly.jsdelivr.net/gh/tn3w/ProtonVPN-IPs@master/protonvpn_logicals.json",
    "https://raw.githubusercontent.com/tn3w/ProtonVPN-IPs/refs/heads/master/protonvpn_logicals.json",
    "https://gh-proxy.com/https://raw.githubusercontent.com/tn3w/ProtonVPN-IPs/refs/heads/master/protonvpn_logicals.json"
]

CACHE_FILE = "cache_github.json"

CC_TO_NAME = {
    'US': 'United States', 'CA': 'Canada', 'MX': 'Mexico', 'CR': 'Costa Rica', 'PA': 'Panama', 'PR': 'Puerto Rico',
    'DE': 'Germany', 'NL': 'Netherlands', 'CH': 'Switzerland', 'FR': 'France', 'UK': 'United Kingdom', 'GB': 'Great Britain',
    'SE': 'Sweden', 'IT': 'Italy', 'ES': 'Spain', 'PL': 'Poland', 'RO': 'Romania', 'IS': 'Iceland', 'DK': 'Denmark',
    'NO': 'Norway', 'FI': 'Finland', 'IE': 'Ireland', 'PT': 'Portugal', 'AT': 'Austria', 'CZ': 'Czechia', 'SK': 'Slovakia',
    'HU': 'Hungary', 'GR': 'Greece', 'BG': 'Bulgaria', 'RS': 'Serbia', 'MD': 'Moldova', 'UA': 'Ukraine', 'EE': 'Estonia',
    'LV': 'Latvia', 'LT': 'Lithuania', 'BE': 'Belgium', 'LU': 'Luxembourg', 'AL': 'Albania', 'MK': 'North Macedonia',
    'JP': 'Japan', 'SG': 'Singapore', 'HK': 'Hong Kong', 'KR': 'South Korea', 'TW': 'Taiwan', 'IL': 'Israel', 'AE': 'UAE',
    'IN': 'India', 'MY': 'Malaysia', 'VN': 'Vietnam', 'TH': 'Thailand', 'ID': 'Indonesia', 'PH': 'Philippines', 'KH': 'Cambodia',
    'MN': 'Mongolia', 'GE': 'Georgia', 'CY': 'Cyprus', 'TR': 'Turkey', 'KZ': 'Kazakhstan',
    'BR': 'Brazil', 'AR': 'Argentina', 'CO': 'Colombia', 'CL': 'Chile', 'PE': 'Peru', 'EC': 'Ecuador', 'VE': 'Venezuela',
    'UY': 'Uruguay', 'PY': 'Paraguay',
    'ZA': 'South Africa', 'EG': 'Egypt', 'NG': 'Nigeria', 'KE': 'Kenya', 'MA': 'Morocco', 'DZ': 'Algeria', 'TN': 'Tunisia',
    'AU': 'Australia', 'NZ': 'New Zealand', 'UNK': 'Unknown'
}

CONTINENTS = {
    'North America': ['US', 'CA', 'MX', 'CR', 'PA', 'PR'],
    'Europe': ['DE', 'NL', 'CH', 'FR', 'UK', 'GB', 'SE', 'IT', 'ES', 'PL', 'RO', 'IS', 'DK', 'NO', 'FI', 'IE', 'PT', 'AT', 'CZ', 'SK', 'HU', 'GR', 'BG', 'RS', 'MD', 'UA', 'EE', 'LV', 'LT', 'BE', 'LU', 'AL', 'MK'],
    'Asia': ['JP', 'SG', 'HK', 'KR', 'TW', 'IL', 'AE', 'IN', 'MY', 'VN', 'TH', 'ID', 'PH', 'KH', 'MN', 'GE', 'CY', 'TR', 'KZ'],
    'South America': ['BR', 'AR', 'CO', 'CL', 'PE', 'EC', 'VE', 'UY', 'PY'],
    'Africa': ['ZA', 'EG', 'NG', 'KE', 'MA', 'DZ', 'TN'],
    'Oceania': ['AU', 'NZ']
}

# رابط کاربری KV
KV = '''
<ProtonButton@Button>:
    background_normal: ''
    background_color: 0,0,0,0
    bold: True
    canvas.before:
        Color:
            rgba: (0.2, 0.2, 0.25, 1) if self.disabled else ((0.06, 0.72, 0.5, 1) if self.state == 'normal' else (0.04, 0.55, 0.38, 1))
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8]

<SocialButton@Button>:
    background_normal: ''
    background_color: 0,0,0,0
    bold: True
    color: 0.9, 0.9, 0.9, 1
    canvas.before:
        Color:
            rgba: (0.15, 0.15, 0.18, 1) if self.state == 'normal' else (0.2, 0.2, 0.25, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [6]

<ResultCard@BoxLayout>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(90)
    padding: dp(10)
    spacing: dp(5)
    name_text: ''
    ip_text: ''
    ping_text: ''
    proto_text: ''
    canvas.before:
        Color:
            rgba: 0.1, 0.12, 0.15, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [12]
        Color:
            rgba: 0.06, 0.72, 0.5, 0.3
        Line:
            width: 1.1
            rounded_rectangle: (self.x, self.y, self.width, self.height, 12)
    BoxLayout:
        orientation: 'horizontal'
        Label:
            text: root.name_text
            bold: True
            font_size: '15sp'
            color: 1, 1, 1, 1
            text_size: self.size
            halign: 'left'
            valign: 'middle'
        Label:
            text: f"{root.ping_text}ms | {root.proto_text}"
            color: 0.06, 0.72, 0.5, 1
            bold: True
            size_hint_x: 0.5
            text_size: self.size
            halign: 'right'
            valign: 'middle'
    BoxLayout:
        orientation: 'horizontal'
        spacing: dp(10)
        Button:
            text: "COPY NAME"
            font_size: '12sp'
            background_normal: ''
            background_color: 0.2, 0.2, 0.25, 1
            on_release: app.copy_to_clipboard(root.name_text, "Server Name Copied!")
        Button:
            text: "COPY IP"
            font_size: '12sp'
            background_normal: ''
            background_color: 0.2, 0.2, 0.25, 1
            on_release: app.copy_to_clipboard(root.ip_text, "IP Address Copied!")

<AboutPopup@ModalView>:
    size_hint: 0.85, 0.35
    auto_dismiss: True
    background_color: 0,0,0,0
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        canvas.before:
            Color:
                rgba: 0.12, 0.12, 0.15, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [15]
            Color:
                rgba: 0.06, 0.72, 0.5, 1
            Line:
                width: 1.5
                rounded_rectangle: (self.x, self.y, self.width, self.height, 15)
        Label:
            text: "[b][color=10B981]ProtonVPN[/color] Scanner v0.0.1[/b]"
            markup: True
            font_size: '18sp'
            size_hint_y: 0.2
        Label:
            text: "Follow us for updates, support, and new bypassing tools!"
            text_size: self.size
            halign: 'center'
            valign: 'middle'
            size_hint_y: 0.3
            color: 0.8, 0.8, 0.8, 1
        BoxLayout:
            orientation: 'horizontal'
            spacing: dp(10)
            size_hint_y: 0.3
            SocialButton:
                text: "Telegram"
                on_release: app.open_url("https://t.me/ProtonVpnScanner")
            SocialButton:
                text: "Twitter (X)"
                on_release: app.open_url("https://x.com/BehrouzSdn")
        Button:
            text: "CLOSE"
            size_hint_y: 0.2
            background_normal: ''
            background_color: 0.2, 0.2, 0.25, 1
            on_release: root.dismiss()

BoxLayout:
    orientation: 'vertical'
    padding: dp(15)
    spacing: dp(10)
    
    # گرادیان ساده
    canvas.before:
        Color:
            rgba: 0.05, 0.05, 0.06, 1
        Rectangle:
            pos: self.x, self.y + self.height * 0.66
            size: self.width, self.height * 0.34
        Color:
            rgba: 0.03, 0.1, 0.08, 1
        Rectangle:
            pos: self.x, self.y + self.height * 0.33
            size: self.width, self.height * 0.33
        Color:
            rgba: 0.02, 0.15, 0.1, 1
        Rectangle:
            pos: self.x, self.y
            size: self.width, self.height * 0.33

    # Header
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        Label:
            text: "[b][color=10B981]ProtonVPN[/color] Scanner v0.0.1[/b]"
            markup: True
            font_size: '20sp'
            size_hint_x: 0.75
            text_size: self.size
            halign: 'left'
            valign: 'middle'
        Button:
            text: "ABOUT"
            size_hint_x: 0.25
            font_size: '12sp'
            bold: True
            background_normal: ''
            background_color: 0.2, 0.2, 0.25, 1
            on_release: app.show_about()

    # DB Load Button
    ProtonButton:
        id: btn_load
        text: "1. LOAD GITHUB DATABASE"
        size_hint_y: None
        height: dp(45)
        on_release: app.start_fetch_thread()

    # دکمه‌های بنفش پروتون
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(8)
        Button:
            id: btn_free
            text: "FREE"
            bold: True
            disabled: True
            background_normal: ''
            background_color: 0.2, 0.2, 0.25, 1
            on_release: app.set_mode('free')
        Button:
            id: btn_premium
            text: "PREMIUM"
            bold: True
            disabled: True
            background_normal: ''
            background_color: 0.2, 0.2, 0.25, 1
            on_release: app.set_mode('paid')
        Button:
            id: btn_all
            text: "ALL"
            bold: True
            disabled: True
            background_normal: ''
            background_color: 0.2, 0.2, 0.25, 1
            on_release: app.set_mode('all')

    # Filters
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(8)
        Spinner:
            id: spin_continent
            text: "All Continents"
            values: ["All Continents"]
            disabled: True
            background_color: 0.6, 0.4, 0.9, 1
            on_text: app.on_continent_change()
        Spinner:
            id: spin_country
            text: "All Countries"
            values: ["All Countries"]
            disabled: True
            background_color: 0.6, 0.4, 0.9, 1

    # Scan Button
    ProtonButton:
        id: btn_scan
        text: "2. START SCAN (Max 500)"
        size_hint_y: None
        height: dp(50)
        disabled: True
        on_release: app.start_scan_thread()

    # دکمه‌های کنترل ادامه و ریست
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(8)
        Button:
            id: btn_next
            text: "NEXT 500"
            bold: True
            disabled: True
            background_normal: ''
            background_color: 0.4, 0.4, 0.4, 1
            on_release: app.next_batch()
        Button:
            id: btn_reset
            text: "🔄 RESET"
            bold: True
            disabled: True
            background_normal: ''
            background_color: 0.8, 0.2, 0.2, 1
            on_release: app.reset_scanner()

    # Status Label
    Label:
        id: lbl_status
        text: "[color=888888]Load database to unlock filters and begin...[/color]"
        markup: True
        size_hint_y: None
        height: dp(30)
        font_size: '14sp'

    # Results Area
    ScrollView:
        id: scroll_view
        GridLayout:
            id: results_grid
            cols: 1
            spacing: dp(10)
            size_hint_y: None
            height: self.minimum_height
'''

class ProtonScannerApp(App):
    def build(self):
        self.raw_data = []
        self.all_filtered = []
        self.active_map = {}
        self.cc_counts = {}
        self.cont_counts = {}
        self.mode = 'free'
        self.offset = 0
        self.last_valid = []
        self.root = Builder.load_string(KV)
        return self.root

    def open_url(self, url):
        webbrowser.open(url)

    def show_about(self):
        popup = Factory.AboutPopup()
        popup.open()

    def copy_to_clipboard(self, text, toast_msg):
        Clipboard.copy(text)
        self.set_status(f"[color=10B981]✅ {toast_msg}[/color]")

    @mainthread
    def set_status(self, text):
        self.root.ids.lbl_status.text = text

    def set_mode(self, mode):
        self.mode = mode
        active_color = (0.42, 0.16, 0.84, 1)
        inactive_color = (0.2, 0.2, 0.25, 1)
        
        self.root.ids.btn_free.background_color = active_color if mode == 'free' else inactive_color
        self.root.ids.btn_premium.background_color = active_color if mode == 'paid' else inactive_color
        self.root.ids.btn_all.background_color = active_color if mode == 'all' else inactive_color
        
        self.update_menus()

    def start_fetch_thread(self):
        self.root.ids.btn_load.disabled = True
        self.root.ids.btn_load.text = "LOADING..."
        self.set_status("[color=ffcc00]⏳ Checking database cache...[/color]")
        threading.Thread(target=self.fetch_data, daemon=True).start()

    def fetch_data(self):
        use_cache = False
        
        if os.path.exists(CACHE_FILE):
            file_age = time.time() - os.path.getmtime(CACHE_FILE)
            if file_age < 3600:
                use_cache = True

        if use_cache:
            self.set_status("[color=10B981]⏳ Loading database from fast local cache...[/color]")
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.raw_data = json.load(f)
                self.trigger_update_menus()
                return
            except Exception:
                self.set_status("[color=ffcc00]⚠️ Cache corrupted, connecting to network...[/color]")

        self.set_status("[color=ffcc00]⏳ Downloading fresh database (bypassing filter)...[/color]")
        
        success = False
        # تلاش برای دانلود از لینک‌های کمکی یکی پس از دیگری
        for url in GITHUB_MIRRORS:
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    self.raw_data = data.get("LogicalServers", data) if isinstance(data, dict) else data
                    
                    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(self.raw_data, f)
                    
                    success = True
                    self.trigger_update_menus()
                    break
            except:
                continue
                
        if not success:
            self.set_status("[color=ff3333]❌ Network Error: Unable to fetch database.[/color]")
            if os.path.exists(CACHE_FILE):
                self.set_status("[color=ffcc00]⚠️ Loading older offline cache...[/color]")
                try:
                    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                        self.raw_data = json.load(f)
                    self.trigger_update_menus()
                except:
                    self.reset_load_btn()
            else:
                self.reset_load_btn()

    @mainthread
    def reset_load_btn(self):
        self.root.ids.btn_load.disabled = False
        self.root.ids.btn_load.text = "1. LOAD GITHUB DATABASE"

    @mainthread
    def trigger_update_menus(self):
        self.root.ids.btn_free.disabled = False
        self.root.ids.btn_premium.disabled = False
        self.root.ids.btn_all.disabled = False
        self.root.ids.spin_continent.disabled = False
        self.root.ids.spin_country.disabled = False
        
        self.set_mode('free')
        
        self.root.ids.btn_load.text = "DATABASE LOADED"
        self.root.ids.btn_load.background_color = (0.2, 0.6, 0.3, 1)
        self.root.ids.btn_scan.disabled = False
        self.set_status("[color=10B981]✅ Ready! Adjust filters and Start Scan.[/color]")

    def update_menus(self):
        if not self.raw_data: return

        targets = []
        countries_set = set()
        self.cc_counts = {}

        for item in self.raw_data:
            if item.get("Status") != 1: continue
            try: ip = item['Servers'][0]['EntryIP']
            except: continue
            
            name = item.get("Name", "Unknown")
            is_free = (item.get("Tier", 0) == 0)

            cc_match = re.match(r'^([A-Z]{2})', name.upper())
            cc = cc_match.group(1) if cc_match else "UNK"

            if self.mode == "free" and not is_free: continue
            if self.mode == "paid" and is_free: continue

            targets.append({'ip': ip, 'name': name, 'cc': cc})
            countries_set.add(cc)
            self.cc_counts[cc] = self.cc_counts.get(cc, 0) + 1

        self.all_filtered = targets

        self.active_map = {}
        self.cont_counts = {}
        for cont, cc_list in CONTINENTS.items():
            found = [c for c in cc_list if c in countries_set]
            if found: 
                self.active_map[cont] = found
                self.cont_counts[cont] = sum(self.cc_counts.get(c, 0) for c in found)

        sorted_conts = sorted(self.active_map.keys(), key=lambda x: self.cont_counts.get(x, 0), reverse=True)
        self.root.ids.spin_continent.values = ['All Continents'] + sorted_conts
        self.root.ids.spin_continent.text = 'All Continents'
        self.on_continent_change()

    def get_display_name(self, cc):
        if cc == 'UNK' or cc == 'All Countries': return cc
        return f"{CC_TO_NAME.get(cc, cc)} ({cc})"

    def extract_cc(self, display_text):
        if display_text in ('All Countries', 'UNK'): return display_text
        match = re.search(r'\(([A-Z]{2})\)$', display_text)
        return match.group(1) if match else display_text

    def on_continent_change(self):
        if not hasattr(self, 'active_map'): return
        
        text = self.root.ids.spin_continent.text
        display_list = ['All Countries']
        
        if text == 'All Continents':
            all_c = set(t['cc'] for t in self.all_filtered if t['cc'] != 'UNK')
            sorted_cc = sorted(list(all_c), key=lambda c: self.cc_counts.get(c, 0), reverse=True)
            display_list.extend([self.get_display_name(c) for c in sorted_cc])
        else:
            countries_in_cont = self.active_map.get(text, [])
            sorted_cc = sorted(countries_in_cont, key=lambda c: self.cc_counts.get(c, 0), reverse=True)
            display_list.extend([self.get_display_name(c) for c in sorted_cc])

        self.root.ids.spin_country.values = display_list
        self.root.ids.spin_country.text = 'All Countries'
        self.offset = 0

    # =========================================================
    # پورت 443 برای TCP و پورت 80 برای UDP
    # =========================================================
    def smart_ping(self, ip, timeout=1.5):
        best_ping = 9999
        best_proto = None

        # 1. Test TCP (Port 443)
        try:
            st = time.time()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            if s.connect_ex((ip, 443)) == 0:
                p = int((time.time() - st) * 1000)
                if p < best_ping:
                    best_ping = p
                    best_proto = 'TCP:443'
            s.close()
        except: pass

        # 2. Test UDP (Port 80)
        try:
            st = time.time()
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(timeout)
            # پکت جادویی پروتون
            s.sendto(b'\x38\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', (ip, 80))
            s.recvfrom(1024)
            p = int((time.time() - st) * 1000)
            if p < best_ping:
                best_ping = p
                best_proto = 'UDP:80'
            s.close()
        except: pass

        if best_ping < 9999:
            return best_ping, best_proto
        return None, None

    def reset_scanner(self):
        self.offset = 0
        self.last_valid = []
        self.root.ids.results_grid.clear_widgets()
        self.set_status("[color=10B981]✅ Scanner Reset. Ready to start again![/color]")
        self.root.ids.btn_scan.disabled = False
        self.root.ids.btn_next.disabled = True
        self.root.ids.btn_reset.disabled = True

    def start_scan_thread(self):
        self.root.ids.btn_scan.disabled = True
        self.root.ids.btn_next.disabled = True
        self.root.ids.btn_reset.disabled = True
        self.root.ids.btn_load.disabled = True
        self.root.ids.results_grid.clear_widgets()
        threading.Thread(target=self.run_scanner, daemon=True).start()

    def next_batch(self):
        self.offset += 500
        self.start_scan_thread()

    def run_scanner(self):
        sel_cont = self.root.ids.spin_continent.text
        sel_cc = self.extract_cc(self.root.ids.spin_country.text)

        filtered = []
        for t in self.all_filtered:
            if sel_cont != 'All Continents' and t['cc'] not in self.active_map.get(sel_cont, []):
                continue
            if sel_cc != 'All Countries' and t['cc'] != sel_cc:
                continue
            filtered.append(t)

        if not filtered:
            self.set_status("[color=ffcc00]⚠️ No servers found for this filter.[/color]")
            self.reset_scan_btn()
            return

        batch = filtered[self.offset:self.offset+500]

        if not batch:
            self.set_status("[color=ffcc00]⚠️ Reached the end of the server list.[/color]")
            self.reset_scan_btn()
            return

        self.set_status(f"[color=ffcc00]🚀 Scanning {len(batch)} servers (Turn VPN OFF!)[/color]")

        valid_servers = []
        completed = 0

        def check_server(srv):
            nonlocal completed
            ping, proto = self.smart_ping(srv['ip'])
            completed += 1
            
            if completed % 15 == 0 or completed == len(batch):
                self.set_status(f"[color=10B981]⏳ Scanning... {completed}/{len(batch)}[/color]")
                
            if ping is not None:
                # 🎯 فیلتر پینگ‌های تقلبی (زیر 100 میلی‌ثانیه حذف می‌شود)
                if ping >= 100:
                    valid_servers.append({'name': srv['name'], 'ip': srv['ip'], 'ping': ping, 'proto': proto})

        with ThreadPoolExecutor(max_workers=8) as ex:
            ex.map(check_server, batch)

        if valid_servers:
            self.last_valid.extend(valid_servers)
            uniq = {v['name']: v for v in self.last_valid}
            self.last_valid = list(uniq.values())
            
            top_15 = sorted(self.last_valid, key=lambda x: x['ping'])[:15]
            self.display_results(top_15)
            self.set_status(f"[color=10B981]✅ Found {len(valid_servers)} alive in this batch. Showing Top 15.[/color]")
        else:
            self.set_status(f"[color=ff3333]❌ All {len(batch)} servers were DEAD or FAKE (<100ms).[/color]")

        remaining = len(filtered) - (self.offset + len(batch))
        self.reset_scan_btn(remaining)

    @mainthread
    def display_results(self, servers):
        grid = self.root.ids.results_grid
        for srv in servers:
            card = Factory.ResultCard()
            card.name_text = srv['name']
            card.ip_text = srv['ip']
            card.ping_text = str(srv['ping'])
            card.proto_text = srv['proto']
            grid.add_widget(card)

    @mainthread
    def reset_scan_btn(self, remaining=0):
        self.root.ids.btn_scan.disabled = False
        self.root.ids.btn_load.disabled = False
        self.root.ids.btn_reset.disabled = False
        
        if remaining > 0:
            self.root.ids.btn_next.disabled = False
        else:
            self.root.ids.btn_next.disabled = True

if __name__ == '__main__':
    ProtonScannerApp().run()
