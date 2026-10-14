"""عناصر مشترک ظاهر برنامه: رنگ‌ها، دکمه‌ها، کارت سرور، کد QR و بلوک‌های راهنما.

رنگ‌ها حس بصری ProtonVPN را دارند (بنفش تیره با دکمه‌های بنفش)؛ این برنامه غیررسمی است.
"""
import os

import flet as ft
import flet.canvas as cv

import i18n
import scanner_core as core

BG = '#1C1B24'
SURFACE = '#27262F'
SURFACE_HIGH = '#33323D'
BORDER = '#3F3E4B'
PRIMARY = '#6D4AFF'
PRIMARY_HOVER = '#8A6DFF'
SUCCESS = '#1EB980'
WARNING = '#F5B642'
DANGER = '#FF5C6C'
TEXT = '#FFFFFF'
TEXT_MUTED = '#A9A7B8'

PING_FAST_MS = 150
PING_OK_MS = 300
QR_SIDE_PX = 300

_LEVEL_COLORS = {'ok': SUCCESS, 'warn': WARNING, 'error': DANGER, 'muted': TEXT_MUTED}


def level_color(level):
    return _LEVEL_COLORS.get(level, TEXT_MUTED)


def ping_color(ms):
    if ms < PING_FAST_MS:
        return SUCCESS
    if ms < PING_OK_MS:
        return WARNING
    return DANGER


def blend(color, base, alpha):
    """رنگ نیمه‌شفاف را روی زمینه‌ی تیره به رنگ توپر تبدیل می‌کند (بدون نیاز به شفافیت هگزادسیمال)."""
    fore = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    back = [int(base[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02X%02X%02X' % tuple(round(alpha * f + (1 - alpha) * b) for f, b in zip(fore, back))


PERSIAN_FONT = 'Vazirmatn'
PERSIAN_FONT_FILE = 'fonts/Vazirmatn-NL-Regular.ttf'


def theme():
    """تم تیره‌ی برنامه. فونت وزیرمتن را برای هر دو زبان می‌گذارد چون متن‌های فارسی در حالت English هم دیده می‌شوند؛ حروف لاتین را به فونت پیش‌فرض می‌سپارد."""
    return ft.Theme(
        font_family=PERSIAN_FONT,
        color_scheme=ft.ColorScheme(primary=PRIMARY, on_primary=TEXT, surface=SURFACE, on_surface=TEXT),
    )


def card(*controls, spacing=10):
    return ft.Container(
        content=ft.Column(list(controls), spacing=spacing),
        bgcolor=SURFACE,
        border_radius=16,
        padding=16,
        border=ft.Border.all(1, BORDER),
    )


def heading(text):
    return ft.Text(text, size=13, weight=ft.FontWeight.BOLD, color=TEXT_MUTED)


def body_text(text, color=TEXT, size=14, weight=None):
    return ft.Text(text, size=size, color=color, weight=weight)


def ltr(text):
    """متن لاتین/عددی که نباید در پاراگراف راست‌به‌چپ جابه‌جا شود (مثل 17 ms)."""
    return f'\u2066{text}\u2069'


def pill(text, color):
    return ft.Container(
        content=ft.Text(text, size=12, weight=ft.FontWeight.BOLD, color=color),
        bgcolor=blend(color, SURFACE, 0.18),
        border_radius=20,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
    )


def primary_button(label, on_click, icon=None):
    return ft.FilledButton(
        content=label,
        icon=icon,
        on_click=on_click,
        height=46,
        expand=True,
        style=ft.ButtonStyle(
            color={ft.ControlState.DISABLED: TEXT_MUTED, ft.ControlState.DEFAULT: TEXT},
            bgcolor={ft.ControlState.DISABLED: SURFACE_HIGH, ft.ControlState.DEFAULT: PRIMARY},
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )


def secondary_button(label, on_click, icon=None, danger=False, expand=True, size=None):
    return ft.OutlinedButton(
        content=ft.Text(label, size=size) if size else label,
        icon=icon,
        on_click=on_click,
        height=42,
        expand=expand,
        style=ft.ButtonStyle(
            color={ft.ControlState.DISABLED: TEXT_MUTED, ft.ControlState.DEFAULT: DANGER if danger else TEXT},
            side=ft.BorderSide(1, BORDER),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )


FLAGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'flags')


def flag(cc, size=20):
    """پرچم کشور از assets/flags. اگر پرچمی برای کد نبود، آیکون کره‌ی زمین نشان داده می‌شود."""
    code = (cc or '').lower()
    if code and os.path.exists(os.path.join(FLAGS_DIR, f'{code}.png')):
        return ft.Image(src=f'flags/{code}.png', width=size * 4 // 3, height=size, fit=ft.BoxFit.COVER,
                        border_radius=3)
    return ft.Icon(ft.Icons.PUBLIC, size=size, color=TEXT_MUTED)


def result_card(server, label, actions):
    """کارت یک سرور. actions نگاشت نام عمل به تابع کلیک است: ip, link, wg, qr, save."""
    aliases = server.get('aliases') or []
    name = server['name'] + (f" (+{len(aliases)})" if aliases else '')
    marker = core.PROVIDER_MARKERS.get(server.get('provider', core.PROVIDER_PROTON), '')
    return card(
        ft.Row(
            [
                flag(server.get('cc')),
                ft.Text(f"{marker} {name}".strip(), size=16, weight=ft.FontWeight.BOLD, color=TEXT, expand=True),
                pill(ltr(f"{server['ping']} ms"), ping_color(server['ping'])),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=10,
        ),
        ft.Text(ltr(f"{server['ip']}  •  {server['proto']}"), size=12, color=TEXT_MUTED),
        ft.Row(
            [
                secondary_button(label('card_copy_ip'), actions['ip'], icon=ft.Icons.CONTENT_COPY, size=12),
                secondary_button(label('card_copy_link'), actions['link'], icon=ft.Icons.LINK, size=12),
            ],
            spacing=8,
        ),
        ft.Row(
            [
                secondary_button(label('card_copy_wg'), actions['wg'], icon=ft.Icons.DATA_OBJECT, size=12),
                secondary_button(label('card_qr'), actions['qr'], icon=ft.Icons.QR_CODE_2, size=12),
                secondary_button(label('card_save'), actions['save'], icon=ft.Icons.SAVE_ALT, size=12),
            ],
            spacing=8,
        ),
        spacing=8,
    )


def qr_canvas(matrix, side=QR_SIDE_PX):
    """کد QR را با مربع‌های صحیح پیکسلی روی بوم سفید می‌کشد؛ لبه‌ی تار دوربین را سخت‌تر نمی‌کند."""
    cell, rects = core.qr_cells(matrix, side)
    background = ft.Paint(color=ft.Colors.WHITE, style=ft.PaintingStyle.FILL)
    dark = ft.Paint(color='#000000', style=ft.PaintingStyle.FILL)
    shapes = [cv.Rect(0, 0, side, side, paint=background)]
    shapes += [cv.Rect(x, y, cell, cell, paint=dark) for x, y, cell in rects]
    return cv.Canvas(shapes=shapes, width=side, height=side)


def link_button(label, url, on_open):
    """دکمه‌ی باز کردن یک نشانی در مرورگر."""
    async def on_click(e):
        await on_open(url)
    return ft.TextButton(
        content=label,
        icon=ft.Icons.OPEN_IN_NEW,
        on_click=on_click,
        style=ft.ButtonStyle(color=PRIMARY_HOVER),
    )


def guide_section(section, lang, on_open):
    """یک بخش راهنما را به کارت تبدیل می‌کند. نوع بلوک‌ها: p, ul, ol, note, warn, link."""
    fix = i18n.isolate_ltr if lang == 'fa' else (lambda text: text)
    controls = [ft.Text(fix(section['title']), size=17, weight=ft.FontWeight.BOLD, color=TEXT)]
    for kind, raw in section['blocks']:
        value = fix(raw) if isinstance(raw, str) else raw
        if kind == 'p':
            controls.append(body_text(value, color=TEXT_MUTED))
        elif kind in ('ul', 'ol'):
            controls.append(ft.Column([
                ft.Row(
                    [ft.Text('•' if kind == 'ul' else f'{number}.', size=14, color=PRIMARY_HOVER,
                             weight=ft.FontWeight.BOLD),
                     ft.Text(fix(item), size=14, color=TEXT, expand=True)],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )
                for number, item in enumerate(value, start=1)
            ], spacing=6))
        elif kind == 'link':
            label, url = value
            controls.append(link_button(fix(label), url, on_open))
        elif kind in ('note', 'warn'):
            tone = PRIMARY if kind == 'note' else DANGER
            controls.append(ft.Container(
                content=body_text(value, color=TEXT, size=13),
                bgcolor=blend(tone, SURFACE, 0.16),
                border=ft.Border.all(1, blend(tone, SURFACE, 0.5)),
                border_radius=12,
                padding=12,
            ))
    return card(*controls, spacing=10)
