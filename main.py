!pip install buildozer
!apt-get install -y \
    python3-pip \
    build-essential \
    git \
    python3 \
    python3-dev \
    ffmpeg \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev \
    libgstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    openjdk-17-jdk \
    unzip \
    zip

# 2. تثبيت Buildozer
!pip install buildozer cython

# 3. إنشاء مجلد المشروع
import os
os.makedirs('/content/SmartFactory', exist_ok=True)
os.chdir('/content/SmartFactory')

# 4. كتابة ملف main.py
main_py = '''
import threading
import serial
import serial.tools.list_ports
import requests
import json
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

# Colors
NAVY   = get_color_from_hex('#060E1F')
NAVY2  = get_color_from_hex('#0A1628')
NAVY3  = get_color_from_hex('#0F1E38')
GOLD   = get_color_from_hex('#C9A84C')
CYAN   = get_color_from_hex('#00C8FF')
GREEN  = get_color_from_hex('#00E88F')
RED    = get_color_from_hex('#FF4444')
MUTED  = get_color_from_hex('#7A8BAA')
WHITE  = get_color_from_hex('#CDD6F4')

Window.clearcolor = NAVY

# ─── State ───────────────────────────────────────────────────
state = {
    "temp": 0.0, "hum": 0.0, "gas": 0, "smoke": 0,
    "rain": 0, "dist": 0, "workers": 0,
    "door": False, "windows": False,
    "emergency": False, "fan": False, "pump": False,
    "mode": None,   # "usb" or "wifi"
    "ser": None,    # serial object
    "wifi_url": "", # http://ip
    "connected": False,
}

# ─── Data Layer ──────────────────────────────────────────────
def send_cmd(cmd):
    try:
        if state["mode"] == "usb" and state["ser"]:
            state["ser"].write((cmd + "\\n").encode())
        elif state["mode"] == "wifi" and state["wifi_url"]:
            requests.get(f'{state["wifi_url"]}/cmd?c={cmd}', timeout=2)
    except Exception as e:
        print(f"CMD error: {e}")

def fetch_data():
    try:
        if state["mode"] == "usb" and state["ser"] and state["ser"].in_waiting:
            line = state["ser"].readline().decode().strip()
            if line.startswith("{"):
                d = json.loads(line)
                state.update({
                    "temp": d.get("t", state["temp"]),
                    "hum":  d.get("h", state["hum"]),
                    "gas":  d.get("g", state["gas"]),
                    "smoke":d.get("s", state["smoke"]),
                    "rain": d.get("r", state["rain"]),
                    "dist": d.get("d", state["dist"]),
                    "workers": d.get("w", state["workers"]),
                    "door": d.get("do", 0) == 1,
                    "windows": d.get("wi", 0) == 1,
                    "emergency": d.get("e", 0) == 1,
                })
        elif state["mode"] == "wifi" and state["wifi_url"]:
            r = requests.get(f'{state["wifi_url"]}/api', timeout=2)
            d = r.json()
            state.update({
                "temp": d.get("t", state["temp"]),
                "hum":  d.get("h", state["hum"]),
                "gas":  d.get("g", state["gas"]),
                "smoke":d.get("s", state["smoke"]),
                "rain": d.get("r", state["rain"]),
                "dist": d.get("d", state["dist"]),
                "workers": d.get("w", state["workers"]),
                "door": d.get("do", False),
                "windows": d.get("wi", False),
                "emergency": d.get("e", False),
            })
    except:
        pass

# ─── KV String ───────────────────────────────────────────────
KV = """
<RoundedButton@Button>:
    background_color: 0,0,0,0
    background_normal: ""
    canvas.before:
        Color:
            rgba: self.bg_color if not self.state == "down" else [c*0.8 for c in self.bg_color]
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
    bg_color: (0.2,0.5,0.8,1)
    color: 1,1,1,1
    font_size: sp(14)
    bold: True

<CardBox@BoxLayout>:
    canvas.before:
        Color:
            rgba: 0.06,0.12,0.22,1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
    padding: dp(14)
    spacing: dp(8)
"""

# ─── Widgets ─────────────────────────────────────────────────
def make_card(orient='vertical', pad=12, space=8):
    box = BoxLayout(orientation=orient, padding=dp(pad), spacing=dp(space))
    with box.canvas.before:
        Color(rgba=NAVY3)
        box._rect = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(12)])
    def update_rect(inst, val):
        inst._rect.pos = inst.pos
        inst._rect.size = inst.size
    box.bind(pos=update_rect, size=update_rect)
    return box

def lbl(text, size=14, color=WHITE, bold=False, halign='right'):
    l = Label(text=text, font_size=sp(size), color=color,
              bold=bold, halign=halign, valign='middle')
    l.bind(size=lambda i,v: setattr(i,'text_size',v))
    return l

def stat_card(title, value_id, color=CYAN, sub=""):
    card = make_card(pad=14)
    card.add_widget(lbl(title, 11, MUTED))
    val = lbl(value_id, 28, color, bold=True)
    val.id = value_id
    card.add_widget(val)
    if sub:
        card.add_widget(lbl(sub, 10, MUTED))
    return card, val

# ═════════════════════════════════════════════════════════════
# SCREENS
# ═════════════════════════════════════════════════════════════

# ─── Welcome Screen ──────────────────────────────────────────
class WelcomeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(rgba=NAVY)
            Rectangle(pos=self.pos, size=self.size)
        box = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(20))
        box.add_widget(Label(size_hint_y=None, height=dp(60)))
        box.add_widget(lbl("🏭", 60, WHITE, halign='center'))
        box.add_widget(lbl("Smart Factory", 36, GOLD, bold=True, halign='center'))
        box.add_widget(lbl("Full Security System", 18, CYAN, halign='center'))
        box.add_widget(lbl("نظام الأمان المتكامل للمصانع", 14, MUTED, halign='center'))
        box.add_widget(Label(size_hint_y=None, height=dp(20)))
        btn = Button(text="ابدأ معنا", font_size=sp(18), bold=True,
                     size_hint=(None, None), size=(dp(200), dp(52)),
                     pos_hint={'center_x': .5},
                     background_color=GOLD, color=NAVY)
        btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        box.add_widget(btn)
        box.add_widget(Label())
        self.add_widget(box)

# ─── Home Screen ─────────────────────────────────────────────
class HomeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', padding=dp(16),
                        spacing=dp(12), size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        box.add_widget(lbl("🏠  الرئيسية", 20, GOLD, bold=True))
        box.add_widget(lbl("نظام أمان متكامل — 17 عنصراً", 13, MUTED))
        box.add_widget(Label(size_hint_y=None, height=dp(10)))
        items = [
            ("⚙️  مكونات النظام","components","#1A5C2A"),
            ("🔌  مخطط التوصيل","wiring","#006064"),
            ("🎮  لوحة التحكم","control","#4A1070"),
            ("ℹ️   من نحن","about","#0D47A1"),
        ]
        for txt, scr, col in items:
            btn = Button(text=txt, font_size=sp(16), bold=True,
                         size_hint_y=None, height=dp(60),
                         background_color=get_color_from_hex(col),
                         color=WHITE)
            btn.bind(on_release=lambda x, s=scr: setattr(self.manager,'current',s))
            box.add_widget(btn)
        scroll.add_widget(box)
        self.add_widget(scroll)

# ─── Components Screen ───────────────────────────────────────
class ComponentsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        comps = [
            ("🧠","Arduino Mega 2560","المتحكم الرئيسي","ATmega2560 — 16MHz — 54 منفذ","جميع الأطراف"),
            ("📶","ESP8266","WiFi Bridge","3.3V — Serial1","D18/D19"),
            ("🌡️","DHT11","حرارة + رطوبة","5V — 0~50°C ±2°C","D23 + 10kΩ"),
            ("💨","MQ-2 Gas","كشف الغاز","5V — عتبة: 400","A0"),
            ("🔥","Flame Sensor","كشف اللهب","3.3V ⚠️ — DO","D22"),
            ("🌫️","Smoke Sensor","كشف الدخان","5V — عتبة: 500","A2 مُصحَّح"),
            ("🚶","PIR Motion","كشف الحركة","5V — طوارئ فقط","D24"),
            ("📡","HC-SR04","التراسونيك","5V — dist=t×0.034÷2","D25/D26"),
            ("🌧️","Rain Sensor","حساس المطر","5V — عتبة: 300","A1"),
            ("📱","RFID ×2","دخول/خروج","3.3V ⚠️ — SPI","D53/D49"),
            ("⚙️","Servo ×5","باب+4شبابيك","PSU 5V/2A ⚠️ — PWM","D10,D6~D9"),
            ("🖥️","LCD I2C","شاشة 16×2","5V — I2C","D20/D21"),
            ("🔌","Relay 4CH","مروحة+مضخة","5V — LOW=ON","D30/D31"),
            ("🔔","Buzzer","إنذار صوتي","5V — 100Ω","D33"),
            ("💡","LED Red","إنذار بصري","5V — 220Ω","D32"),
        ]
        main = BoxLayout(orientation='vertical')
        main.add_widget(BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=dp(50),
            padding=[dp(12),dp(8)]))
        hdr = main.children[0]
        back = Button(text="← رجوع", size_hint_x=None, width=dp(80),
                      font_size=sp(14), background_color=NAVY3, color=GOLD)
        back.bind(on_release=lambda x: setattr(self.manager,'current','home'))
        hdr.add_widget(back)
        hdr.add_widget(lbl("⚙️  مكونات النظام", 18, GOLD, bold=True))

        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=dp(8), padding=dp(12),
                          size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        self._detail = lbl("اضغط على أي عنصر للتفاصيل", 13, MUTED)
        self._detail_box = make_card(pad=12)
        self._detail_box.size_hint_y = None
        self._detail_box.height = dp(80)
        self._detail_box.add_widget(self._detail)

        for icon,name,role,spec,pin in comps:
            row = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=dp(64), spacing=dp(10), padding=[dp(12),dp(6)])
            with row.canvas.before:
                Color(rgba=NAVY3)
                row._bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(8)])
            row.bind(pos=lambda i,v: setattr(i._bg,'pos',v),
                     size=lambda i,v: setattr(i._bg,'size',v))
            row.add_widget(lbl(icon, 26, WHITE, halign='center'))
            info = BoxLayout(orientation='vertical')
            info.add_widget(lbl(name, 14, WHITE, bold=True))
            info.add_widget(lbl(role, 11, MUTED))
            row.add_widget(info)
            pin_lbl = lbl(pin, 12, CYAN, halign='left')
            pin_lbl.size_hint_x = None
            pin_lbl.width = dp(80)
            row.add_widget(pin_lbl)
            detail_txt = f"{name} | {spec} | التوصيل: {pin}"
            row.bind(on_touch_down=lambda inst, touch, t=detail_txt:
                     self._show_detail(t) if inst.collide_point(*touch.pos) else None)
            grid.add_widget(row)

        grid.add_widget(self._detail_box)
        scroll.add_widget(grid)
        main.add_widget(scroll)
        self.add_widget(main)

    def _show_detail(self, txt):
        self._detail.text = txt
        self._detail.color = CYAN

# ─── Wiring Screen ───────────────────────────────────────────
class WiringScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        data = [
            ("DHT11","D23","أصفر","5V | GND | 10kΩ"),
            ("MQ-2","A0","أصفر","5V | GND"),
            ("Flame ⚠️","D22","برتقالي","3.3V فقط! | GND"),
            ("Smoke","A2","أصفر","5V | GND — وليس D21"),
            ("PIR","D24","أخضر","5V | GND"),
            ("HC-SR04 TRIG","D25","أصفر","5V | GND"),
            ("HC-SR04 ECHO","D26","برتقالي","5V | GND"),
            ("Rain","A1","أزرق","5V | GND"),
            ("RFID-1 SS ⚠️","D53","بنفسجي","3.3V فقط! SPI"),
            ("RFID-2 SS ⚠️","D49","بنفسجي","3.3V فقط! SPI"),
            ("RFID MOSI","D51","بنفسجي","SPI مشترك"),
            ("RFID MISO","D50","بنفسجي","SPI مشترك"),
            ("RFID SCK","D52","بنفسجي","SPI مشترك"),
            ("RFID RST","D5","برتقالي","مشترك"),
            ("Servo باب","D10","أصفر","PSU 5V خارجي!"),
            ("Servo ش1","D6","أصفر","PSU 5V خارجي!"),
            ("Servo ش2","D7","أصفر","PSU 5V خارجي!"),
            ("Servo ش3","D8","أصفر","PSU 5V خارجي!"),
            ("Servo ش4","D9","أصفر","PSU 5V خارجي!"),
            ("LCD SDA","D20","برتقالي","5V | GND"),
            ("LCD SCL","D21","أصفر","5V | GND"),
            ("Relay Fan","D30","برتقالي","LOW=ON | 5V | GND"),
            ("Relay Pump","D31","برتقالي","LOW=ON | 5V | GND"),
            ("Buzzer","D33","أصفر","100Ω | GND"),
            ("LED Red","D32","أحمر","220Ω! | GND"),
            ("ESP TX","D19","بنفسجي","مباشر ← RX Mega"),
            ("ESP RX ⚠️","D18","بنفسجي","مقسم 1kΩ+2kΩ → TX Mega"),
        ]
        main = BoxLayout(orientation='vertical')
        hdr = BoxLayout(size_hint_y=None, height=dp(50), padding=[dp(12),dp(8)])
        back = Button(text="← رجوع", size_hint_x=None, width=dp(80),
                      font_size=sp(14), background_color=NAVY3, color=GOLD)
        back.bind(on_release=lambda x: setattr(self.manager,'current','home'))
        hdr.add_widget(back)
        hdr.add_widget(lbl("🔌  جدول التوصيلات", 18, GOLD, bold=True))
        main.add_widget(hdr)

        scroll = ScrollView()
        grid = GridLayout(cols=4, spacing=dp(2), padding=dp(8),
                          size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        for hd in ["العنصر","المنفذ","اللون","ملاحظة"]:
            l = Label(text=hd, font_size=sp(12), bold=True,
                      color=GOLD, size_hint_y=None, height=dp(36))
            grid.add_widget(l)
        for i,(comp,pin,col,note) in enumerate(data):
            bg = NAVY3 if i%2==0 else NAVY2
            warn = "⚠️" in comp or "⚠️" in note
            for txt,fc in [(comp, RED if warn else WHITE),
                            (pin, CYAN),
                            (col, MUTED),
                            (note, RED if warn else MUTED)]:
                lbl_w = Label(text=txt, font_size=sp(11), color=fc,
                               size_hint_y=None, height=dp(34),
                               halign='center', valign='middle')
                with lbl_w.canvas.before:
                    Color(rgba=bg)
                    Rectangle(pos=lbl_w.pos, size=lbl_w.size)
                lbl_w.bind(pos=lambda i,v: i.canvas.before.clear() or
                           setattr(i,'_needs_update', True),
                           size=lambda i,v: None)
                grid.add_widget(lbl_w)
        scroll.add_widget(grid)
        main.add_widget(scroll)
        self.add_widget(main)

# ─── Control / Connect Screen ────────────────────────────────
class ControlScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._mode = None
        main = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        hdr = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        back = Button(text="← رجوع", size_hint_x=None, width=dp(80),
                      font_size=sp(14), background_color=NAVY3, color=GOLD)
        back.bind(on_release=lambda x: setattr(self.manager,'current','home'))
        hdr.add_widget(back)
        hdr.add_widget(lbl("🎮  تحكّم في نظامك", 18, GOLD, bold=True))
        main.add_widget(hdr)

        # Mode buttons
        row = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(10))
        b_usb = Button(text="🔌 USB", font_size=sp(16), bold=True,
                        background_color=NAVY3, color=CYAN,
                        background_normal='')
        b_wifi = Button(text="📶 WiFi", font_size=sp(16), bold=True,
                         background_color=NAVY3, color=CYAN,
                         background_normal='')
        b_usb.bind(on_release=lambda x: self._show('usb'))
        b_wifi.bind(on_release=lambda x: self._show('wifi'))
        row.add_widget(b_usb); row.add_widget(b_wifi)
        main.add_widget(row)

        # USB form
        self.usb_box = BoxLayout(orientation='vertical', spacing=dp(10))
        self.usb_box.add_widget(lbl("اختر المنفذ:", 13, MUTED))
        self.port_spin = Spinner(
            text='اختر COM Port',
            values=self._get_ports(),
            size_hint_y=None, height=dp(44), font_size=sp(14))
        self.usb_box.add_widget(self.port_spin)
        b_conn_usb = Button(text="اتصال USB", font_size=sp(15), bold=True,
                             size_hint_y=None, height=dp(48),
                             background_color=CYAN, color=NAVY,
                             background_normal='')
        b_conn_usb.bind(on_release=self._connect_usb)
        self.usb_box.add_widget(b_conn_usb)
        self.usb_box.opacity = 0; self.usb_box.size_hint_y = None; self.usb_box.height = 0
        main.add_widget(self.usb_box)

        # WiFi form
        self.wifi_box = BoxLayout(orientation='vertical', spacing=dp(10))
        self.wifi_box.add_widget(lbl("عنوان IP للـ ESP8266:", 13, MUTED))
        self.ip_inp = TextInput(hint_text='192.168.1.100', multiline=False,
                                size_hint_y=None, height=dp(44),
                                font_size=sp(14), foreground_color=WHITE,
                                background_color=NAVY3)
        self.wifi_box.add_widget(self.ip_inp)
        b_conn_wifi = Button(text="اتصال WiFi", font_size=sp(15), bold=True,
                              size_hint_y=None, height=dp(48),
                              background_color=get_color_from_hex('#0088cc'), color=WHITE,
                              background_normal='')
        b_conn_wifi.bind(on_release=self._connect_wifi)
        self.wifi_box.add_widget(b_conn_wifi)
        self.wifi_box.opacity = 0; self.wifi_box.size_hint_y = None; self.wifi_box.height = 0
        main.add_widget(self.wifi_box)

        self.status_lbl = lbl("اختر طريقة الاتصال", 13, MUTED, halign='center')
        main.add_widget(self.status_lbl)
        main.add_widget(Label())
        self.add_widget(main)

    def _get_ports(self):
        try:
            return [p.device for p in serial.tools.list_ports.comports()] or ['COM3','COM4','COM5']
        except:
            return ['COM3','COM4','COM5']

    def _show(self, mode):
        if mode == 'usb':
            self.usb_box.opacity = 1; self.usb_box.height = dp(160)
            self.wifi_box.opacity = 0; self.wifi_box.height = 0
        else:
            self.wifi_box.opacity = 1; self.wifi_box.height = dp(160)
            self.usb_box.opacity = 0; self.usb_box.height = 0

    def _connect_usb(self, *a):
        port = self.port_spin.text
        if 'اختر' in port:
            self.status_lbl.text = "⚠️ اختر منفذ COM أولاً"; return
        try:
            s = serial.Serial(port, 9600, timeout=1)
            state["ser"] = s; state["mode"] = "usb"; state["connected"] = True
            self.status_lbl.text = f"✅ متصل عبر {port}"
            self.manager.current = 'dashboard'
        except Exception as e:
            self.status_lbl.text = f"❌ خطأ: {e}"

    def _connect_wifi(self, *a):
        ip = self.ip_inp.text.strip()
        if not ip:
            self.status_lbl.text = "⚠️ أدخل عنوان IP"; return
        state["wifi_url"] = f"http://{ip}"; state["mode"] = "wifi"
        state["connected"] = True
        self.status_lbl.text = f"✅ متصل WiFi — {ip}"
        self.manager.current = 'dashboard'

# ─── Dashboard Screen ────────────────────────────────────────
class DashboardScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._vals = {}
        self._event = None
        main = BoxLayout(orientation='vertical')

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(52),
                        padding=[dp(12),dp(8)], spacing=dp(8))
        with hdr.canvas.before:
            Color(rgba=NAVY2)
            Rectangle(pos=hdr.pos, size=hdr.size)
        back = Button(text="←", size_hint_x=None, width=dp(40),
                      font_size=sp(18), background_color=(0,0,0,0), color=GOLD)
        back.bind(on_release=lambda x: setattr(self.manager,'current','home'))
        hdr.add_widget(back)
        hdr.add_widget(lbl("📊  لوحة التحكم الحية", 16, GOLD, bold=True))
        self.status_bar = lbl("جاري الاتصال...", 12, MUTED)
        hdr.add_widget(self.status_bar)
        main.add_widget(hdr)

        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', padding=dp(12),
                            spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # Stats Grid
        stats_grid = GridLayout(cols=2, spacing=dp(8),
                                size_hint_y=None, height=dp(320))
        defs = [
            ("العمال داخل","--",GOLD,"مسجّل دخول"),
            ("الحرارة","--°C",CYAN,"حد: 35°C"),
            ("الرطوبة","--%",WHITE,"حد: 80%"),
            ("الغاز","--",GREEN,"حد: 400"),
            ("الدخان","--",GREEN,"حد: 500"),
            ("المسافة","--cm",CYAN,"تراسونيك"),
        ]
        for title,vid,col,sub in defs:
            card = make_card(pad=12)
            card.add_widget(lbl(title, 11, MUTED))
            v = lbl(vid, 26, col, bold=True)
            self._vals[title] = v
            card.add_widget(v)
            card.add_widget(lbl(sub, 10, MUTED))
            stats_grid.add_widget(card)
        content.add_widget(stats_grid)

        # Emergency indicator
        self.emrg_lbl = lbl("✅  وضع طبيعي", 15, GREEN, bold=True, halign='center')
        emrg_card = make_card(pad=12)
        emrg_card.size_hint_y = None; emrg_card.height = dp(50)
        emrg_card.add_widget(self.emrg_lbl)
        content.add_widget(emrg_card)

        # Control Buttons
        ctrl_title = lbl("أزرار التحكم", 13, MUTED)
        content.add_widget(ctrl_title)
        btns = [
            ("فتح الباب",   "DOOR_OPEN",   "#1A4A2A"),
            ("إغلاق الباب", "DOOR_CLOSE",  "#2A1A1A"),
            ("فتح النوافذ", "WIN_OPEN",    "#1A2A4A"),
            ("إغلاق النوافذ","WIN_CLOSE",  "#2A1A2A"),
            ("تشغيل المروحة","FAN_ON",     "#2A2A10"),
            ("إيقاف المروحة","FAN_OFF",    "#1A1A1A"),
            ("تشغيل المضخة","PUMP_ON",     "#102A2A"),
            ("إيقاف المضخة","PUMP_OFF",    "#1A1A1A"),
        ]
        grid2 = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(260))
        for txt,cmd,col in btns:
            b = Button(text=txt, font_size=sp(14), bold=True,
                       background_color=get_color_from_hex(col),
                       color=WHITE, background_normal='')
            b.bind(on_release=lambda x, c=cmd: send_cmd(c))
            grid2.add_widget(b)
        content.add_widget(grid2)

        # Emergency button
        emrg_btn = Button(text="🚨  تفعيل الطوارئ", font_size=sp(16),
                          bold=True, size_hint_y=None, height=dp(54),
                          background_color=RED, color=WHITE, background_normal='')
        emrg_btn.bind(on_release=lambda x: send_cmd("EMERGENCY"))
        content.add_widget(emrg_btn)

        scroll.add_widget(content)
        main.add_widget(scroll)
        self.add_widget(main)

    def on_enter(self):
        self._event = Clock.schedule_interval(self._update, 1.5)

    def on_leave(self):
        if self._event:
            self._event.cancel()

    def _update(self, dt):
        threading.Thread(target=fetch_data, daemon=True).start()
        Clock.schedule_once(self._refresh_ui, 0.5)

    def _refresh_ui(self, dt):
        self._vals["العمال داخل"].text = str(state["workers"])
        t = state["temp"]
        self._vals["الحرارة"].text = f"{t:.1f}°C"
        self._vals["الحرارة"].color = RED if t > 35 else CYAN
        self._vals["الرطوبة"].text = f"{state['hum']:.0f}%"
        g = state["gas"]
        self._vals["الغاز"].text = str(g)
        self._vals["الغاز"].color = RED if g > 400 else GREEN
        s = state["smoke"]
        self._vals["الدخان"].text = str(s)
        self._vals["الدخان"].color = RED if s > 500 else GREEN
        self._vals["المسافة"].text = f"{state['dist']}cm"
        if state["emergency"]:
            self.emrg_lbl.text = "🚨  وضع الطوارئ!"
            self.emrg_lbl.color = RED
        else:
            self.emrg_lbl.text = "✅  وضع طبيعي"
            self.emrg_lbl.color = GREEN
        mode = "USB" if state["mode"]=="usb" else "WiFi"
        self.status_bar.text = f"متصل — {mode}"

# ─── About Screen ────────────────────────────────────────────
class AboutScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', padding=dp(16),
                        spacing=dp(12), size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        hdr = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        back = Button(text="← رجوع", size_hint_x=None, width=dp(80),
                      font_size=sp(14), background_color=NAVY3, color=GOLD)
        back.bind(on_release=lambda x: setattr(self.manager,'current','home'))
        hdr.add_widget(back)
        hdr.add_widget(lbl("ℹ️  من نحن", 18, GOLD, bold=True))
        box.add_widget(hdr)
        infos = [
            ("🎓 عن المشروع", "نظام أمان صناعي متكامل يجمع 17 عنصراً إلكترونياً في منظومة واحدة تعمل 24/7 لحماية المصانع."),
            ("🔧 التقنيات", "Arduino Mega 2560 + ESP8266\nKivy Python App\nHTTP REST API\nSerial USB Communication"),
            ("📋 المكونات", "5 سيرفوهات | 2 RFID | 7 حساسات\nLCD I2C | Relay 4CH | Buzzer | LED"),
            ("⚡ الأداء", "استجابة طوارئ < 200ms\nتحديث كل 1.5 ثانية\nيعمل بدون إنترنت عبر USB"),
        ]
        for title, desc in infos:
            card = make_card(pad=14)
            card.size_hint_y = None; card.height = dp(120)
            card.add_widget(lbl(title, 15, GOLD, bold=True))
            card.add_widget(lbl(desc, 12, MUTED))
            box.add_widget(card)
        scroll.add_widget(box)
        self.add_widget(scroll)

# ═════════════════════════════════════════════════════════════
# APP
# ═════════════════════════════════════════════════════════════
class SmartFactoryApp(App):
    def build(self):
        self.title = "Smart Factory"
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ComponentsScreen(name='components'))
        sm.add_widget(WiringScreen(name='wiring'))
        sm.add_widget(ControlScreen(name='control'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(AboutScreen(name='about'))
        return sm

if __name__ == '__main__':
    SmartFactoryApp().run()
'''
with open('/content/SmartFactory/main.py', 'w', encoding='utf-8') as f:
    f.write(main_py)
print("main.py written ✅")
