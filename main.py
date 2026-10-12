"""ProtonVPN Scanner نسخه‌ی 1.0.2 با Flet — رابط دو زبانه (فارسی و English).

منطق دیتابیس، پینگ و کانفیگ در scanner_core.py است؛ این فایل فقط وضعیت و رابط را مدیریت می‌کند.
اجرا: python main.py
"""
import asyncio
import os
import traceback

import flet as ft

# اگر یکی از ماژول‌ها بارگذاری نشود (مثلاً یک پکیج که در APK نیست)، متن خطا روی صفحه نشان داده می‌شود
# و برنامه بی‌صدا با صفحه‌ی سیاه متوقف نمی‌شود.
try:
    import app_settings
    import guide_content
    import i18n
    import scanner_core as core
    import ui_parts as ui
except Exception:
    IMPORT_ERROR = traceback.format_exc()
else:
    IMPORT_ERROR = None

SETTINGS_KEY = 'settings'
CONFIG_ERROR_KEYS = {
    'no_public_key': 'err_no_public_key',
    'bad_public_key': 'err_bad_public_key',
    'bad_ip': 'err_bad_ip',
    'bad_private_key': 'err_key_invalid',
    'key_file_exists': 'err_key_file_exists',
}
QR_HINT_KEYS = {'config': 'qr_hint_config', 'link': 'qr_hint_link'}
AWG_ERROR_KEYS = {'number': 'err_awg_number', 'range': 'err_awg_range', 'order': 'err_awg_order'}
TAB_SCAN, TAB_SERVERS, TAB_SETTINGS, TAB_GUIDE = range(4)


class UserError(Exception):
    """خطایی که متنش از i18n گرفته می‌شود. key کلید متن و values مقادیر آن است."""

    def __init__(self, key, **values):
        super().__init__(key)
        self.key = key
        self.values = values


class ScannerApp:
    def __init__(self, page):
        self.page = page
        self.settings = app_settings.default_settings()
        self.lang = self.settings['language']
        self.tab = TAB_SCAN
        self.private_key = ''
        self.mode = 'free'
        self.raw_data = None
        self.loaded_once = False
        self.index = None
        self.all_filtered = []
        self.continent = core.ALL_CONTINENTS
        self.country = core.ALL_COUNTRIES
        self.scan_selection = (core.ALL_CONTINENTS, core.ALL_COUNTRIES)
        self.offset = 0
        self.remaining = 0
        self.last_valid = []
        self.busy = False
        self.progress = (0, 1)
        self.status = ('muted', 'load_first', {})
        self.support_dir = os.path.join(os.path.expanduser('~'), '.protonvpn-scanner')
        self.clipboard = ft.Clipboard()
        self.prefs = ft.SharedPreferences()
        self.launcher = ft.UrlLauncher()
        self.storage = ft.StoragePaths()

    # ---------- کمک‌ها ----------
    def t(self, key, **values):
        return i18n.t(self.lang, key, **values)

    @property
    def cache_path(self):
        return os.path.join(self.support_dir, core.CACHE_FILE)

    @property
    def export_dir(self):
        return os.path.join(self.support_dir, 'wireguard')

    def obfuscation(self):
        return app_settings.obfuscation_for_build(self.settings)

    def selected_value(self, control):
        return next(iter(control.selected))

    # ---------- راه‌اندازی ----------
    async def start(self):
        page = self.page
        page.title = 'ProtonVPN Scanner'
        page.fonts = {ui.PERSIAN_FONT: ui.PERSIAN_FONT_FILE}
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = ui.BG
        page.padding = 0
        try:  # روی دسکتاپ اندازه‌ی پنجره مثل یک برنامه‌ی موبایلی؛ در وب این تنظیم لازم نیست
            page.window.width = 440
            page.window.height = 860
            page.window.min_width = 360
        except Exception:
            pass

        page.services.extend([self.clipboard, self.prefs, self.launcher, self.storage])
        # اول رابط با تنظیمات پیش‌فرض ساخته می‌شود تا صفحه‌ی خالی نماند؛ تنظیمات ذخیره‌شده بعداً می‌آید
        self.build()
        page.update()
        await self.load_saved_state()

    async def load_saved_state(self):
        await self.resolve_support_dir()
        saved = app_settings.load_settings(await self.read_settings())
        if saved != self.settings:
            self.settings = saved
            self.lang = saved['language']
            self.build()
            self.page.update()

    async def resolve_support_dir(self):
        try:
            path = await asyncio.wait_for(self.storage.get_application_support_directory(), timeout=5)
            if path:
                self.support_dir = path
        except Exception:
            pass  # مسیر پیش‌فرض کافی است؛ خطای ذخیره‌سازی بعداً در پیام نشان داده می‌شود

    async def read_settings(self):
        try:
            return await asyncio.wait_for(self.prefs.get(SETTINGS_KEY), timeout=5)
        except Exception:
            return None

    async def save_settings(self):
        try:
            await self.prefs.set(SETTINGS_KEY, app_settings.dump_settings(self.settings))
        except Exception:
            pass  # تنظیمات فقط برای دفعه‌ی بعد است؛ نبودن آن نباید برنامه را متوقف کند

    # ---------- ساخت رابط ----------
    def build(self):
        page = self.page
        page.rtl = self.lang == 'fa'
        page.theme = ui.theme()
        self.servers_destination = ft.NavigationBarDestination(
            icon=ft.Icons.LIST_ALT, label=self.t('nav_servers'))
        self.scan_tab = self.build_scan_tab()
        self.servers_tab = self.build_servers_tab()
        self.settings_tab = self.build_settings_tab()
        self.guide_tab = self.build_guide_tab()
        self.body = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=12,
                              controls=[self.current_tab()])
        page.navigation_bar = ft.NavigationBar(
            selected_index=self.tab,
            on_change=self.on_tab,
            bgcolor=ui.SURFACE,
            indicator_color=ui.PRIMARY,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.RADAR, label=self.t('nav_scan')),
                self.servers_destination,
                ft.NavigationBarDestination(icon=ft.Icons.TUNE, label=self.t('nav_settings')),
                ft.NavigationBarDestination(icon=ft.Icons.MENU_BOOK, label=self.t('nav_guide')),
            ],
        )
        header = ft.Container(
            padding=ft.Padding.only(left=16, right=16, top=18, bottom=6),
            content=ft.Row(
                [
                    ft.Image(src='icon.png', width=40, height=40, border_radius=10,
                             fit=ft.BoxFit.COVER),
                    ft.Column(
                        [
                            ft.Text(self.t('app_name'), size=18, weight=ft.FontWeight.BOLD, color=ui.TEXT),
                            ft.Text(self.t('about_version', version=core.APP_VERSION), size=12,
                                    color=ui.TEXT_MUTED),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=12,
            ),
        )
        page.controls.clear()
        page.add(ft.Container(content=ft.Column([header, self.body], spacing=0, expand=True),
                              padding=ft.Padding.symmetric(horizontal=16), expand=True))
        self.sync()

    def current_tab(self):
        return {
            TAB_SCAN: self.scan_tab,
            TAB_SERVERS: self.servers_tab,
            TAB_SETTINGS: self.settings_tab,
            TAB_GUIDE: self.guide_tab,
        }[self.tab]

    def build_scan_tab(self):
        t = self.t
        self.btn_load = ui.primary_button(t('btn_load'), self.on_load, icon=ft.Icons.CLOUD_DOWNLOAD)
        self.db_text = ui.body_text('', color=ui.TEXT_MUTED, size=12)
        self.mode_seg = ft.SegmentedButton(
            segments=[
                ft.Segment(value='free', label=ft.Text(t('mode_free'))),
                ft.Segment(value='paid', label=ft.Text(t('mode_paid'))),
                ft.Segment(value='all', label=ft.Text(t('mode_all'))),
            ],
            selected=[self.mode],
            on_change=self.on_mode,
        )
        self.continent_dd = ft.Dropdown(
            value=self.continent, options=self.continent_options(), on_select=self.on_continent,
            expand=True, border_color=ui.BORDER, focused_border_color=ui.PRIMARY, bgcolor=ui.SURFACE,
            color=ui.TEXT,
        )
        self.country_dd = ft.Dropdown(
            value=self.country, options=self.country_options(), on_select=self.on_country,
            expand=True, border_color=ui.BORDER, focused_border_color=ui.PRIMARY, bgcolor=ui.SURFACE,
            color=ui.TEXT,
        )
        self.btn_scan = ui.primary_button(t('btn_scan'), self.on_scan, icon=ft.Icons.RADAR)
        self.btn_next = ui.secondary_button(t('btn_next'), self.on_next, icon=ft.Icons.SKIP_NEXT)
        self.btn_reset = ui.secondary_button(t('btn_reset'), self.on_reset_scan, icon=ft.Icons.RESTART_ALT,
                                             danger=True)
        self.progress_bar = ft.ProgressBar(value=0, color=ui.PRIMARY, bgcolor=ui.SURFACE_HIGH,
                                           border_radius=4)
        self.status_text = ft.Text('', size=13, weight=ft.FontWeight.BOLD)
        self.result_text = ui.body_text('', color=ui.TEXT, size=14, weight=ft.FontWeight.BOLD)
        self.result_button = ui.primary_button(t('btn_view_results'), self.on_view_results,
                                               icon=ft.Icons.LIST_ALT)
        self.result_banner = ft.Container(
            content=ft.Column([self.result_text, self.result_button], spacing=10),
            visible=False,
            bgcolor=ui.blend(ui.SUCCESS, ui.SURFACE, 0.18),
            border=ft.Border.all(1, ui.blend(ui.SUCCESS, ui.SURFACE, 0.6)),
            border_radius=16,
            padding=16,
        )
        return ft.Column(
            [
                self.result_banner,
                ui.card(ui.heading(t('step_database')),
                        ft.Row([self.btn_load], spacing=8),
                        self.db_text),
                ui.card(ui.heading(t('filter_title')),
                        self.mode_seg,
                        ft.Row([self.continent_dd, self.country_dd], spacing=8)),
                ui.card(ui.heading(t('step_scan')),
                        ft.Container(
                            content=ui.body_text(t('vpn_warning'), color=ui.WARNING, size=13),
                            bgcolor=ui.blend(ui.WARNING, ui.SURFACE, 0.14),
                            border_radius=12, padding=12,
                        ),
                        ft.Row([self.btn_scan], spacing=8),
                        ft.Row([self.btn_next, self.btn_reset], spacing=8),
                        self.progress_bar,
                        self.status_text),
            ],
            spacing=12,
        )

    def build_servers_tab(self):
        t = self.t
        self.key_field = ft.TextField(
            label=t('key_label'), value=self.private_key, password=True, can_reveal_password=True,
            on_change=self.on_key_change, border_color=ui.BORDER, focused_border_color=ui.PRIMARY,
            bgcolor=ui.SURFACE, color=ui.TEXT, text_size=13,
        )
        self.btn_export = ui.secondary_button(t('btn_export'), self.on_export, icon=ft.Icons.DOWNLOAD)
        self.btn_links = ui.secondary_button(t('btn_copy_links'), self.on_copy_links, icon=ft.Icons.LINK)
        self.results_header = ft.Text('', size=13, weight=ft.FontWeight.BOLD, color=ui.TEXT_MUTED)
        self.results_list = ft.Column(spacing=10)
        return ft.Column(
            [
                ui.card(
                    self.key_field,
                    ui.body_text(t('key_hint'), color=ui.TEXT_MUTED, size=12),
                    ft.Row([self.btn_export], spacing=8),
                    ft.Row([self.btn_links], spacing=8),
                ),
                self.results_header,
                self.results_list,
            ],
            spacing=12,
        )

    def build_settings_tab(self):
        t = self.t
        self.lang_seg = ft.SegmentedButton(
            segments=[
                ft.Segment(value='fa', label=ft.Text(i18n.LANGUAGE_NAMES['fa'])),
                ft.Segment(value='en', label=ft.Text(i18n.LANGUAGE_NAMES['en'])),
            ],
            selected=[self.lang],
            on_change=self.on_language,
        )
        self.obfs_switch = ft.Switch(
            label=t('settings_obfs_switch'), value=self.settings['obfuscation_enabled'],
            on_change=self.on_obfs_toggle, active_color=ui.PRIMARY,
        )
        self.obfs_hint = ui.body_text(self.obfs_hint_text(), color=ui.TEXT_MUTED, size=12)
        self.awg_fields, self.awg_errors = {}, {}
        field_controls = []
        for key in core.AWG_KEYS:
            field = ft.TextField(
                label=key, value=str(self.settings['obfuscation'][key]), width=150, text_size=13,
                on_change=self.on_awg_change, border_color=ui.BORDER, focused_border_color=ui.PRIMARY,
                bgcolor=ui.SURFACE, color=ui.TEXT, dense=True,
            )
            error = ft.Text('', size=11, color=ui.DANGER)
            self.awg_fields[key] = field
            self.awg_errors[key] = error
            field_controls.append(ft.Column([field, error], spacing=2))
        about_links = ft.Row([
            ui.secondary_button(t('open_telegram'), self.open_telegram, icon=ft.Icons.SEND),
            ui.secondary_button(t('open_x'), self.open_x, icon=ft.Icons.OPEN_IN_NEW),
        ], spacing=8)
        return ft.Column(
            [
                ui.card(ui.heading(t('settings_language')), self.lang_seg),
                ui.card(
                    ui.heading(t('settings_obfs')),
                    self.obfs_switch,
                    self.obfs_hint,
                    ft.Row(field_controls, wrap=True, spacing=10, run_spacing=10),
                    ui.body_text(t('settings_obfs_hint'), color=ui.TEXT_MUTED, size=12),
                    ft.Row([ui.secondary_button(t('settings_reset'), self.on_reset_obfs,
                                                icon=ft.Icons.RESTART_ALT)], spacing=8),
                ),
                ui.card(
                    ui.heading(t('about_title')),
                    ft.Text(t('about_version', version=core.APP_VERSION), size=14, color=ui.TEXT),
                    ui.body_text(t('about_disclaimer'), color=ui.TEXT_MUTED, size=12),
                    about_links,
                ),
            ],
            spacing=12,
        )

    def build_guide_tab(self):
        return ft.Column(
            [ui.guide_section(section, self.lang, self.open_url) for section in guide_content.GUIDE[self.lang]],
            spacing=12,
        )

    def obfs_hint_text(self):
        key = 'settings_obfs_on' if self.settings['obfuscation_enabled'] else 'settings_obfs_off'
        return self.t(key)

    # ---------- وضعیت و به‌روزرسانی رابط ----------
    def sync(self):
        """همه‌ی کنترل‌ها را طبق وضعیت برنامه تنظیم می‌کند و صفحه را به‌روز می‌کند."""
        busy = self.busy
        loaded = self.index is not None
        has_results = bool(self.last_valid)
        self.btn_load.content = self.t('btn_reload' if self.loaded_once else 'btn_load')
        self.btn_load.disabled = busy
        self.db_text.value = self.db_summary()
        self.mode_seg.disabled = busy or not loaded
        self.continent_dd.disabled = busy or not loaded
        self.country_dd.disabled = busy or not loaded
        self.btn_scan.disabled = busy or not loaded
        self.btn_next.disabled = busy or self.remaining <= 0
        self.btn_reset.disabled = busy or not (has_results or self.remaining or self.offset)
        self.result_banner.visible = has_results
        if has_results:
            self.result_text.value = self.t('results_ready', alive=len(self.last_valid),
                                            shown=min(len(self.last_valid), core.TOP_N))
        # تا وقتی تب سرورها باز نشده، تعداد نتیجه‌ها کنار اسم آن می‌آید
        self.servers_destination.label = (
            self.t('nav_servers_count', count=len(self.last_valid))
            if has_results and self.tab != TAB_SERVERS else self.t('nav_servers'))
        done, total = self.progress
        self.progress_bar.value = done / max(total, 1)
        level, key, values = self.status
        self.status_text.value = self.t(key, **values)
        self.status_text.color = ui.level_color(level)

        self.key_field.disabled = busy
        self.btn_export.disabled = busy or not has_results
        self.btn_links.disabled = busy or not has_results
        self.results_list.controls = self.result_controls()
        if has_results:
            shown = min(len(self.last_valid), core.TOP_N)
            self.results_header.value = self.t('results_header', shown=shown, total=len(self.last_valid))
        else:
            self.results_header.value = ''
        self.page.update()

    def db_summary(self):
        if self.index is None:
            return self.t('db_none')
        mode_key = {'free': 'mode_free', 'paid': 'mode_paid', 'all': 'mode_all'}[self.mode]
        return self.t('db_summary', count=len(self.all_filtered), mode=self.t(mode_key))

    def set_status(self, level, key, **values):
        self.status = (level, key, values)
        self.sync()

    def toast(self, level, key, **values):
        """پیام کوتاه پایین صفحه برای کپی، ذخیره و خطاها."""
        snack = ft.SnackBar(content=ft.Text(self.t(key, **values), color=ui.TEXT),
                            bgcolor=ui.SURFACE_HIGH)
        snack.bgcolor = ui.blend(ui.level_color(level), ui.SURFACE_HIGH, 0.35)
        self.page.show_dialog(snack)

    def set_progress(self, done, total):
        self.progress = (done, total)
        self.sync()

    # ---------- گزینه‌های فیلتر ----------
    def continent_options(self):
        options = [ft.DropdownOption(key=core.ALL_CONTINENTS, text=self.t('continent_all'))]
        if self.index is not None:
            options += [ft.DropdownOption(key=c, text=c) for c in core.continent_choices(self.index)]
        return options

    def country_options(self):
        if self.index is None:
            return [ft.DropdownOption(key=core.ALL_COUNTRIES, text=self.t('country_all'))]
        labels = core.country_choices(self.index, self.continent)
        return [ft.DropdownOption(key=label, text=self.t('country_all') if label == core.ALL_COUNTRIES else label)
                for label in labels]

    def refresh_region_options(self):
        self.continent_dd.options = self.continent_options()
        self.country_dd.options = self.country_options()

    def update_menus(self):
        servers = core.extract_servers(self.raw_data)
        self.all_filtered = core.dedupe_endpoints(core.filter_by_tier(servers, self.mode))
        self.index = core.build_region_index(self.all_filtered)
        self.continent = core.ALL_CONTINENTS
        self.country = core.ALL_COUNTRIES
        self.continent_dd.value = self.continent
        self.country_dd.value = self.country
        self.refresh_region_options()
        self.reset_scan_session()

    def reset_scan_position(self):
        """NEXT را غیرفعال می‌کند؛ بعد از تغییر محدوده باید دوباره اسکن شروع شود."""
        self.offset = 0
        self.remaining = 0

    def reset_scan_session(self):
        """نتیجه‌ها و موقعیت اسکن را پاک می‌کند؛ برای وقتی که فهرست سرورها عوض می‌شود."""
        self.reset_scan_position()
        self.last_valid = []
        self.progress = (0, 1)
        self.status = ('ok', 'scan_reset_done', {})

    # ---------- رویدادهای تب‌ها و فیلترها ----------
    async def on_tab(self, e):
        self.tab = e.control.selected_index
        self.body.controls = [self.current_tab()]
        self.sync()

    async def on_view_results(self, e=None):
        self.tab = TAB_SERVERS
        self.page.navigation_bar.selected_index = TAB_SERVERS
        self.body.controls = [self.current_tab()]
        self.sync()

    async def on_mode(self, e):
        self.mode = self.selected_value(e.control)
        if self.raw_data is not None:
            self.update_menus()
        self.sync()

    async def on_continent(self, e):
        self.continent = e.control.value
        self.country = core.ALL_COUNTRIES
        self.country_dd.value = self.country
        self.country_dd.options = self.country_options()
        self.reset_scan_position()
        self.sync()

    async def on_country(self, e):
        self.country = e.control.value
        self.reset_scan_position()
        self.sync()

    async def on_key_change(self, e):
        self.private_key = e.control.value or ''

    async def on_language(self, e):
        self.lang = self.selected_value(e.control)
        self.settings['language'] = self.lang
        await self.save_settings()
        self.build()

    # ---------- دیتابیس ----------
    async def on_load(self, e=None):
        if self.busy:
            return
        max_age = 0 if self.loaded_once else core.CACHE_MAX_AGE_S
        self.busy = True
        self.set_status('muted', 'load_loading')
        try:
            data, source = await asyncio.to_thread(core.load_database, self.cache_path, core.GITHUB_MIRRORS,
                                                   max_age)
        except Exception as exc:
            data, source = None, None
            self.toast('error', 'err_generic', error=str(exc))
        finally:
            self.busy = False
        if data is None:
            self.set_status('error', 'load_failed')
            return
        self.raw_data = data
        self.loaded_once = True
        try:
            self.update_menus()
        except Exception as exc:  # داده‌ی خراب نباید دکمه‌ها را قفل کند
            self.index = None
            self.all_filtered = []
            self.set_status('error', 'load_failed')
            self.toast('error', 'err_generic', error=str(exc))
            return
        keys = {'cache': 'load_done_cache', 'network': 'load_done_network', 'stale-cache': 'load_done_stale'}
        self.set_status('ok', keys.get(source, 'load_done_cache'))

    # ---------- اسکن ----------
    async def on_scan(self, e=None):
        self.scan_selection = (self.continent, core.cc_from_label(self.country))
        self.offset = 0
        self.last_valid = []
        await self.run_batch()

    async def on_next(self, e=None):
        self.offset += core.BATCH_SIZE
        await self.run_batch()

    async def on_reset_scan(self, e=None):
        self.offset = 0
        self.remaining = 0
        self.last_valid = []
        self.progress = (0, 1)
        self.set_status('ok', 'scan_reset_done')

    async def run_batch(self):
        continent, cc = self.scan_selection
        active_map = self.index.active_map if self.index else {}
        servers = core.filter_servers(self.all_filtered, continent, cc, active_map)
        if not servers:
            self.set_status('warn', 'scan_none_in_scope')
            return
        batch = servers[self.offset:self.offset + core.BATCH_SIZE]
        if not batch:
            self.remaining = 0
            self.set_status('warn', 'scan_end')
            return

        total = len(batch)
        done = 0
        alive = []
        gate = asyncio.Semaphore(core.SCAN_WORKERS)

        async def check(server):
            nonlocal done
            async with gate:
                ping, proto = await asyncio.to_thread(core.smart_ping, server['ip'])
            done += 1
            if done % 10 == 0 or done == total:
                self.progress = (done, total)
                self.sync()
            # پینگ‌های زیر حد مجاز جواب واقعی نیستند
            if ping is not None and ping >= core.MIN_PLAUSIBLE_PING_MS:
                alive.append({**server, 'ping': ping, 'proto': proto})

        self.busy = True
        self.progress = (0, total)
        self.set_status('warn', 'scan_progress', total=total)
        try:
            outcomes = await asyncio.gather(*(check(server) for server in batch), return_exceptions=True)
        finally:
            self.busy = False
        failures = [outcome for outcome in outcomes if isinstance(outcome, Exception)]
        if failures:
            self.toast('error', 'err_generic', error=str(failures[0]))

        self.remaining = len(servers) - (self.offset + total)
        if alive:
            self.last_valid = core.merge_results(self.last_valid, alive)
            self.set_status('ok', 'scan_found', alive=len(alive), shown=min(len(self.last_valid), core.TOP_N))
        else:
            self.set_status('error', 'scan_all_dead', total=total, ms=core.MIN_PLAUSIBLE_PING_MS)

    def result_controls(self):
        if not self.last_valid:
            return [ui.body_text(self.t('results_empty'), color=ui.TEXT_MUTED, size=13)]
        actions_for = lambda srv: {  # noqa: E731 - کوتاه و فقط برای ساخت کارت‌ها
            'ip': self.handler(self.copy_ip, srv),
            'link': self.handler(self.copy_link, srv),
            'wg': self.handler(self.copy_wg, srv),
            'qr': self.handler(self.show_qr, srv),
            'save': self.handler(self.save_wg, srv),
        }
        top = core.top_results(self.last_valid, core.TOP_N)
        return [ui.result_card(srv, self.t, actions_for(srv)) for srv in top]

    def handler(self, action, server):
        async def on_click(e):
            await self.guarded(lambda: action(server))
        return on_click

    # ---------- کلید و کانفیگ ----------
    def key_for(self, required):
        key = self.private_key.strip()
        if not key:
            if required:
                raise UserError('err_key_required')
            return ''
        if not core.is_valid_wg_key(key):
            raise UserError('err_key_invalid')
        return key

    async def guarded(self, action):
        try:
            await action()
        except UserError as exc:
            self.toast('error', exc.key, **exc.values)
        except core.ConfigError as exc:
            self.toast('error', CONFIG_ERROR_KEYS.get(exc.code, 'err_generic'), error=str(exc))
        except Exception as exc:  # خطای غیرمنتظره نباید برنامه را از کار بیندازد؛ فقط پیام می‌دهیم
            self.toast('error', 'err_generic', error=str(exc))

    async def copy_text(self, text, key, **values):
        await self.clipboard.set(text)
        self.toast('ok', key, **values)

    async def copy_ip(self, server):
        await self.copy_text(server['ip'], 'copied')

    async def copy_link(self, server):
        key = self.key_for(required=True)
        link = core.build_wg_link(server, key, obfuscation=self.obfuscation())
        await self.copy_text(link, 'link_copied', name=server['name'])

    async def copy_wg(self, server):
        key = self.key_for(required=False)
        conf = core.build_wireguard_config(server, key, obfuscation=self.obfuscation())
        await self.copy_text(conf, 'config_copied')

    async def save_wg(self, server):
        key = self.key_for(required=False)
        path = await asyncio.to_thread(core.write_wireguard_config, server, self.export_dir, key,
                                       self.obfuscation())
        self.toast('ok', 'saved_to', path=path)

    async def show_qr(self, server):
        key = self.key_for(required=True)
        if not core.qr_available():
            raise UserError('err_qr_package')
        obfuscation = self.obfuscation()
        # هر دو حالت همین‌جا ساخته می‌شوند تا خطای سرور قبل از باز شدن پنجره دیده شود
        payloads = {
            'config': core.build_wireguard_config(server, key, obfuscation=obfuscation),
            'link': core.build_wg_link(server, key, obfuscation=obfuscation),
        }
        qr_box = ft.Container(bgcolor=ft.Colors.WHITE, border_radius=8)
        hint = ui.body_text('', color=ui.TEXT_MUTED, size=12)

        def show_mode(mode):
            qr_box.content = ui.qr_canvas(core.qr_matrix(payloads[mode]))
            hint.value = self.t(QR_HINT_KEYS[mode])

        async def on_mode(e):
            show_mode(self.selected_value(e.control))
            self.page.update()

        show_mode('config')
        mode_switch = ft.SegmentedButton(
            segments=[
                ft.Segment(value='config', label=ft.Text(self.t('qr_mode_config'))),
                ft.Segment(value='link', label=ft.Text(self.t('qr_mode_link'))),
            ],
            selected=['config'],
            on_change=on_mode,
        )
        controls = [mode_switch, qr_box, hint]
        aliases = server.get('aliases') or []
        if aliases:
            controls.insert(0, ui.body_text(self.t('qr_same_host', aliases=', '.join(aliases)),
                                            color=ui.TEXT_MUTED, size=12))
        dialog = ft.AlertDialog(
            title=ft.Text(self.t('qr_title', name=server['name']), size=16, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=ui.QR_SIDE_PX + 40,
                content=ft.Column(controls, tight=True, spacing=12,
                                  horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            actions=[ui.secondary_button(self.t('close'), lambda e: self.page.pop_dialog(), expand=False)],
            bgcolor=ui.SURFACE,
        )
        self.page.show_dialog(dialog)

    async def on_copy_links(self, e=None):
        await self.guarded(self.do_copy_links)

    async def do_copy_links(self):
        key = self.key_for(required=True)
        cc = core.cc_from_label(self.country)
        active_map = self.index.active_map if self.index else {}
        servers = core.filter_servers(self.last_valid, self.continent, cc, active_map)
        obfuscation = self.obfuscation()
        links, skipped = [], 0
        for server in servers:
            try:
                links.append(core.build_wg_link(server, key, obfuscation=obfuscation))
            except core.ConfigError:
                skipped += 1
        if not links:
            raise UserError('no_scope_servers')
        if cc != core.ALL_COUNTRIES:
            scope = self.country
        elif self.continent != core.ALL_CONTINENTS:
            scope = self.continent
        else:
            scope = self.t('scope_all')
        await self.clipboard.set('\n'.join(links))
        if skipped:
            self.toast('warn', 'links_copied_partial', count=len(links), scope=scope, skipped=skipped)
        else:
            self.toast('ok', 'links_copied', count=len(links), scope=scope)

    async def on_export(self, e=None):
        await self.guarded(self.do_export)

    async def do_export(self):
        key = self.key_for(required=False)
        top = core.top_results(self.last_valid, core.TOP_N)
        if not top:
            raise UserError('export_nothing')
        obfuscation = self.obfuscation()
        written, skipped = await asyncio.to_thread(core.export_wireguard_configs, top, self.export_dir, key,
                                                   obfuscation)
        kind = 'AmneziaWG' if obfuscation else 'WireGuard'
        if skipped:
            self.toast('warn', 'exported_partial', count=len(written), kind=kind, path=self.export_dir,
                       skipped=len(skipped))
        else:
            self.toast('ok', 'exported', count=len(written), kind=kind, path=self.export_dir)

    # ---------- تنظیمات AmneziaWG ----------
    async def on_obfs_toggle(self, e):
        self.settings['obfuscation_enabled'] = bool(e.control.value)
        self.obfs_hint.value = self.obfs_hint_text()
        await self.save_settings()
        self.page.update()

    async def on_awg_change(self, e=None):
        values = {key: field.value for key, field in self.awg_fields.items()}
        params, errors = core.check_obfuscation(values)
        for key, error in self.awg_errors.items():
            error.value = self.t(AWG_ERROR_KEYS[errors[key]]) if key in errors else ''
        if not errors:
            self.settings['obfuscation'] = params
            await self.save_settings()
        self.page.update()

    async def on_reset_obfs(self, e=None):
        self.settings = app_settings.reset_obfuscation(self.settings)
        for key, field in self.awg_fields.items():
            field.value = str(self.settings['obfuscation'][key])
            self.awg_errors[key].value = ''
        await self.save_settings()
        self.toast('ok', 'settings_reset_done')
        self.page.update()

    async def open_url(self, url):
        try:
            await self.launcher.launch_url(url)
        except Exception as exc:  # مرورگر در دسترس نباشد نباید برنامه را از کار بیندازد
            self.toast('error', 'err_generic', error=str(exc))

    async def open_telegram(self, e=None):
        await self.open_url('https://t.me/ProtonVpnScanner')

    async def open_x(self, e=None):
        await self.open_url('https://x.com/BehrouzSdn')


async def main(page: ft.Page):
    if IMPORT_ERROR:  # ui بارگذاری نشده، پس رنگ‌ها مستقیم نوشته شده‌اند
        page.bgcolor = '#1C1B24'
        page.add(ft.Text('Import error:\n' + IMPORT_ERROR[-1500:], color='#FF5C6C', selectable=True))
        page.update()
        return
    try:  # ساخت ScannerApp هم داخل try است تا خطای آن هم روی صفحه بیاید
        app = ScannerApp(page)
        await app.start()
    except Exception:  # اگر راه‌اندازی شکست خورد، صفحه‌ی خالی نماند و خطا نشان داده شود
        page.controls.clear()
        page.add(ft.Text('Startup error:\n' + traceback.format_exc()[-1500:], color=ui.DANGER, selectable=True))
        page.update()


# ft.run بدون شرط __name__ اجرا می‌شود: روی موبایل ماژول با نام دیگری بارگذاری می‌شود
# و با شرط قبلی هیچ رابطی ساخته نمی‌شد (صفحه‌ی سیاه).
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets') if '__file__' in globals() else 'assets'
ft.run(main, assets_dir=ASSETS_DIR)
