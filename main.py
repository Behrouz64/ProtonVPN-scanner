import os
import threading
import webbrowser
from concurrent.futures import ThreadPoolExecutor

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.factory import Factory
from kivy.properties import ListProperty, ObjectProperty, StringProperty

import scanner_core as core

# پس‌زمینه اصلی شفاف تا گرادیانِ KV دیده شود
Window.clearcolor = (0, 0, 0, 1)

PURPLE = (0.42, 0.16, 0.84, 1)
GREEN = (0.06, 0.72, 0.5, 1)
AMBER = (1.0, 0.8, 0.0, 1)
RED = (1.0, 0.2, 0.2, 1)
MUTED = (0.6, 0.62, 0.66, 1)
PING_FAST_MS = 150
PING_OK_MS = 300

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

<SecondaryButton@Button>:
    background_normal: ''
    background_color: (0.14, 0.14, 0.17, 1) if self.disabled else (0.22, 0.22, 0.28, 1)
    bold: True
    font_size: '12sp'

<ModeToggle@ToggleButton>:
    background_normal: ''
    background_down: ''
    background_color: (0.14, 0.14, 0.17, 1) if self.state == 'normal' else (0.42, 0.16, 0.84, 1)
    bold: True
    disabled_color: (0.4, 0.4, 0.45, 1)

<SectionTitle@Label>:
    size_hint_y: None
    height: dp(22)
    font_size: '12sp'
    bold: True
    color: 0.55, 0.6, 0.6, 1
    text_size: self.size
    halign: 'left'
    valign: 'middle'

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

<ResultCard>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(118)
    padding: dp(10)
    spacing: dp(6)
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
        size_hint_y: None
        height: dp(30)
        Label:
            text: root.name_text
            bold: True
            font_size: '16sp'
            color: 1, 1, 1, 1
            text_size: self.size
            halign: 'left'
            valign: 'middle'
        Label:
            text: f"{root.ping_text} ms"
            color: root.ping_color
            bold: True
            size_hint_x: 0.35
            text_size: self.size
            halign: 'right'
            valign: 'middle'
    Label:
        text: f"{root.ip_text}  •  {root.proto_text}"
        color: 0.7, 0.72, 0.75, 1
        font_size: '12sp'
        text_size: self.size
        halign: 'left'
        valign: 'middle'
        size_hint_y: None
        height: dp(18)
    BoxLayout:
        size_hint_y: None
        height: dp(36)
        spacing: dp(8)
        SecondaryButton:
            text: "COPY IP"
            on_release: app.copy_to_clipboard(root.ip_text, "IP copied")
        SecondaryButton:
            text: "COPY WG"
            on_release: app.copy_wireguard(root.server)
        SecondaryButton:
            text: "SAVE .CONF"
            on_release: app.save_wireguard(root.server)

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
    padding: dp(14)
    spacing: dp(8)

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
        height: dp(44)
        Label:
            text: "[b][color=10B981]ProtonVPN[/color] Scanner[/b]"
            markup: True
            font_size: '20sp'
            size_hint_x: 0.7
            text_size: self.size
            halign: 'left'
            valign: 'middle'
        Button:
            text: "ABOUT"
            size_hint_x: 0.3
            font_size: '12sp'
            bold: True
            background_normal: ''
            background_color: 0.2, 0.2, 0.25, 1
            on_release: app.show_about()

    # Step 1: database
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)
        ProtonButton:
            id: btn_load
            text: "1. LOAD DATABASE"
            on_release: app.start_fetch_thread()
        Label:
            id: lbl_db
            text: "No database loaded"
            color: 0.55, 0.6, 0.6, 1
            font_size: '12sp'
            size_hint_x: 0.42
            text_size: self.size
            halign: 'right'
            valign: 'middle'

    # Tier filter
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(6)
        ModeToggle:
            id: btn_free
            text: "FREE"
            group: 'mode'
            state: 'down'
            disabled: True
            on_release: app.set_mode('free')
        ModeToggle:
            id: btn_premium
            text: "PREMIUM"
            group: 'mode'
            disabled: True
            on_release: app.set_mode('paid')
        ModeToggle:
            id: btn_all
            text: "ALL"
            group: 'mode'
            disabled: True
            on_release: app.set_mode('all')

    # Region filters
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(8)
        Spinner:
            id: spin_continent
            text: "All Continents"
            values: ["All Continents"]
            disabled: True
            background_normal: ''
            background_color: 0.3, 0.3, 0.36, 1
            on_text: app.on_continent_change()
        Spinner:
            id: spin_country
            text: "All Countries"
            values: ["All Countries"]
            disabled: True
            background_normal: ''
            background_color: 0.3, 0.3, 0.36, 1

    # Step 2: scan
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)
        ProtonButton:
            id: btn_scan
            text: "2. START SCAN (500)"
            disabled: True
            on_release: app.start_scan()
        SecondaryButton:
            id: btn_next
            text: "NEXT 500"
            disabled: True
            on_release: app.next_batch()
        SecondaryButton:
            id: btn_reset
            text: "RESET"
            disabled: True
            background_color: 0.6, 0.18, 0.18, 1
            on_release: app.reset_scanner()

    ProgressBar:
        id: prog
        max: 1
        value: 0
        size_hint_y: None
        height: dp(8)

    Label:
        id: lbl_status
        text: "[color=888888]Load the database to unlock filters and start.[/color]"
        markup: True
        size_hint_y: None
        height: dp(26)
        font_size: '14sp'
        text_size: self.size
        halign: 'left'
        valign: 'middle'

    # WireGuard export
    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(8)
        TextInput:
            id: wg_key
            hint_text: "WireGuard private key (optional, written to .conf)"
            password: True
            multiline: False
            font_size: '13sp'
            size_hint_x: 0.55
        ProtonButton:
            id: btn_export
            text: "EXPORT TOP 15 (.conf)"
            font_size: '12sp'
            disabled: True
            on_release: app.export_top()

    # AmneziaWG obfuscation (optional): paste the Jc/Jmin/... lines from a working config
    TextInput:
        id: awg_params
        hint_text: "AmneziaWG params (optional): paste Jc, Jmin, Jmax, S1, S2, H1-H4 lines"
        multiline: True
        font_size: '12sp'
        size_hint_y: None
        height: dp(96)

    SectionTitle:
        id: lbl_results
        text: "RESULTS"

    ScrollView:
        id: scroll_view
        GridLayout:
            id: results_grid
            cols: 1
            spacing: dp(10)
            padding: [0, 0, 0, dp(8)]
            size_hint_y: None
            height: self.minimum_height
'''

SCAN_LOCKED_IDS = ('btn_load', 'btn_free', 'btn_premium', 'btn_all',
                   'spin_continent', 'spin_country', 'btn_scan', 'btn_reset',
                   'btn_export', 'wg_key', 'awg_params')


def ping_rgba(ms):
    if ms < PING_FAST_MS:
        return GREEN
    if ms < PING_OK_MS:
        return AMBER
    return RED


class ResultCard(BoxLayout):
    name_text = StringProperty('')
    ip_text = StringProperty('')
    ping_text = StringProperty('')
    proto_text = StringProperty('')
    ping_color = ListProperty(GREEN)
    server = ObjectProperty(None, allownone=True)


class ProtonScannerApp(App):
    def build(self):
        self.raw_data = []
        self.all_filtered = []   # سرورهای فعال بر اساس تب FREE/PREMIUM/ALL
        self.index = None        # core.RegionIndex برای اسپینرها
        self.mode = 'free'
        self.offset = 0
        self.scan_selection = (core.ALL_CONTINENTS, core.ALL_COUNTRIES)
        self.last_valid = []
        self.root = Builder.load_string(KV)
        return self.root

    @property
    def cache_path(self):
        return os.path.join(self.user_data_dir, core.CACHE_FILE)

    @property
    def export_dir(self):
        return os.path.join(self.user_data_dir, 'wireguard')

    def open_url(self, url):
        webbrowser.open(url)

    def show_about(self):
        Factory.AboutPopup().open()

    def wireguard_options(self):
        """کلید خصوصی و پارامترهای AmneziaWG را اعتبارسنجی می‌کند؛ در خطا ValueError برمی‌گرداند."""
        key = self.root.ids.wg_key.text.strip()
        if key and not core.is_valid_wg_key(key):
            raise ValueError("Invalid WireGuard private key")
        obfuscation = core.parse_obfuscation(self.root.ids.awg_params.text)
        return key, obfuscation

    def copy_to_clipboard(self, text, toast_msg):
        Clipboard.copy(text)
        self.set_status(f"[color=10B981]✅ {toast_msg}[/color]")

    def copy_wireguard(self, server):
        try:
            key, obfuscation = self.wireguard_options()
            conf = core.build_wireguard_config(server, key, obfuscation=obfuscation)
        except ValueError as e:
            self.set_status(f"[color=ff3333]❌ {e}[/color]")
            return
        Clipboard.copy(conf)
        self.set_status("[color=10B981]✅ Config copied[/color]")

    def save_wireguard(self, server):
        try:
            key, obfuscation = self.wireguard_options()
            path = core.write_wireguard_config(server, self.export_dir, key, obfuscation)
        except (ValueError, OSError) as e:
            self.set_status(f"[color=ff3333]❌ {e}[/color]")
            return
        self.set_status(f"[color=10B981]✅ Saved: {path}[/color]")

    def export_top(self):
        try:
            key, obfuscation = self.wireguard_options()
        except ValueError as e:
            self.set_status(f"[color=ff3333]❌ {e}[/color]")
            return
        top = core.top_results(self.last_valid, core.TOP_N)
        if not top:
            self.set_status("[color=ffcc00]⚠️ Nothing to export yet.[/color]")
            return
        try:
            written, skipped = core.export_wireguard_configs(top, self.export_dir, key, obfuscation)
        except OSError as e:
            self.set_status(f"[color=ff3333]❌ {e}[/color]")
            return
        kind = "AmneziaWG" if obfuscation else "WireGuard"
        msg = f"✅ Exported {len(written)} {kind} configs to {self.export_dir}"
        if skipped:
            msg += f" ({len(skipped)} skipped: no WG key)"
        self.set_status(f"[color=10B981]{msg}[/color]")

    @mainthread
    def set_status(self, text):
        self.root.ids.lbl_status.text = text

    @mainthread
    def set_progress(self, done, total):
        prog = self.root.ids.prog
        prog.max = max(total, 1)
        prog.value = done

    @mainthread
    def refresh_controls(self, busy=False, remaining=0):
        """وضعیت دکمه‌ها را بر اساس «در حال اسکن بودن» و «دیتابیس لود شده» تنظیم می‌کند."""
        ids = self.root.ids
        loaded = self.index is not None
        ids.btn_load.disabled = busy
        ids.btn_free.disabled = busy or not loaded
        ids.btn_premium.disabled = busy or not loaded
        ids.btn_all.disabled = busy or not loaded
        ids.spin_continent.disabled = busy or not loaded
        ids.spin_country.disabled = busy or not loaded
        ids.btn_scan.disabled = busy or not loaded
        ids.btn_next.disabled = busy or remaining <= 0
        ids.btn_reset.disabled = busy or not self.last_valid
        ids.btn_export.disabled = busy or not self.last_valid
        ids.wg_key.disabled = busy
        ids.awg_params.disabled = busy

    def start_fetch_thread(self):
        # بعد از اولین لود، دکمه RELOAD کش را دور می‌زند و دیتابیس تازه می‌گیرد
        force = self.index is not None
        self.root.ids.btn_load.disabled = True
        self.root.ids.btn_load.text = "LOADING..."
        self.set_status("[color=ffcc00]⏳ Loading database...[/color]")
        threading.Thread(target=self.fetch_data, args=(force,), daemon=True).start()

    def fetch_data(self, force=False):
        max_age = 0 if force else core.CACHE_MAX_AGE_S
        data, source = core.load_database(self.cache_path, max_age=max_age)
        if data is None:
            self.set_status("[color=ff3333]❌ Network error and no cache available.[/color]")
            self.finish_load(loaded=False)
            return
        self.raw_data = data
        self.finish_load(loaded=True, source=source)

    @mainthread
    def finish_load(self, loaded, source=''):
        self.root.ids.btn_load.text = "RELOAD DATABASE" if loaded else "1. LOAD DATABASE"
        if not loaded:
            self.refresh_controls()
            return

        self.update_menus()
        labels = {
            'cache': 'fast local cache',
            'network': 'fresh download',
            'stale-cache': 'older offline cache (network failed)',
        }
        self.set_status(f"[color=10B981]✅ Loaded from {labels.get(source, source)}. Adjust filters and scan.[/color]")
        self.refresh_controls()

    def set_mode(self, mode):
        self.mode = mode
        self.update_menus()

    def update_menus(self):
        if not self.raw_data:
            return
        ids = self.root.ids
        servers = core.extract_servers(self.raw_data)
        self.all_filtered = core.filter_by_tier(servers, self.mode)
        self.index = core.build_region_index(self.all_filtered)

        ids.lbl_db.text = f"{len(self.all_filtered)} {self.mode.upper()} servers"
        ids.spin_continent.values = [core.ALL_CONTINENTS] + core.continent_choices(self.index)
        ids.spin_continent.text = core.ALL_CONTINENTS
        self.on_continent_change()

    def on_continent_change(self):
        if self.index is None:
            return
        ids = self.root.ids
        ids.spin_country.values = core.country_choices(self.index, ids.spin_continent.text)
        ids.spin_country.text = core.ALL_COUNTRIES

    # =========================================================
    # اسکن
    # =========================================================
    def start_scan(self):
        ids = self.root.ids
        self.scan_selection = (ids.spin_continent.text, core.cc_from_label(ids.spin_country.text))
        self.offset = 0
        self.last_valid = []
        self.clear_results()
        self.refresh_controls(busy=True)
        threading.Thread(target=self.run_scanner, daemon=True).start()

    def next_batch(self):
        self.offset += core.BATCH_SIZE
        self.refresh_controls(busy=True)
        threading.Thread(target=self.run_scanner, daemon=True).start()

    def reset_scanner(self):
        self.offset = 0
        self.last_valid = []
        self.clear_results()
        self.set_progress(0, 1)
        self.set_status("[color=10B981]✅ Scanner reset. Ready to start again.[/color]")
        self.refresh_controls()

    @mainthread
    def clear_results(self):
        self.root.ids.results_grid.clear_widgets()
        self.root.ids.lbl_results.text = "RESULTS"

    def run_scanner(self):
        continent, country = self.scan_selection
        servers = core.filter_servers(self.all_filtered, continent, country,
                                      self.index.active_map if self.index else {})
        if not servers:
            self.set_status("[color=ffcc00]⚠️ No servers found for this filter.[/color]")
            self.refresh_controls()
            return

        batch = servers[self.offset:self.offset + core.BATCH_SIZE]
        if not batch:
            self.set_status("[color=ffcc00]⚠️ Reached the end of the server list.[/color]")
            self.refresh_controls()
            return

        total = len(batch)
        done_lock = threading.Lock()
        done = 0
        alive = []

        self.set_progress(0, total)
        self.set_status(f"[color=ffcc00]🚀 Scanning {total} servers (turn VPN OFF!)[/color]")

        def check_server(srv):
            nonlocal done
            ping, proto = core.smart_ping(srv['ip'])
            with done_lock:
                done += 1
                current = done
            if current % 10 == 0 or current == total:
                self.set_progress(current, total)
            # فیلتر پینگ‌های تقلبی
            if ping is not None and ping >= core.MIN_PLAUSIBLE_PING_MS:
                with done_lock:
                    alive.append({**srv, 'ping': ping, 'proto': proto})

        with ThreadPoolExecutor(max_workers=core.SCAN_WORKERS) as ex:
            list(ex.map(check_server, batch))

        remaining = len(servers) - (self.offset + total)
        if alive:
            self.last_valid = core.merge_results(self.last_valid, alive)
            self.show_results(core.top_results(self.last_valid, core.TOP_N), len(self.last_valid))
            self.set_status(f"[color=10B981]✅ Found {len(alive)} alive in this batch. Showing top {core.TOP_N}.[/color]")
        else:
            self.set_status(f"[color=ff3333]❌ All {total} servers were dead or fake (<{core.MIN_PLAUSIBLE_PING_MS}ms).[/color]")

        self.refresh_controls(remaining=remaining)

    @mainthread
    def show_results(self, servers, total_alive):
        grid = self.root.ids.results_grid
        grid.clear_widgets()
        for srv in servers:
            card = ResultCard(
                name_text=srv['name'],
                ip_text=srv['ip'],
                ping_text=str(srv['ping']),
                proto_text=srv['proto'],
                ping_color=ping_rgba(srv["ping"]),
                server=srv,
            )
            grid.add_widget(card)
        self.root.ids.lbl_results.text = f"RESULTS  •  top {len(servers)} of {total_alive} alive"


if __name__ == '__main__':
    ProtonScannerApp().run()
