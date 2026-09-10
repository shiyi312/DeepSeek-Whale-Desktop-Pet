#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek Whale Desktop Pet v4
完整对标原版/plus：原版气泡、自动情绪动画、台词系统、完整悬浮菜单。
"""

import copy
import glob
import json
import math
import os
import random
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

from PyQt5.QtCore import (
    Qt, QEvent, QTimer, QUrl, QSize, QRect, QRectF, QPointF,
    QPropertyAnimation, QEasingCurve, QLockFile, pyqtSignal, QVariantAnimation
)
from PyQt5.QtGui import (
    QPixmap, QMovie, QIcon, QColor, QPainter, QPen, QBrush,
    QPainterPath, QFont, QFontMetrics, QTransform, QCursor
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QSlider,
    QCheckBox, QComboBox, QLineEdit, QPushButton, QFrame, QListWidget,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QSystemTrayIcon, QMenu,
    QScrollArea, QMessageBox, QTabWidget, QFileDialog, QInputDialog
)

try:
    import winreg
except Exception:
    winreg = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
EXPR_DIR = os.path.join(APP_DIR, "expressions")
SOUND_DIR = os.path.join(APP_DIR, "sounds")
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".dshw-desktop-pet.json")
UPDATE_URL = "https://github.com/shiyi312/DeepSeek-Whale-Desktop-Pet"
LOG_PATH = os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "dshw-pet.log")

LOCAL_VERSION = "4.4.0"
LOG_KEEP = 100
HUD_GAP = 2
SFX_POOL_SIZE = 5
QQ_GROUP = "254668799"
QQ_GROUP_URL = "https://qun.qq.com/qq/254668799"

# 喂食大目录时的扫描上限（避免遍历几万文件卡住界面）
SCAN_LIMIT_FILES = 20000
SCAN_LIMIT_SECONDS = 3.0

# 深色列表样式（控件级设置，确保 viewport 与滚动条都是深色，不用系统原生外观）
LIST_QSS = """
QListWidget { background: rgba(15,23,42,0.55); border: 1.5px solid rgba(148,163,184,0.30);
    border-radius: 10px; color: #e2e8f0; font-size: 16px; padding: 4px; outline: none; }
QListWidget::item { border-radius: 8px; padding: 8px 10px; margin: 2px 0; }
QListWidget::item:hover { background: rgba(56,189,248,0.14); }
QListWidget::item:selected { background: rgba(34,211,238,0.28); color: #ffffff; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: rgba(148,163,184,0.6); border-radius: 5px; min-height: 26px; }
QScrollBar::handle:vertical:hover { background: rgba(56,189,248,0.8); }
QScrollBar:horizontal { background: transparent; height: 0px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0px; width: 0px; }
"""

DEFAULT_APP_RULES = [
    {"match": "steam", "text": "又在打游戏啦？记得适可而止哦~", "enabled": True},
    {"match": "code", "text": "敲代码辛苦了，起来活动一下吧！", "enabled": True},
    {"match": "chrome", "text": "上网冲浪中~记得多喝水哦", "enabled": True},
]

SIZE_MIN = 1
SIZE_MAX = 20
SIZE_BASE = 220
SIZE_SCALE_MAX = 2.5
EDGE_MARGIN = 40
DEFAULT_SIZE_LEVEL = 10

RANDOM_TEXTS = [    "你好呀，我是 DeepSeek 小鲸鱼~",
    "今天也要元气满满哦！",
    "要记得喝水休息一下。",
    "抢票加油！",
    "余额还有多少呢？",
    "不要熬夜太晚啦！",
    "代码写得顺利吗？",
    "摸摸头，今天辛苦啦。",
]

EXPR_CN = {
    "DSniang1": "默认表情", "rua": "摸头动图",
    "angry": "生气", "cheer": "加油", "close_eyes": "闭眼",
    "disappointed": "失落", "exhausted": "疲惫", "fatfish": "大肥鱼",
    "greet": "打招呼", "half_closed_eyes": "半闭眼", "mock": "嘲笑",
    "ok": "OK", "quiet": "别吵", "sad": "伤心", "scared": "惊吓",
    "shy": "害羞", "stroking": "摸头", "thumbsup": "点赞", "what": "干什么",
    "amazing": "惊叹", "astonish": "震惊", "bored": "无聊", "caught": "抓包",
    "cornerfish": "角落鱼", "dazed": "发呆", "fakelaugh": "假笑",
    "give": "给你", "gotcha": "抓到", "grit": "咬牙", "happy": "开心",
    "know": "知道", "loud": "大声", "money": "有钱", "paymore": "加钱",
    "proud": "骄傲", "question": "疑问", "shocked": "震惊", "sotaku": "死宅",
    "superhappy": "超级开心", "wicked": "坏笑", "wronged": "委屈",
    "cake": "小蛋糕", "candy": "糖果", "cry": "哭唧唧", "dame": "哒咩",
    "evidence": "证据", "good": "乖巧", "grace": "优雅", "heart": "比心",
    "hip": "叉腰", "hit": "挨揍", "hm": "哼哼", "insight": "洞察",
    "peek": "偷偷看", "poorfish": "可怜大肥鱼", "ready": "好了叫你",
    "reflect": "检讨", "run": "跑", "sleepy": "困", "stretch": "活动筋骨",
    "study": "研究", "tea": "喝茶", "wake": "刚睡醒", "wall": "面壁",
    "wipe": "擦汗", "youwrite": "你来写", "art": "艺术", "boba": "奶茶",
    "chef": "厨师", "coffee": "咖啡", "dancing": "跳舞", "fishing": "钓鱼",
    "freeride": "蹭车", "gaming": "打游戏", "guitar": "弹吉他",
    "icecream": "冰淇淋", "icecream_mosaic": "打码冰淇淋", "kneel": "跪",
    "noodles": "吃面", "nooo": "不要啊", "phone": "玩手机", "playdead": "装死",
    "reading": "看书", "scholar": "学霸", "signboard": "举牌",
    "slacking": "摸鱼", "sleep": "睡觉", "snowman": "雪人",
    "sobbing": "大哭", "surrender": "投降", "thinking": "思考",
    "tremble": "颤抖", "upsidedown": "倒立", "watering": "浇花",
    "workhard": "努力", "youfirst": "你先",
}

BUBBLE_COLORS = {
    "blue": {"bg": (255, 255, 255, 245), "border": "#203170", "text": "#203170"},
    "pink": {"bg": (255, 228, 240, 245), "border": "#be185d", "text": "#831843"},
    "dark": {"bg": (17, 24, 39, 235), "border": "#60a5fa", "text": "#f8fafc"},
    "green": {"bg": (236, 253, 245, 245), "border": "#047857", "text": "#065f46"},
}

MOODS = [
    "元气满满", "开心", "平静", "有点困", "想摸鱼",
    "充满干劲", "需要充电", "小兴奋", "偷偷摸鱼中",
    "今天也要加油呀",
]


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def rotate_log_if_needed():
    """启动时把上一次的日志归档（保留最近 LOG_KEEP 份），便于查闪退。"""
    try:
        if not os.path.exists(LOG_PATH) or os.path.getsize(LOG_PATH) == 0:
            return
        stamp = time.strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(LOG_PATH)
        os.replace(LOG_PATH, f"{base}_{stamp}{ext}")
        logs = sorted(glob.glob(f"{base}_*{ext}"))
        for old in logs[:-LOG_KEEP]:
            try:
                os.remove(old)
            except OSError:
                pass
    except OSError:
        pass


# ---------- 外部编辑文件（台词 / 应用监测规则，均带注释说明） ----------
LINES_PATH = os.path.join(os.path.expanduser("~"), ".dshw-pet-lines.txt")
RULES_PATH = os.path.join(os.path.expanduser("~"), ".dshw-pet-rules.txt")

LINES_TEMPLATE = """# ============================================================
#  小鲸鱼桌宠 · 气泡台词文件（可直接编辑，保存后生效）
# ============================================================
# 怎么写：
#   1. 一行写一句台词，写完保存本文件即可；
#   2. 以 # 开头的整行是「注释」，不会显示出来；
#   3. 空白行会被自动忽略；
#   4. 想让新台词立刻生效：设置 → 系统 →「重新加载台词与规则」，
#      或重启桌宠（台词模式选「随机台词」或「自定义台词」时用这里的内容）。
#
# 下面是自带台词（可以随意删改）：
"""

RULES_TEMPLATE = """# ============================================================
#  小鲸鱼桌宠 · 应用打开监测规则（可直接编辑，保存后生效）
# ============================================================
# 每行一条规则，用竖线 | 分成 4 段：
#   匹配词 | 触发台词 | 触发概率(0-100，可省略，默认100) | 是否启用(1开/0关，可省略，默认1)
#
# 各段说明：
#   · 匹配词：进程名或窗口标题里的关键字（不区分大小写）
#       例：steam（Steam）、chrome（浏览器）、vscode（VS Code）、QQ、网易云
#   · 触发台词：命中后桌宠说的话，随便写
#   · 触发概率：打开该应用时有百分之多少的几率说这句话
#       例：30 表示 30% 概率触发（想每次都说就填 100；想让桌宠少唠叨就填 10~30）
#   · 是否启用：1 = 开启这条规则；0 = 暂时关闭（不用删掉）
#
# 注意：
#   · 以 # 开头的整行是注释，空白行忽略；
#   · 同一个应用 5 分钟内只会说一次，不会一直刷屏；
#   · 改完保存本文件后，设置 → 系统 →「重新加载台词与规则」即可生效。
#
# 下面是示例规则（可以随意删改）：
"""


def ensure_lines_file(defaults):
    """首次运行生成带注释的台词文件。"""
    if os.path.exists(LINES_PATH):
        return
    try:
        with open(LINES_PATH, "w", encoding="utf-8") as f:
            f.write(LINES_TEMPLATE)
            for line in defaults:
                f.write(line + "\n")
    except OSError:
        pass


def load_lines_file():
    """读取台词文件（忽略 # 注释与空行）。"""
    lines = []
    try:
        with open(LINES_PATH, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if line and not line.startswith("#"):
                    lines.append(line)
    except OSError:
        pass
    return lines


def load_rules_file():
    """读取应用监测规则文件：匹配词 | 台词 | 概率 | 启用。"""
    rules = []
    try:
        with open(RULES_PATH, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 2 or not parts[0] or not parts[1]:
                    continue
                chance, enabled = 100, True
                if len(parts) >= 3 and parts[2]:
                    try:
                        chance = max(0, min(100, int(float(parts[2]))))
                    except ValueError:
                        chance = 100
                if len(parts) >= 4 and parts[3]:
                    enabled = parts[3].lower() not in ("0", "false", "no", "关", "否")
                rules.append({"match": parts[0], "text": parts[1], "chance": chance, "enabled": enabled})
    except OSError:
        pass
    return rules


def write_rules_file(rules):
    """把当前规则写回文件（保留注释头）。"""
    try:
        with open(RULES_PATH, "w", encoding="utf-8") as f:
            f.write(RULES_TEMPLATE)
            for rule in rules:
                if not isinstance(rule, dict):
                    continue
                f.write("{0} | {1} | {2} | {3}\n".format(
                    rule.get("match", ""), rule.get("text", ""),
                    int(rule.get("chance", 100)), 1 if rule.get("enabled", True) else 0))
    except OSError:
        pass


# ---------- 磁盘图标美化（大肥鱼） ----------
def build_fish_ico(png_path, ico_path, size=256):
    """把 PNG 转成 ICO（单张 PNG 内嵌，Vista 及以上支持）。"""
    import struct
    pix = QPixmap(png_path)
    if pix.isNull():
        return False
    pix = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    tmp = ico_path + ".tmp.png"
    if not pix.save(tmp, "PNG"):
        return False
    try:
        with open(tmp, "rb") as f:
            data = f.read()
    except OSError:
        return False
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    try:
        with open(ico_path, "wb") as f:
            f.write(struct.pack("<HHH", 0, 1, 1))                      # ICONDIR
            f.write(struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(data), 22))  # ICONDIRENTRY
            f.write(data)
    except OSError:
        return False
    return True


def apply_drive_icon(drive, ico_path):
    """在磁盘根目录写 desktop.ini 指向图标（需要管理员权限），失败返回 False。"""
    root = drive.rstrip("\\") + "\\"
    ini = os.path.join(root, "desktop.ini")
    try:
        with open(ini, "w", encoding="utf-8") as f:
            f.write("[.ShellClassInfo]\n")
            f.write(f"IconResource={ico_path},0\n")
        subprocess.run(["attrib", "+s", "+h", ini], capture_output=True)
        subprocess.run(["attrib", "+s", root], capture_output=True)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def expr_display_name(raw):
    ver = ""
    base = raw
    if raw.startswith("v1_"):
        ver, base = "v1", raw[3:]
    elif raw.startswith("v2_"):
        ver, base = "v2", raw[3:]
    elif raw.startswith("v3_"):
        ver, base = "v3", raw[3:]
    elif raw.startswith("v4_"):
        ver, base = "v4", raw[3:]
    cn = EXPR_CN.get(base, base)
    if ver and base not in ("DSniang1", "rua"):
        return f"{ver}·{cn}"
    return cn


def scan_expressions():
    result = []
    os.makedirs(EXPR_DIR, exist_ok=True)
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.gif"):
        for path in sorted(glob.glob(os.path.join(EXPR_DIR, ext))):
            name = os.path.splitext(os.path.basename(path))[0]
            if name == "DSniang02":
                continue
            if name not in [e["name"] for e in result]:
                result.append({"name": name, "path": path, "display": expr_display_name(name)})
    if not result:
        plugin_dir = os.path.expanduser(r"~\.dsh\profiles\desktop\node_modules\dsh-whale-widget\assets")
        for fname in ["DSniang1.png", "rua.gif"]:
            p = os.path.join(plugin_dir, fname)
            if os.path.exists(p):
                name = os.path.splitext(fname)[0]
                result.append({"name": name, "path": p, "display": expr_display_name(name)})
    return result


def scan_sounds():
    """扫描 sounds/ 目录：{模式名: {"click": 路径, "release": 路径}}。
    支持 xxx.mp3（点击/松手同一文件）与 xxx_click.mp3 + xxx_release.mp3 配对。"""
    result = {}
    os.makedirs(SOUND_DIR, exist_ok=True)
    files = {}
    for ext in ("*.mp3", "*.MP3", "*.wav", "*.WAV", "*.ogg", "*.m4a"):
        for path in sorted(glob.glob(os.path.join(SOUND_DIR, ext))):
            files[os.path.splitext(os.path.basename(path))[0]] = path
    for name in list(files):
        if name.endswith("_click") and name[:-6] + "_release" in files:
            result[name[:-6]] = {"click": files[name], "release": files[name[:-6] + "_release"]}
    for name, path in files.items():
        if name.endswith("_click") or name.endswith("_release"):
            continue
        result.setdefault(name, {"click": path, "release": path})
    return result


def size_level_to_px(level):
    """档位 → 像素：1~10 段保持原有尺寸，10~20 段扩展到 2.5 倍上限。"""
    level = max(SIZE_MIN, min(SIZE_MAX, int(level)))
    mid = (SIZE_MIN + SIZE_MAX) // 2
    scale_mid = 0.6 + (mid - SIZE_MIN) * (1.5 - 0.6) / (SIZE_MAX - SIZE_MIN)   # 保持原默认档尺寸
    if level <= mid:
        factor = 0.6 + (level - SIZE_MIN) * (scale_mid - 0.6) / (mid - SIZE_MIN)
    else:
        factor = scale_mid + (level - mid) * (SIZE_SCALE_MAX - scale_mid) / (SIZE_MAX - mid)
    return max(100, round(SIZE_BASE * factor))


# Q 弹多关键帧（对标鲸鱼娘 SQUASH_KEY）：(时间比例, 纵向缩放 sy, 横向缩放 sx)，底部中心锚点
SQUASH_KEY = [
    (0.00, 1.00, 1.00),
    (0.18, 0.86, 1.12),
    (0.38, 1.12, 0.93),
    (0.58, 0.94, 1.05),
    (0.78, 1.02, 0.99),
    (1.00, 1.00, 1.00),
]


def squash_at(t):
    """按关键帧插值出 (sy, sx)。"""
    t = max(0.0, min(1.0, float(t)))
    for i in range(len(SQUASH_KEY) - 1):
        t0, sy0, sx0 = SQUASH_KEY[i]
        t1, sy1, sx1 = SQUASH_KEY[i + 1]
        if t <= t1:
            k = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return sy0 + (sy1 - sy0) * k, sx0 + (sx1 - sx0) * k
    return SQUASH_KEY[-1][1], SQUASH_KEY[-1][2]


AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_NAME = "WhaleDesktopPet"


def get_autostart_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if os.path.exists(pythonw):
        return f'"{pythonw}" "{os.path.abspath(__file__)}"'
    return f'"{sys.executable}" "{os.path.abspath(__file__)}"'


def set_autostart(enabled):
    if winreg is None:
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE)
    except OSError:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY)
    try:
        if enabled:
            winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ, get_autostart_command())
        else:
            try:
                winreg.DeleteValue(key, AUTOSTART_NAME)
            except OSError:
                pass
        return True
    finally:
        winreg.CloseKey(key)


def is_autostart_enabled():
    if winreg is None:
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, AUTOSTART_NAME)
            return True
        except OSError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False


def autostart_command_matches():
    """注册表里的自启命令是否指向当前程序（路径正确才叫真的能自启）。"""
    if winreg is None:
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, AUTOSTART_NAME)
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False
    reg = str(value).strip().strip('"')
    want = get_autostart_command().strip().strip('"')
    return os.path.normcase(reg.split('"')[0].strip()) == os.path.normcase(want.split('"')[0].strip())


class BubbleWidget(QWidget):
    """原版风格气泡：独立顶层窗口、圆角、尾巴、动态尺寸，不遮挡桌宠。"""

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.lines = []
        self.color_key = "blue"
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self.font_size = 13
        self.scale = 1.0
        self._timer.timeout.connect(self.hide)

    def apply_color(self, key):
        self.color_key = key if key in BUBBLE_COLORS else "blue"
        self.update()

    def set_style(self, font_size=13, scale=1.0):
        self.font_size = max(10, int(font_size))
        self.scale = max(0.6, min(1.5, float(scale)))
        self.update()

    def show_lines(self, lines, duration=3000, pet=None):
        self.lines = [str(x) for x in lines if str(x).strip()][:3]
        if not self.lines:
            return

        font = QFont("Microsoft YaHei", self.font_size)
        fm = QFontMetrics(font)
        max_text_w = int(280 * self.scale)
        line_rects = []
        total_h = 0
        max_w = 0
        for line in self.lines:
            br = fm.boundingRect(QRect(0, 0, max_text_w, 500),
                                 Qt.TextWordWrap | Qt.AlignHCenter, line)
            line_rects.append(br)
            total_h += br.height()
            max_w = max(max_w, br.width())
        self._line_rects = line_rects

        w = max(200, min(360, max_w + 60))
        h = max(80, total_h + 60)
        self.setFixedSize(w, h)

        if pet is not None:
            x = pet.x() + (pet.width() - w) // 2
            y = pet.y() - h - 8
            if y < 0:
                y = pet.y() + pet.height() + 8
            self.move(max(0, x), max(0, y))

        self.update()
        self.show()
        self.raise_()
        self._timer.start(duration)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        c = BUBBLE_COLORS.get(self.color_key, BUBBLE_COLORS["blue"])
        rect = self.rect().adjusted(5, 5, -5, -14)

        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 18, 18)
        p.setPen(QPen(QColor(c["border"]), 3))
        p.setBrush(QBrush(QColor(*c["bg"])))
        p.drawPath(path)

        tail = QPainterPath()
        tail.moveTo(rect.left() + rect.width() // 2 - 12, rect.bottom())
        tail.lineTo(rect.left() + rect.width() // 2, rect.bottom() + 14)
        tail.lineTo(rect.left() + rect.width() // 2 + 12, rect.bottom())
        p.setPen(QPen(QColor(c["border"]), 3))
        p.setBrush(QBrush(QColor(*c["bg"])))
        p.drawPath(tail)

        p.setPen(QColor(c["text"]))
        p.setFont(QFont("Microsoft YaHei", self.font_size))
        content = QRect(rect.left() + 14, rect.top() + 10, rect.width() - 28, rect.height() - 20)
        line_rects = getattr(self, "_line_rects", [])
        if not line_rects:
            line_rects = [p.fontMetrics().boundingRect(content, Qt.TextWordWrap | Qt.AlignHCenter, line) for line in self.lines]
        total_h = sum(br.height() for br in line_rects)
        y = content.top() + max(0, (content.height() - total_h) // 2)
        for line, br in zip(self.lines, line_rects):
            draw_rect = QRect(content.left(), y, content.width(), br.height() + 4)
            p.drawText(draw_rect, Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextWordWrap, line)
            y += br.height() + 4


def fmt_token(n):
    """token 简化显示（鲸鱼娘同款）：返回 (数量字符串, 单位字符串)。"""
    n = max(0, int(n))
    for thresh, unit in ((1e9, "B"), (1e6, "M"), (1e4, "W"), (1e3, "K")):
        if n >= thresh:
            v = n / thresh
            if abs(v - round(v)) < 1e-6:
                s = str(int(round(v)))
            else:
                s = ("%.1f" % v).rstrip("0").rstrip(".")
            return s, unit
    return str(n), "token"


class HudCard(QWidget):
    """鲸鱼娘风格 HUD：白框圆角卡片 + 深藏蓝 Token 数字（中蓝单位）+ 秒级时间。
    数字滚动动画、变化颜色反馈（增加亮蓝/消耗红）、主题描边联动保留。"""

    THEMES = {
        "blue": {"frame": QColor(32, 49, 112, 130), "time": QColor(31, 46, 71, 150)},
        "pink": {"frame": QColor(190, 24, 93, 130), "time": QColor(136, 19, 55, 165)},
        "dark": {"frame": QColor(30, 58, 138, 140), "time": QColor(30, 58, 138, 170)},
        "green": {"frame": QColor(6, 95, 70, 135), "time": QColor(6, 95, 70, 165)},
    }
    NUM_IDLE = QColor(31, 46, 71)       # 深藏蓝（鲸鱼娘同款）
    NUM_GAIN = QColor(37, 99, 235)      # 增加：亮蓝
    NUM_COST = QColor(220, 38, 38)      # 消耗：红
    PREFIX = QColor(34, 96, 168)        # "Token：" 与单位：中蓝（鲸鱼娘同款）

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._token = 0
        self.time_text = ""
        self.font_px = 11
        self.theme = "blue"
        self.tint = "idle"
        self.abbrev = True

    def apply_theme(self, key):
        self.theme = key if key in self.THEMES else "blue"
        self.update()

    def set_content(self, token_val, time_text, font_px, tint="idle", abbrev=None):
        self._token = max(0, int(token_val))
        self.time_text = time_text
        self.font_px = max(10, min(20, int(font_px)))
        self.tint = tint if tint in ("idle", "gain", "cost") else "idle"
        if abbrev is not None:
            self.abbrev = bool(abbrev)
        self.update()

    def _font(self):
        f = QFont("Microsoft YaHei UI")
        f.setPixelSize(self.font_px)
        f.setBold(True)
        return f

    def _parts(self):
        """返回 [(文本, 颜色), ...] 分段，及总宽。"""
        abbr_num, abbr_unit = fmt_token(self._token)
        num, unit = (abbr_num, abbr_unit) if self.abbrev else (f"{self._token:,}", "")
        num_color = {"idle": self.NUM_IDLE, "gain": self.NUM_GAIN, "cost": self.NUM_COST}[self.tint]
        parts = [("Token：", self.PREFIX), (num, num_color)]
        if unit:
            parts.append((unit, self.PREFIX))
        parts.append(("   ", self.PREFIX))
        parts.append((self.time_text, self.THEMES.get(self.theme, self.THEMES["blue"])["time"]))
        return parts

    def desired_width(self):
        f = self._font()
        fm = QFontMetrics(f)
        total = sum(fm.horizontalAdvance(t) for t, _ in self._parts())
        return total + 42

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = self.rect().adjusted(0, 0, -1, -1)
        th = self.THEMES.get(self.theme, self.THEMES["blue"])

        # 白色圆角框（鲸鱼娘素材自带白框同款样式，主题色描边）
        body = QPainterPath()
        body.addRoundedRect(QRectF(r), 10, 10)
        p.setPen(QPen(th["frame"], 1.2))
        p.setBrush(QBrush(QColor(255, 255, 255, 238)))
        p.drawPath(body)

        # 居中分段文字：Token：数量[单位]   时间
        f = self._font()
        p.setFont(f)
        fm = QFontMetrics(f)
        parts = self._parts()
        total = sum(fm.horizontalAdvance(t) for t, _ in parts)
        x = r.center().x() - total / 2.0
        baseline = r.top() + (r.height() - fm.height()) / 2.0 + fm.ascent()
        for text, color in parts:
            p.setPen(color)
            p.drawText(QPointF(x, baseline), text)
            x += fm.horizontalAdvance(text)


class SettingsTitleBar(QWidget):
    """面板顶部标题栏：可拖动移动面板；右侧 ✕ 为备用关闭（默认仍是离开面板即关）。"""

    def __init__(self, panel, logo_path=""):
        super().__init__(panel)
        self.panel = panel
        self._drag_pos = None
        self.setFixedHeight(46)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 8, 16, 0)
        lay.setSpacing(10)
        if logo_path:
            logo_label = QLabel()
            lp = QPixmap(logo_path)
            if not lp.isNull():
                lp = lp.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(lp)
                lay.addWidget(logo_label)
        title = QLabel("小鲸鱼设置")
        title.setObjectName("title")
        lay.addWidget(title)
        lay.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(panel.close)
        lay.addWidget(close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.panel.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            screen = QApplication.primaryScreen()
            g = screen.availableGeometry() if screen else None
            nx = event.globalPos().x() - self._drag_pos.x()
            ny = event.globalPos().y() - self._drag_pos.y()
            if g:
                nx = max(g.left(), min(nx, g.right() - self.panel.width()))
                ny = max(g.top(), min(ny, g.bottom() - self.panel.height()))
            self.panel.move(nx, ny)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        if hasattr(self.panel, "pet"):
            self.panel.pet.remember_panel_geometry(self.panel)   # 记住位置，之后不再跟随桌宠
        event.accept()


class Card(QFrame):
    """设置面板分区卡片：标题 + 说明 + 可选「?」提示 + 内容区。"""

    def __init__(self, title, desc="", tip="", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(9)
        head = QHBoxLayout()
        head.setSpacing(6)
        t = QLabel(title)
        t.setObjectName("cardTitle")
        head.addWidget(t)
        head.addStretch()
        if tip:
            q = QLabel("?")
            q.setObjectName("cardTip")
            q.setToolTip(tip)
            q.setFixedSize(20, 20)
            q.setAlignment(Qt.AlignCenter)
            head.addWidget(q)
        lay.addLayout(head)
        if desc:
            d = QLabel(desc)
            d.setObjectName("cardDesc")
            d.setWordWrap(True)
            lay.addWidget(d)
        self.body = QVBoxLayout()
        self.body.setSpacing(9)
        lay.addLayout(self.body)
        self.keywords = f"{title} {desc} {tip}"

    def add(self, widget):
        self.body.addWidget(widget)
        self.keywords += " " + getattr(widget, "text", lambda: "")()
        return widget

    def add_layout(self, layout):
        self.body.addLayout(layout)
        return layout

    def add_checks(self, checks, cols=2):
        """复选框两列紧凑排布（内容自适应）。"""
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        for i, c in enumerate(checks):
            grid.addWidget(c, i // cols, i % cols)
            grid.setColumnStretch(i % cols, 1)
            self.keywords += " " + c.text()
        self.body.addLayout(grid)
        return grid

    def add_row(self, *widgets):
        row = QHBoxLayout()
        row.setSpacing(8)
        for wgt in widgets:
            row.addWidget(wgt)
        self.body.addLayout(row)
        return row


class SettingsPanel(QWidget):
    """标签页式多分区设置面板：互动 / Token / 气泡 / 系统。"""

    def __init__(self, pet):
        super().__init__()
        self.pet = pet
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(500)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        card = QFrame(self)
        card.setObjectName("glassCard")
        card.setStyleSheet("""
            QFrame#glassCard { background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(30,41,59,0.97), stop:1 rgba(15,23,42,0.97));
                border: 1px solid rgba(148,163,184,0.35); border-radius: 20px; color: #f8fafc; }
            QWidget { font-family: "Microsoft YaHei UI", "Microsoft YaHei"; }
            QLabel { color: #f8fafc; font-size: 16px; }
            QLabel#title { font-size: 24px; font-weight: 800; color: #22d3ee; }
            QLabel#section { font-size: 15px; color: #a5b4fc; font-weight: 700; margin-top: 8px; }
            QFrame#card { background: rgba(255,255,255,0.05);
                border: 1px solid rgba(148,163,184,0.22); border-radius: 14px; }
            QLabel#cardTitle { font-size: 16px; font-weight: 800; color: #67e8f9; }
            QLabel#cardDesc { font-size: 13px; color: #94a3b8; }
            QLabel#cardTip { background: rgba(148,163,184,0.30); border-radius: 10px;
                color: #e2e8f0; font-size: 13px; font-weight: 800; }
            QLabel#tokenLabel { color: #fbbf24; font-size: 16px; font-weight: 700; }
            QComboBox, QLineEdit {
                background: rgba(255,255,255,0.10); border: 1.5px solid rgba(255,255,255,0.22);
                border-radius: 10px; padding: 9px 12px; color: white; font-size: 16px; font-weight: 600;
            }
            QComboBox QAbstractItemView { background: #0f172a; color: white; selection-background-color: #2563eb;
                font-size: 15px; padding: 6px; border-radius: 10px; }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #7c3aed);
                border: none; border-radius: 11px; padding: 9px 12px; color: white;
                font-size: 16px; font-weight: 700;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #8b5cf6); }
            QPushButton#danger { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #b91c1c); }
            QPushButton#closeBtn { background: rgba(255,255,255,0.14); color: #f87171; border: none;
                border-radius: 14px; font-size: 16px; font-weight: 800; padding: 0; }
            QPushButton#closeBtn:hover { background: rgba(239,68,68,0.90); color: white; }
            QCheckBox { color: #e2e8f0; font-size: 16px; font-weight: 600; spacing: 8px; }
            QCheckBox:hover { color: #38bdf8; }
            QCheckBox::indicator { width: 20px; height: 20px; border-radius: 6px; border: 2px solid rgba(255,255,255,0.45);
                background: rgba(255,255,255,0.06); }
            QCheckBox::indicator:hover { border-color: #38bdf8; }
            QCheckBox::indicator:checked { background: #22d3ee; border-color: #22d3ee; }
            QSlider::groove:horizontal { height: 8px; border-radius: 4px; background: rgba(255,255,255,0.18); }
            QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #22d3ee); border-radius: 4px; }
            QSlider::handle:horizontal { background: white; width: 20px; height: 20px; margin: -6px 0; border-radius: 10px; border: 3px solid #22d3ee; }
            QTabWidget::pane { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; }
            QTabBar::tab { background: rgba(255,255,255,0.08); color: #cbd5e1; padding: 9px 16px;
                border-top-left-radius: 10px; border-top-right-radius: 10px; font-size: 15px; font-weight: 700; }
            QTabBar::tab:selected { background: #2563eb; color: white; }
            /* 深色细滚动条（列表 / 滚动区通用） */
            QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
            QScrollBar::handle:vertical { background: rgba(148,163,184,0.6); border-radius: 5px; min-height: 28px; }
            QScrollBar::handle:vertical:hover { background: rgba(56,189,248,0.8); }
            QScrollBar:horizontal { background: transparent; height: 0px; }
            QScrollBar::add-line, QScrollBar::sub-line { height: 0px; width: 0px; }
            QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32); shadow.setOffset(0, 8); shadow.setColor(QColor(0, 0, 0, 90))
        card.setGraphicsEffect(shadow)

        root_layout = QVBoxLayout(card)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(10)

        # 标题栏（可拖动 + ✕ 备用关闭）
        logo_path = ""
        for e in pet.expressions:
            if e["name"] == "DSniang1":
                logo_path = e["path"]
                break
        if not logo_path and pet.expressions:
            logo_path = pet.expressions[0]["path"]
        titlebar = SettingsTitleBar(self, logo_path)
        root_layout.addWidget(titlebar)

        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs)

        # ============ 互动页 ============
        page_interact = QWidget()
        p1 = QVBoxLayout(page_interact)
        p1.setSpacing(12)

        self.expr_combo = QComboBox()
        for e in pet.expressions:
            self.expr_combo.addItem(e["display"], e["name"])
        idx = self.expr_combo.findData(pet.expression)
        if idx >= 0:
            self.expr_combo.setCurrentIndex(idx)
        self.expr_combo.currentIndexChanged.connect(self._on_expr)

        self.click_rotate_slider = QSlider(Qt.Horizontal)
        self.click_rotate_slider.setRange(1, 100)
        self.click_rotate_slider.setValue(pet.click_rotate_count)
        self.click_rotate_value = QLabel(f"{pet.click_rotate_count} 下")
        self.click_rotate_slider.valueChanged.connect(self._on_click_rotate)

        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(SIZE_MIN, SIZE_MAX)
        self.size_slider.setValue(pet.size_level)
        self.size_value = QLabel(str(pet.size_level))
        self.size_slider.valueChanged.connect(self._on_size)
        self.size_slider.sliderPressed.connect(pet.begin_panel_lock)
        self.size_slider.sliderReleased.connect(self._on_size_done)

        card_look = Card("🎨 外观", "表情、连点换表情次数与角色大小",
                         tip="连点换表情：连续点击这么多次后换下一个表情（1~100）\n"
                             "大小：档位 1~20，对应 0.6~2.5 倍")
        card_look.add(self.expr_combo)
        card_look.add(QLabel("连点换表情"))
        card_look.add_layout(self._row(self.click_rotate_slider, self.click_rotate_value))
        card_look.add(QLabel("大小"))
        card_look.add_layout(self._row(self.size_slider, self.size_value))
        p1.addWidget(card_look)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(pet.volume)
        self.vol_value = QLabel(f"{pet.volume}%")
        self.vol_slider.valueChanged.connect(self._on_vol)

        self.sound_combo = QComboBox()
        self.sound_combo.addItem("小黄鸭", "duck")
        self.sound_combo.addItem("音效1", "fx1")
        for mode in pet.sounds:
            if mode not in ("duck", "fx1"):
                self.sound_combo.addItem(mode, mode)
        idx = self.sound_combo.findData(pet.sound_mode)
        if idx >= 0:
            self.sound_combo.setCurrentIndex(idx)
        self.sound_combo.currentIndexChanged.connect(self._on_sound_mode)
        self.sound_check = QCheckBox("启用音效")
        self.sound_check.setChecked(pet.sound_enabled)
        self.sound_check.toggled.connect(self._on_sound)

        card_sound = Card("🔊 声音", "音效开关、音效选择与音量",
                          tip="音效文件放在程序 sounds 目录里即可出现在列表中")
        card_sound.add(self.sound_combo)
        card_sound.add(self.sound_check)
        card_sound.add(QLabel("音量"))
        card_sound.add_layout(self._row(self.vol_slider, self.vol_value))
        p1.addWidget(card_sound)

        self.follow_check = QCheckBox("鼠标跟随")
        self.follow_check.setChecked(pet.follow_mode)
        self.follow_check.toggled.connect(self._on_follow_mode)
        self.evade_check = QCheckBox("躲避鼠标")
        self.evade_check.setChecked(pet.evade_mode)
        self.evade_check.toggled.connect(self._on_evade_mode)
        self.wander_check = QCheckBox("待机漫游")
        self.wander_check.setChecked(pet.wander_mode)
        self.wander_check.toggled.connect(self._on_wander_mode)

        card_act = Card("🕹️ 行为", "怎么动由你决定",
                        tip="跟随与躲避互斥（同时只会生效一个）；\n"
                            "待机漫游可以和躲避共存，久无操作时自己散步")
        card_act.add_checks([self.follow_check, self.evade_check, self.wander_check])
        p1.addWidget(card_act)

        self.mirror_check = QCheckBox("贴边自动镜像")
        self.mirror_check.setChecked(pet.auto_mirror)
        self.mirror_check.toggled.connect(self._on_mirror)
        self.lock_check = QCheckBox("固定位置（防止误拖）")
        self.lock_check.setChecked(pet.lock_position)
        self.lock_check.toggled.connect(self._on_lock)
        self.top_check = QCheckBox("始终置顶")
        self.top_check.setChecked(pet.always_on_top)
        self.top_check.toggled.connect(self._on_top)
        self.snap_check = QCheckBox("拖拽吸附屏幕边缘")
        self.snap_check.setChecked(pet.snap_enabled)
        self.snap_check.toggled.connect(self._on_snap)

        card_win = Card("🪟 窗口", "贴边、置顶与拖拽行为",
                        tip="贴边自动镜像：贴到屏幕左边缘时水平翻转（面朝屏内）\n"
                            "拖拽吸附边缘：松手时中心落在屏幕某侧 1/4 区域即贴边")
        card_win.add_checks([self.mirror_check, self.snap_check,
                             self.lock_check, self.top_check])
        p1.addWidget(card_win)
        p1.addStretch()

        # ============ Token 页 ============
        page_token = QWidget()
        p2 = QVBoxLayout(page_token)
        p2.setSpacing(12)
        self.token_check = QCheckBox("开启 Token 系统")
        self.token_check.setChecked(pet.token_enabled)
        self.token_check.toggled.connect(self._on_token_enabled)
        self.hud_check = QCheckBox("显示 Token HUD（桌宠下方）")
        self.hud_check.setChecked(pet.hud_visible)
        self.hud_check.toggled.connect(self._on_hud_visible)
        self.hud_abbrev_check = QCheckBox("HUD 数字缩写（如 388.4W）")
        self.hud_abbrev_check.setChecked(pet.hud_abbrev)
        self.hud_abbrev_check.toggled.connect(self._on_hud_abbrev)
        self.token_label = QLabel(f"当前 Token：{pet.token:,}")
        self.token_label.setObjectName("tokenLabel")
        token_row = QHBoxLayout()
        add_btn = QPushButton("+520W Token")
        add_btn.clicked.connect(self._on_add_tokens)
        clear_btn = QPushButton("清空 Token")
        clear_btn.setObjectName("danger")
        clear_btn.clicked.connect(self._on_clear_tokens)
        token_row.addWidget(add_btn)
        token_row.addWidget(clear_btn)

        card_token = Card("💰 趣味 Token", "点击/喂食消耗，可随时充值或清空",
                          tip="关闭 Token 系统后不影响互动与喂食，只是不再计数；\n"
                              "拖文件到桌宠身上也能喂食（会真实删除文件）")
        card_token.add(self.token_check)
        card_token.add(self.token_label)
        card_token.add_layout(token_row)
        p2.addWidget(card_token)

        card_hud = Card("🧾 HUD 显示", "桌宠下方的 Token / 时间显示",
                        tip="HUD 显示在角色下方，不遮挡角色；数字缩写示例：388.4W")
        card_hud.add_checks([self.hud_check, self.hud_abbrev_check])
        p2.addWidget(card_hud)
        p2.addStretch()

        # ============ 气泡页 ============
        page_bubble = QWidget()
        p3 = QVBoxLayout(page_bubble)
        p3.setSpacing(12)
        self.line_mode = QComboBox()
        self.line_mode.addItem("今日心情", "mood")
        self.line_mode.addItem("随机台词", "random")
        self.line_mode.addItem("自定义台词", "custom")
        self.line_mode.addItem("固定台词", "fixed")
        idx = self.line_mode.findData(pet.line_source)
        if idx >= 0:
            self.line_mode.setCurrentIndex(idx)
        self.line_mode.currentIndexChanged.connect(self._on_line_source)
        p3.addWidget(self.line_mode)

        self.custom_line_edit = QLineEdit(pet.fixed_line)
        self.custom_line_edit.setPlaceholderText("输入一句台词")
        self.custom_line_edit.textChanged.connect(self._on_fixed_line)
        p3.addWidget(self.custom_line_edit)
        self.custom_empty = QLabel("⚠️ 自定义台词库为空，请先添加")
        self.custom_empty.setStyleSheet("color:#fca5a5; font-size:14px; font-weight:700;")
        self.custom_list = QListWidget()
        self.custom_list.setMaximumHeight(120)
        self.custom_list.setWordWrap(True)
        self.custom_list.setSpacing(2)
        self.custom_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.custom_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.custom_list.setStyleSheet(LIST_QSS)
        add_btn = QPushButton("添加为自定义台词")
        add_btn.clicked.connect(self._on_add_custom)
        delete_btn = QPushButton("删除选中台词")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self._on_delete_custom)
        lines_btn = QPushButton("编辑台词文件（每行一句，txt）")
        lines_btn.clicked.connect(self._on_open_lines)

        card_line = Card("💬 台词", "决定她说什么",
                         tip="今日心情 / 随机台词 / 自定义台词 / 固定台词 四种模式\n"
                             "自定义台词也可以直接在 .dshw-pet-lines.txt 里一行一句地写")
        card_line.add(self.line_mode)
        card_line.add(self.custom_line_edit)
        card_line.add(self.custom_empty)
        card_line.add(self.custom_list)
        card_line.add_row(add_btn, delete_btn)
        card_line.add(lines_btn)
        p3.addWidget(card_line)
        self._refresh_custom_list()

        self.bubble_check = QCheckBox("显示气泡")
        self.bubble_check.setChecked(pet.bubble_on)
        self.bubble_check.toggled.connect(self._on_bubble)
        self.auto_close_slider = QSlider(Qt.Horizontal)
        self.auto_close_slider.setRange(1, 10)
        self.auto_close_slider.setValue(max(1, pet.bubble_close_sec))
        self.auto_close_value = QLabel(f"{pet.bubble_close_sec}秒")
        self.auto_close_slider.valueChanged.connect(self._on_bubble_close)
        self.color_combo = QComboBox()
        self.color_combo.addItem("蓝色", "blue")
        self.color_combo.addItem("粉色", "pink")
        self.color_combo.addItem("深色", "dark")
        self.color_combo.addItem("绿色", "green")
        idx = self.color_combo.findData(pet.bubble_color)
        if idx >= 0:
            self.color_combo.setCurrentIndex(idx)
        self.color_combo.currentIndexChanged.connect(self._on_bubble_color)
        self.show_time_check = QCheckBox("显示当前时间")
        self.show_time_check.setChecked(pet.show_time)
        self.show_time_check.toggled.connect(self._on_show_time)
        self.show_greeting_check = QCheckBox("时间问候")
        self.show_greeting_check.setChecked(pet.show_greeting)
        self.show_greeting_check.toggled.connect(self._on_show_greeting)

        card_bubble = Card("🫧 气泡", "气泡开关、外观与出现频率",
                           tip="气泡颜色同时决定 HUD 卡片描边主题；\n"
                               "对话频率控制点击时弹出台词的几率")
        card_bubble.add(self.bubble_check)
        card_bubble.add_checks([self.show_time_check, self.show_greeting_check])
        card_bubble.add(QLabel("气泡颜色"))
        card_bubble.add(self.color_combo)
        card_bubble.add(QLabel("关闭时间"))
        card_bubble.add_layout(self._row(self.auto_close_slider, self.auto_close_value))
        p3.addWidget(card_bubble)

        self.bubble_font_slider = QSlider(Qt.Horizontal)
        self.bubble_font_slider.setRange(10, 24)
        self.bubble_font_slider.setValue(pet.bubble_font_size)
        self.bubble_font_value = QLabel(f"{pet.bubble_font_size}px")
        self.bubble_font_slider.valueChanged.connect(self._on_bubble_font)
        self.bubble_scale_slider = QSlider(Qt.Horizontal)
        self.bubble_scale_slider.setRange(70, 140)
        self.bubble_scale_slider.setValue(int(pet.bubble_scale * 100))
        self.bubble_scale_value = QLabel(f"{int(pet.bubble_scale * 100)}%")
        self.bubble_scale_slider.valueChanged.connect(self._on_bubble_scale)
        self.bubble_freq_slider = QSlider(Qt.Horizontal)
        self.bubble_freq_slider.setRange(1, 100)
        self.bubble_freq_slider.setValue(pet.bubble_freq)
        self.bubble_freq_value = QLabel(f"{pet.bubble_freq}%")
        self.bubble_freq_slider.valueChanged.connect(self._on_bubble_freq)

        card_bubble_style = Card("🎚️ 气泡外观", "字号、框大小与出现频率",
                                 tip="框大小 100% 为默认；字号 10~24px")
        card_bubble_style.add(QLabel("字号"))
        card_bubble_style.add_layout(self._row(self.bubble_font_slider, self.bubble_font_value))
        card_bubble_style.add(QLabel("框大小"))
        card_bubble_style.add_layout(self._row(self.bubble_scale_slider, self.bubble_scale_value))
        card_bubble_style.add(QLabel("对话频率"))
        card_bubble_style.add_layout(self._row(self.bubble_freq_slider, self.bubble_freq_value))
        p3.addWidget(card_bubble_style)
        p3.addStretch()

        # ============ 系统页 ============
        page_system = QWidget()
        p4 = QVBoxLayout(page_system)
        p4.setSpacing(12)
        self.auto_rotate_check = QCheckBox("自动轮换表情")
        self.auto_rotate_check.setChecked(pet.auto_rotate)
        self.auto_rotate_check.toggled.connect(self._on_auto_rotate_setting)
        self.auto_rotate_interval_slider = QSlider(Qt.Horizontal)
        self.auto_rotate_interval_slider.setRange(5, 100)
        self.auto_rotate_interval_slider.setValue(pet.auto_rotate_interval)
        self.auto_rotate_interval_value = QLabel(f"{pet.auto_rotate_interval} 秒")
        self.auto_rotate_interval_slider.valueChanged.connect(self._on_auto_rotate_interval)
        self.idle_anim_check = QCheckBox("空闲自动表情动画")
        self.idle_anim_check.setChecked(pet.auto_emotion)
        self.idle_anim_check.toggled.connect(self._on_auto_emotion)
        self.blink_check = QCheckBox("空闲自动眨眼")
        self.blink_check.setChecked(pet.blink_enabled)
        self.blink_check.toggled.connect(self._on_blink)
        self.blink_slider = QSlider(Qt.Horizontal)
        self.blink_slider.setRange(5, 120)
        self.blink_slider.setValue(pet.blink_interval)
        self.blink_value = QLabel(f"{pet.blink_interval}秒")
        self.blink_slider.valueChanged.connect(self._on_blink_interval)

        card_anim = Card("🎬 自动动画", "不用管她时她自己会有的小动作",
                         tip="自动轮换：每隔设定秒数换一个表情\n"
                             "空闲动画：长时间没互动时做表情变化；眨眼按间隔随机眨")
        card_anim.add(QLabel("轮换间隔"))
        card_anim.add_layout(self._row(self.auto_rotate_interval_slider, self.auto_rotate_interval_value))
        card_anim.add_checks([self.auto_rotate_check, self.idle_anim_check, self.blink_check])
        card_anim.add(QLabel("眨眼间隔"))
        card_anim.add_layout(self._row(self.blink_slider, self.blink_value))
        p4.addWidget(card_anim)

        self.monitor_check = QCheckBox("开启应用打开监控")
        self.monitor_check.setChecked(pet.app_monitor_enabled)
        self.monitor_check.toggled.connect(self._on_app_monitor)
        self.rule_match_edit = QLineEdit()
        self.rule_match_edit.setPlaceholderText("匹配词：进程名/窗口标题，如 steam")
        self.rule_text_edit = QLineEdit()
        self.rule_text_edit.setPlaceholderText("触发台词，如：又在打游戏啦？")
        rule_btn_row = QHBoxLayout()
        add_rule_btn = QPushButton("添加规则")
        add_rule_btn.clicked.connect(self._on_add_rule)
        toggle_rule_btn = QPushButton("启用/停用")
        toggle_rule_btn.clicked.connect(self._on_toggle_rule)
        del_rule_btn = QPushButton("删除选中规则")
        del_rule_btn.setObjectName("danger")
        del_rule_btn.clicked.connect(self._on_delete_rule)
        rule_btn_row.addWidget(add_rule_btn)
        rule_btn_row.addWidget(toggle_rule_btn)
        rule_btn_row.addWidget(del_rule_btn)
        self.rule_list = QListWidget()
        self.rule_list.setMaximumHeight(146)
        self.rule_list.setWordWrap(True)
        self.rule_list.setSpacing(2)
        self.rule_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rule_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.rule_list.setStyleSheet(LIST_QSS)
        self.rule_list.itemDoubleClicked.connect(lambda item: self._on_toggle_rule())

        card_monitor = Card("🖥️ 应用打开监控", "打开指定软件时让她说一句",
                            tip="每行规则格式：匹配词 | 台词 | 触发概率 | 启用\n"
                                "触发概率 0~100（如 30 表示 30% 几率）；同一应用 5 分钟内只说一次\n"
                                "也可以直接编辑 .dshw-pet-rules.txt（文件内有详细说明）")
        card_monitor.add(self.monitor_check)
        card_monitor.add(self.rule_match_edit)
        card_monitor.add(self.rule_text_edit)
        card_monitor.add_layout(rule_btn_row)
        card_monitor.add(self.rule_list)
        card_monitor.add_row(self._plain_btn("编辑规则文件", self._on_open_rules),
                             self._plain_btn("重新加载规则", self._on_reload_external))
        p4.addWidget(card_monitor)
        self._refresh_rules()

        self.autostart_check = QCheckBox("开机自启")
        self.autostart_check.setChecked(is_autostart_enabled())
        self.autostart_check.toggled.connect(self._on_autostart)

        card_tools = Card("🛠️ 系统与工具", "开机自启、更新、音效与磁盘图标",
                          tip="开机自启会随系统启动并自动修正失效路径；\n"
                              "美化磁盘图标需要以管理员身份运行才生效")
        card_tools.add(self.autostart_check)
        # 系统操作按钮：两列网格，避免一排全宽按钮显得拥挤
        sys_grid = QGridLayout()
        sys_grid.setSpacing(8)
        actions = (
            ("美化磁盘图标", self.pet.beautify_drive_icons, "plain"),
            ("检查更新", self._on_check_update, "plain"),
            ("设置自定义音效", self._on_custom_sound, "plain"),
            ("清除自定义音效", self._on_clear_sound, "danger"),
            ("打开运行日志", self._on_open_log, "plain"),
        )
        for i, (label, handler, style) in enumerate(actions):
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            if style == "danger":
                btn.setObjectName("danger")
            if i == len(actions) - 1:
                sys_grid.addWidget(btn, i // 2, 0, 1, 2)     # 最后一个跨两列
            else:
                sys_grid.addWidget(btn, i // 2, i % 2)
        card_tools.add_layout(sys_grid)
        p4.addWidget(card_tools)

        about_card = Card("ℹ️ 关于", "版本、更新源与交流群",
                          tip="点「检查更新」会读取 GitHub Releases 的最新版本号对比")
        about_link = QLabel(
            f'<a href="{UPDATE_URL}" style="color:#93c5fd; text-decoration:none;">'
            f'小鲸鱼桌宠 v{LOCAL_VERSION} · 访问更新源</a>')
        about_link.setOpenExternalLinks(True)
        qq_label = QLabel(f"QQ 交流群：{QQ_GROUP}")
        qq_label.setStyleSheet("color:#94a3b8; font-size:13px;")
        about_card.add(about_link)
        about_card.add(qq_label)
        p4.addWidget(about_card)
        p4.addStretch()

        self.tabs.addTab(page_interact, "互动")
        self.tabs.addTab(page_token, "Token")
        self.tabs.addTab(page_bubble, "气泡")
        self.tabs.addTab(page_system, "系统")
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # 搜索框：过滤卡片（匹配卡片标题/说明/内部控件文字）
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索设置项（如 音量、泡泡、自启）")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._on_search)
        root_layout.insertWidget(1, self.search_edit)     # 放在标题栏下方
        self._cards = self.findChildren(Card)

        # 低分辨率屏幕才启用滚动区；高分辨率保持原来的样式
        screen = QApplication.primaryScreen()
        avail_h = screen.availableGeometry().height() if screen else 1080
        need_h = self.sizeHint().height()
        self.low_res_scroll = need_h > avail_h - 60
        if self.low_res_scroll:
            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setStyleSheet(
                "QScrollArea{background:transparent;border:none;}"
                "QScrollBar:vertical{width:8px;background:transparent;margin:2px;}"
                "QScrollBar::handle:vertical{background:rgba(148,163,184,0.55);border-radius:4px;}"
                "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
            card.setParent(None)
            scroll.setWidget(card)
            outer.addWidget(scroll)
            self.setFixedHeight(min(need_h, max(360, avail_h - 60)))
        else:
            outer.addWidget(card)

        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(150)
        self._hover_timer.timeout.connect(self._check_hover)
        self._hover_timer.start()
        self._open_time = time.monotonic()

    def _can_autoclose(self):
        """自动关闭保护：正在拖动控件 / 拖动桌宠 / 弹出菜单或对话框时不要关面板。"""
        if getattr(self.pet, "_panel_lock", False):
            return False
        if QApplication.mouseButtons() != Qt.NoButton:
            return False
        if QApplication.activeModalWidget() is not None:
            return False
        if QApplication.activePopupWidget() is not None:
            return False
        return True

    def _check_hover(self):
        if not self.isVisible():
            return
        if time.monotonic() - self._open_time < 0.5:
            return
        if not self._can_autoclose():
            return
        pos = QCursor.pos()
        if not self.frameGeometry().contains(pos):
            self.close()

    def ensure_on_screen(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        w = min(self.width(), geo.width() - 20)
        h = min(self.height(), geo.height() - 20)
        x = max(geo.left(), min(self.x(), geo.right() - w))
        y = max(geo.top(), min(self.y(), geo.bottom() - h))
        if self.width() != w or self.height() != h:
            self.setFixedWidth(max(300, int(w)))
        self.move(int(x), int(y))

    def changeEvent(self, event):
        if event.type() == QEvent.WindowDeactivate and self._can_autoclose():
            self.close()
        super().changeEvent(event)

    def _plain_btn(self, text, handler):
        """卡片内并排的次要按钮。"""
        btn = QPushButton(text)
        btn.clicked.connect(handler)
        return btn

    def _on_search(self, text):
        """按关键字过滤卡片（匹配卡片标题/说明/内部控件文字）。"""
        key = text.strip().lower()
        for card in self._cards:
            card.setVisible(not key or key in card.keywords.lower())

    def _on_tab_changed(self, index):
        """记住上次所在的标签页。"""
        self.pet.panel_tab = int(index)
        self.pet.save()

    def _row(self, widget, value_widget):
        row = QHBoxLayout()
        row.addWidget(widget)
        if value_widget is not None:
            row.addWidget(value_widget)
        return row

    # ---------- handlers ----------
    def _on_expr(self, index):
        name = self.expr_combo.itemData(index)
        if name:
            self.pet.apply_expression(name)
            self.pet.sync_rotation_from_current()

    def _on_size(self, val):
        self.size_value.setText(str(val))
        # 拖动过程中不写配置、不移动面板（松手后统一保存并校正位置）
        self.pet.set_size_level(val, save=False)

    def _on_size_done(self):
        self.pet.end_panel_lock()

    def _on_vol(self, val):
        self.vol_value.setText(f"{val}%")
        self.pet.set_volume(val)

    def _on_sound_mode(self, index):
        self.pet.set_sound_mode(self.sound_combo.itemData(index))

    def _on_line_source(self, index):
        self.pet.set_line_source(self.line_mode.itemData(index))

    def _on_fixed_line(self, text):
        self.pet.set_fixed_line_and_clear_custom(text)

    def _refresh_custom_list(self):
        self.custom_list.clear()
        for line in self.pet.custom_lines:
            self.custom_list.addItem(line)
        self.custom_empty.setVisible(len(self.pet.custom_lines) == 0)

    def _on_add_custom(self):
        text = self.custom_line_edit.text().strip()
        if text:
            self.pet.add_custom_line(text)
            self.pet.set_line_source("custom")
            idx = self.line_mode.findData("custom")
            if idx >= 0:
                self.line_mode.setCurrentIndex(idx)
            self.custom_line_edit.clear()
            self._refresh_custom_list()

    def _on_delete_custom(self):
        row = self.custom_list.currentRow()
        if row >= 0 and row < len(self.pet.custom_lines):
            del self.pet.custom_lines[row]
            self.pet.save()
            self._refresh_custom_list()

    def _on_bubble(self, enabled):
        self.pet.set_bubble_on(enabled)

    def _on_bubble_close(self, val):
        self.auto_close_value.setText(f"{val}秒")
        self.pet.set_bubble_close(val)

    def _on_bubble_color(self, index):
        self.pet.set_bubble_color(self.color_combo.itemData(index))

    def _on_show_time(self, enabled):
        self.pet.set_show_time(enabled)

    def _on_show_greeting(self, enabled):
        self.pet.set_show_greeting(enabled)

    def _on_bubble_font(self, val):
        self.bubble_font_value.setText(f"{val}px")
        self.pet.set_bubble_font_size(val)

    def _on_bubble_scale(self, val):
        self.bubble_scale_value.setText(f"{val}%")
        self.pet.set_bubble_scale(val / 100.0)

    def _on_bubble_freq(self, val):
        self.bubble_freq_value.setText(f"{val}%")
        self.pet.set_bubble_freq(val)

    def _on_auto_emotion(self, enabled):
        self.pet.set_auto_emotion(enabled)

    def _on_blink(self, enabled):
        self.pet.set_blink_enabled(enabled)

    def _on_blink_interval(self, val):
        self.blink_value.setText(f"{val}秒")
        self.pet.set_blink_interval(val)

    def _on_auto_rotate_setting(self, enabled):
        self.pet.set_auto_rotate(enabled)

    def _on_auto_rotate_interval(self, val):
        self.auto_rotate_interval_value.setText(f"{val} 秒")
        self.pet.set_auto_rotate_interval(val)

    def _on_click_rotate(self, val):
        self.click_rotate_value.setText(f"{val} 下")
        self.pet.set_click_rotate_count(val)

    def _on_mirror(self, enabled):
        self.pet.set_auto_mirror(enabled)

    def _on_follow_mode(self, enabled):
        self.pet.set_follow_mode(enabled)
        if enabled:
            self.evade_check.setChecked(False)

    def _on_evade_mode(self, enabled):
        self.pet.set_evade_mode(enabled)
        if enabled:
            self.follow_check.setChecked(False)

    def _on_wander_mode(self, enabled):
        self.pet.set_wander_mode(enabled)

    def _on_lock(self, enabled):
        self.pet.set_lock_position(enabled)

    def _on_sound(self, enabled):
        self.pet.set_sound_enabled(enabled)

    def _on_top(self, enabled):
        self.pet.set_always_on_top(enabled)

    def _on_autostart(self, enabled):
        self.pet.set_autostart(enabled)

    def _on_check_update(self):
        self.pet.check_update()

    def _on_custom_sound(self):
        self.pet.choose_custom_sound()

    def _on_open_log(self):
        self.pet.open_log()

    def _on_hud_visible(self, enabled):
        self.pet.set_hud_visible(enabled)

    def _on_hud_abbrev(self, enabled):
        self.pet.set_hud_abbrev(enabled)

    def _on_snap(self, enabled):
        self.pet.set_snap_enabled(enabled)

    def _on_app_monitor(self, enabled):
        self.pet.set_app_monitor_enabled(enabled)

    def _on_clear_sound(self):
        self.pet.clear_custom_sound()

    def _refresh_rules(self):
        self.rule_list.clear()
        for rule in self.pet.app_rules:
            if isinstance(rule, dict):
                mark = "开" if rule.get("enabled", True) else "关"
                chance = int(rule.get("chance", 100))
                # 两行显示：状态 + 匹配词 + 概率 / 触发台词（不截断、不拥挤）
                self.rule_list.addItem(
                    f"[{mark}] {rule.get('match', '')}　·　{chance}%\n{rule.get('text', '')}")

    def _on_add_rule(self):
        match = self.rule_match_edit.text().strip()
        text = self.rule_text_edit.text().strip()
        if not match or not text:
            self.pet.show_bubble_quick("请先填写匹配词和台词")
            return
        self.pet.app_rules.append({"match": match, "text": text, "chance": 100, "enabled": True})
        self.pet.save_rules()
        self.rule_match_edit.clear()
        self.rule_text_edit.clear()
        self._refresh_rules()

    def _on_delete_rule(self):
        row = self.rule_list.currentRow()
        if 0 <= row < len(self.pet.app_rules):
            del self.pet.app_rules[row]
            self.pet.save_rules()
            self._refresh_rules()

    def _on_toggle_rule(self):
        row = self.rule_list.currentRow()
        if 0 <= row < len(self.pet.app_rules) and isinstance(self.pet.app_rules[row], dict):
            rule = self.pet.app_rules[row]
            rule["enabled"] = not rule.get("enabled", True)
            self.pet.save_rules()
            self._refresh_rules()

    def _on_open_lines(self):
        self.pet.open_lines_file()

    def _on_open_rules(self):
        self.pet.open_rules_file()

    def _on_reload_external(self):
        self.pet.reload_external()
        self._refresh_rules()

    def _on_token_enabled(self, enabled):
        self.pet.set_token_enabled(enabled)
        self.token_label.setText(f"当前 Token：{self.pet.token:,}")

    def _on_add_tokens(self):
        self.pet.add_tokens(5200000)
        self.token_label.setText(f"当前 Token：{self.pet.token:,}")

    def _on_clear_tokens(self):
        self.pet.clear_tokens()
        self.token_label.setText(f"当前 Token：{self.pet.token:,}")

class PetWindow(QWidget):
    update_done = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAcceptDrops(True)          # 允许拖文件/文件夹进来喂食

        self.cfg = load_config()
        self.size_level = int(self.cfg.get("size_level", DEFAULT_SIZE_LEVEL))
        self.size_px = size_level_to_px(self.size_level)
        self.expression = "DSniang1"
        if self.expression.startswith(("v1_angry", "v2_angry", "v3_angry", "v4_angry",
                                        "v1_disappointed", "v2_disappointed", "v3_disappointed", "v4_disappointed",
                                        "v1_half_closed_eyes", "v2_half_closed_eyes", "v3_half_closed_eyes", "v4_half_closed_eyes",
                                        "v1_close_eyes", "v2_close_eyes", "v3_close_eyes", "v4_close_eyes")):
            self.expression = "DSniang1"
        self.click_text = self.cfg.get("click_text", "")
        self.line_source = self.cfg.get("line_source", "mood")
        self.fixed_line = self.cfg.get("fixed_line", "")
        self.custom_lines = list(self.cfg.get("custom_lines", []))
        if self.line_source == "random" and not self.custom_lines:
            self.line_source = "mood"
        self.random_enabled = bool(self.cfg.get("random_enabled", True))
        self.bubble_on = bool(self.cfg.get("bubble_on", True))
        self.bubble_close_sec = int(self.cfg.get("bubble_close_sec", 3))
        self.bubble_color = self.cfg.get("bubble_color", "blue")
        self.show_time = bool(self.cfg.get("show_time", True))
        self.show_greeting = bool(self.cfg.get("show_greeting", True))
        self.bubble_font_size = int(self.cfg.get("bubble_font_size", 13))
        self.bubble_scale = float(self.cfg.get("bubble_scale", 1.0))
        self.bubble_freq = int(self.cfg.get("bubble_freq", 100))
        self.auto_emotion = bool(self.cfg.get("auto_emotion", True))
        self.blink_enabled = bool(self.cfg.get("blink_enabled", True))
        self.blink_interval = int(self.cfg.get("blink_interval", 30))
        self.auto_rotate = bool(self.cfg.get("auto_rotate", True))
        self.auto_rotate_interval = max(5, min(100, int(self.cfg.get("auto_rotate_interval", 60))))
        self.click_rotate_count = max(1, min(100, int(self.cfg.get("click_rotate_count", 30))))
        self.token_enabled = bool(self.cfg.get("token_enabled", True))
        self.token = int(self.cfg.get("token", 1000000))
        if self.token < 0:
            self.token = 0
        self._shown_token = self.token
        self._token_roll = None
        self.follow_mode = bool(self.cfg.get("follow_mode", False))
        self.evade_mode = bool(self.cfg.get("evade_mode", False))
        self.wander_mode = bool(self.cfg.get("wander_mode", False))
        self._vx = 0.0
        self._vy = 0.0
        self._r_pressed = False
        self._r_dragging = False
        self._press_global = None
        self._char_at_press = None
        self._sling_active = False
        self._sling_vx = 0.0
        self._sling_vy = 0.0
        self._last_bounce_at = 0.0
        self._after_right_drag = False
        self._last_interact = time.monotonic()
        self._wander_on = False
        self._wander_mode_state = "stop"
        self._wander_delay = 0.0
        self._wander_speed = 0.0
        self._wander_angle = 0.0
        self._wander_turn = 0.0
        self._wander_steps_left = 0
        self._click_count = 0
        self._press_at = 0.0
        self._rotate_pos = 0
        self.auto_mirror = bool(self.cfg.get("auto_mirror", True))
        self.lock_position = bool(self.cfg.get("lock_position", False))
        self.always_on_top = bool(self.cfg.get("always_on_top", True))
        self.sound_enabled = bool(self.cfg.get("sound_enabled", True))
        self.sound_mode = self.cfg.get("sound_mode", "duck")
        self.volume = int(self.cfg.get("volume", 70))
        self.custom_sound_path = self.cfg.get("custom_sound_path", "")
        if self.custom_sound_path and not os.path.exists(self.custom_sound_path):
            self._log("自定义音效文件不存在，已自动清除：" + self.custom_sound_path)
            self.custom_sound_path = ""
        self.autostart = bool(self.cfg.get("autostart", False))
        self.hud_visible = bool(self.cfg.get("hud_visible", True))
        self.hud_abbrev = bool(self.cfg.get("hud_abbrev", True))
        self.panel_pinned = bool(self.cfg.get("panel_pinned", False))
        _pos = self.cfg.get("panel_pos")
        self.panel_pos = list(_pos) if isinstance(_pos, (list, tuple)) and len(_pos) == 2 else None
        self.panel_tab = max(0, min(3, int(self.cfg.get("panel_tab", 0))))
        self.snap_enabled = bool(self.cfg.get("snap_enabled", True))
        self.app_monitor_enabled = bool(self.cfg.get("app_monitor_enabled", True))
        rules = self.cfg.get("app_rules")
        if not isinstance(rules, list) or not rules:
            rules = copy.deepcopy(DEFAULT_APP_RULES)
        self.app_rules = rules
        ensure_lines_file(RANDOM_TEXTS)
        self.lines_file = load_lines_file()
        file_rules = load_rules_file()
        if file_rules:
            self.app_rules = file_rules
        else:
            write_rules_file(self.app_rules)

        self.setFixedSize(self.size_px, self.size_px + 34)

        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.size_px, self.size_px)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setScaledContents(True)
        self._fade_effect = QGraphicsOpacityEffect(self.label)
        self.label.setGraphicsEffect(self._fade_effect)

        self.bubble = BubbleWidget()
        self.bubble.apply_color(self.bubble_color)

        self.hud_card = HudCard(self)
        self._hud_timer = QTimer(self)
        self._hud_timer.timeout.connect(self._update_hud)
        self._hud_timer.start(1000)
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._monitor_tick)
        self._monitor_timer.start(2000)
        self._last_fore_exe = ""
        self._rule_fire_time = {}
        self._checking_update = False
        self.update_done.connect(self._on_update_done)
        self._update_hud()

        self._sfx_pool = []
        self._sfx_seq = 0
        self._evade_tele_at = 0.0
        self._panel_lock = False
        self.sounds = {}
        self._squish_anim = None
        self._fade_anim = None
        self._base_pixmap = None

        self.movie = None
        self._drag_pos = None
        self._dragging = False
        self._moved = False
        self.settings_panel = None

        self._last_expression = self.expression
        self._idle_8s = QTimer(self)
        self._idle_8s.setSingleShot(True)
        self._idle_8s.timeout.connect(self._on_idle_8s)
        self._idle_120s = QTimer(self)
        self._idle_120s.setSingleShot(True)
        self._idle_120s.timeout.connect(self._on_idle_120s)
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._do_blink)
        self._blink_back_timer = QTimer(self)
        self._blink_back_timer.setSingleShot(True)
        self._blink_back_timer.timeout.connect(self._restore_after_blink)
        self._auto_rotate_timer = QTimer(self)
        self._auto_rotate_timer.timeout.connect(self._on_auto_rotate)
        self._move_timer = QTimer(self)
        self._move_timer.timeout.connect(self._move_tick)
        self._move_timer.start(16)

        self.expressions = scan_expressions()
        self.apply_expression(self.expression, save=False, play_sound=False)

        if self.cfg.get("x") is not None and self.cfg.get("y") is not None:
            self.move(int(self.cfg["x"]), int(self.cfg["y"]))
        else:
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(geo.right() - self.width() - 30, geo.bottom() - self.height() - 60)

        self._load_sounds()
        self._sync_autostart()
        self._reset_idle_timers()
        self._log("小鲸鱼桌宠启动")

    # ---------- 音效（播放器池：每声完整播放、零延迟、最多池上限层不糊） ----------
    def _load_sounds(self):
        builtin = {
            "duck": {"click": "Ya1.mp3", "release": "Ya2.mp3"},
            "fx1": {"click": "D1.mp3", "release": "D2.mp3"},
        }
        self.sounds = {}
        for mode, pair in builtin.items():
            resolved = {}
            for kind, fname in pair.items():
                p = os.path.join(EXPR_DIR, fname)
                if not os.path.exists(p):
                    alt = os.path.expanduser(
                        r"~\.dsh\profiles\desktop\node_modules\dsh-whale-widget\assets\\" + fname)
                    if os.path.exists(alt):
                        p = alt
                    else:
                        continue
                resolved[kind] = p
            if resolved:
                self.sounds[mode] = resolved
        self.sounds.update(scan_sounds())
        self._sfx_pool = [QMediaPlayer() for _ in range(SFX_POOL_SIZE)]
        for player in self._sfx_pool:
            player.setVolume(self.volume)
        self._preload_sound()

    def _sound_path_for(self, kind):
        # 自定义音效优先：覆盖点击 / 松手 / 弹射 / 反弹全部音效
        if self.custom_sound_path and os.path.exists(self.custom_sound_path):
            return self.custom_sound_path
        item = self.sounds.get(self.sound_mode)
        if item:
            return item.get(kind) or item.get("click")
        return None

    def _preload_sound(self):
        """把当前音效预加载到池内全部播放器，播放时零加载延迟。"""
        path = self._sound_path_for("click")
        if not path:
            return
        content = QMediaContent(QUrl.fromLocalFile(path))
        for player in self._sfx_pool:
            if getattr(player, "_dsh_path", "") != path:
                player.setMedia(content)
                player._dsh_path = path

    def play_sound(self, key="click"):
        if not self.sound_enabled or not self._sfx_pool:
            return
        path = self._sound_path_for("release" if key == "release" else "click")
        if not path:
            return
        try:
            # 优先用空闲播放器 → 每声都能完整播放；都在播则接管最早的一声
            player = None
            for p in self._sfx_pool:
                if p.state() != QMediaPlayer.PlayingState:
                    player = p
                    break
            if player is None:
                player = self._sfx_pool[self._sfx_seq % len(self._sfx_pool)]
                self._sfx_seq += 1
                player.stop()
            else:
                player.setPosition(0)
            if getattr(player, "_dsh_path", "") != path:
                player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
                player._dsh_path = path
            player.setVolume(self.volume)
            player.play()
        except Exception:
            pass

    # ---------- 表情 ----------
    def _mirror_pixmap(self, pix):
        if self.auto_mirror and self._near_left_edge():
            return pix.transformed(QTransform().scale(-1, 1))
        return pix

    def _near_left_edge(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return False
        return self.x() <= screen.availableGeometry().left() + 10

    def apply_expression(self, name, save=True, play_sound=True, fade=True):
        target = None
        for e in self.expressions:
            if e["name"] == name:
                target = e
                break
        if target is None:
            if self.expressions:
                target = self.expressions[0]
            else:
                return
        name = target["name"]
        self.expression = name

        if self.movie is not None:
            self.movie.stop()
            self.movie = None

        if target["path"].lower().endswith(".gif"):
            self.movie = QMovie(target["path"])
            self.movie.setScaledSize(QSize(self.size_px, self.size_px))
            self.label.setMovie(self.movie)
            self.movie.start()
        else:
            pix = QPixmap(target["path"])
            if not pix.isNull():
                self._base_pixmap = pix.scaled(self.size_px, self.size_px, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.label.setPixmap(self._mirror_pixmap(self._base_pixmap))

        if save:
            self.save()
        self._last_expression = name

        if fade:
            self._play_fade()

    def _play_fade(self):
        if self._fade_anim is not None:
            self._fade_anim.stop()
        anim = QPropertyAnimation(self._fade_effect, b"opacity")
        anim.setDuration(180)
        anim.setStartValue(0.3)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._fade_anim = anim

    # ---------- 自动情绪 ----------
    def _reset_idle_timers(self):
        self._idle_8s.start(8000)
        self._idle_120s.start(120000)
        if self.blink_enabled and not self._blink_timer.isActive():
            self._blink_timer.start(self.blink_interval * 1000)
        if self.auto_rotate:
            if not self._auto_rotate_timer.isActive():
                self._auto_rotate_timer.start(self.auto_rotate_interval * 1000)
        else:
            self._auto_rotate_timer.stop()

    def _on_idle_8s(self):
        if self.auto_emotion and not self._moved:
            if self.expression not in ("v1_half_closed_eyes", "v2_half_closed_eyes", "v3_half_closed_eyes", "v4_half_closed_eyes"):
                self.apply_expression("v1_half_closed_eyes", save=False, fade=True)

    def _on_idle_120s(self):
        if self.auto_emotion:
            self.apply_expression("v1_disappointed", save=False, fade=True)

    def _do_blink(self):
        if not self.blink_enabled or self._dragging:
            return
        current = self.expression
        if "close_eyes" not in current and "half_closed" not in current:
            self._blink_orig_expression = self.expression
            self.apply_expression("v1_close_eyes", save=False, play_sound=False, fade=False)
            self._blink_back_timer.start(260)
        self._blink_timer.start(self.blink_interval * 1000)

    def _restore_after_blink(self):
        if self.blink_enabled:
            self.apply_expression(getattr(self, "_blink_orig_expression", self._last_expression),
                                  save=False, play_sound=False, fade=False)

    def _rotation_names(self):
        return [e["name"] for e in self.expressions
                if e["name"] != "DSniang1" and not e["name"].endswith("_DSniang1")]

    def _next_auto_expression(self):
        names = self._rotation_names()
        if not names:
            return
        if self._rotate_pos >= len(names):
            self._rotate_pos = 0
            self.apply_expression("DSniang1", save=False, play_sound=False)
            return
        name = names[self._rotate_pos]
        self._rotate_pos += 1
        self.apply_expression(name, save=False, play_sound=False)

    def _next_click_expression(self):
        names = self._rotation_names()
        if not names:
            return
        if self._rotate_pos >= len(names):
            self._rotate_pos = 0
            self.apply_expression("DSniang1", save=False, play_sound=False)
            return
        name = names[self._rotate_pos]
        self._rotate_pos += 1
        self.apply_expression(name, save=False, play_sound=False)

    def sync_rotation_from_current(self):
        names = self._rotation_names()
        if self.expression == "DSniang1" or self.expression.endswith("_DSniang1"):
            self._rotate_pos = 0
            return
        try:
            idx = names.index(self.expression)
            self._rotate_pos = idx + 1
        except ValueError:
            self._rotate_pos = 0

    def _on_auto_rotate(self):
        if self.auto_rotate and not self._dragging:
            self._next_auto_expression()

    def _click_counted(self):
        self._click_count += 1
        if self._click_count >= self.click_rotate_count:
            self._click_count = 0
            self._next_click_expression()

    # ---------- 气泡 ----------
    def show_bubble(self):
        if not self.bubble_on:
            return
        text = self.click_text.strip()
        if not text:
            text = self._pick_line()
        if not text:
            return
        if self.line_source == "random" and random.randrange(100) >= self.bubble_freq:
            return
        lines = []
        if self.show_time:
            lines.append(f"当前时间 {time.strftime('%H:%M')}")
        if self.show_greeting:
            h = time.localtime().tm_hour
            if 5 <= h < 11:
                greeting = "早上好"
            elif 11 <= h < 13:
                greeting = "中午好"
            elif 13 <= h < 18:
                greeting = "下午好"
            else:
                greeting = "晚上好"
            if text.startswith("今日心情"):
                text = f"{greeting}，{text}"
        lines.append(text)
        self.bubble.apply_color(self.bubble_color)
        self.bubble.set_style(self.bubble_font_size, self.bubble_scale)
        self.bubble.show_lines(lines, self.bubble_close_sec * 1000, pet=self)

    def _pick_line(self):
        if self.line_source == "mood":
            return "今日心情：" + random.choice(MOODS)
        if self.line_source == "fixed":
            return self.fixed_line
        if self.line_source == "custom":
            pool = self.lines_file + self.custom_lines
            if pool:
                return random.choice(pool)
            return ""
        # random
        pool = self.lines_file + self.custom_lines
        if self.random_enabled and pool:
            return random.choice(pool + RANDOM_TEXTS)
        if self.random_enabled:
            return random.choice(RANDOM_TEXTS)
        return ""

    # ---------- Token 趣味系统 ----------
    def _apply_layout(self):
        # 鲸鱼娘同款白框比例：宽约角色 86%、高约角色 15%；与角色不重叠，避免挡字
        card_h = max(32, round(self.size_px * 0.15))
        card_w = max(round(self.size_px * 0.86), min(max(self.hud_card.desired_width(), 120), 320))
        win_w = max(self.size_px, card_w)
        if self.hud_visible:
            win_h = self.size_px + card_h + HUD_GAP
        else:
            win_h = self.size_px + 4
        if self.width() != win_w or self.height() != win_h:
            self.setFixedSize(win_w, win_h)
        self.hud_card.setFixedHeight(card_h)
        lx = (win_w - self.size_px) // 2
        self.label.setGeometry(lx, 0, self.size_px, self.size_px)
        self.hud_card.setGeometry((win_w - card_w) // 2, self.size_px + HUD_GAP, card_w, card_h)
        self.hud_card.setVisible(self.hud_visible)
        self.label.raise_()

    def _hud_font_px(self):
        # 鲸鱼娘基准 5% 偏小，放大到 6.5%（用户要求看得清）：13~18px
        return max(13, min(18, int(self.size_px * 0.065)))

    def _update_hud(self):
        try:
            now = time.strftime("%H:%M:%S")
        except Exception:
            now = ""
        self.hud_card.apply_theme(self.bubble_color)
        self.hud_card.set_content(self._shown_token, now, self._hud_font_px(), "idle", self.hud_abbrev)
        self._apply_layout()

    # ---------- 原版数字滚动动画（700ms easeOutCubic） ----------
    def _animate_token_to(self, target):
        if not self.token_enabled:
            return
        if self._token_roll is not None:
            self._token_roll.stop()
            self._token_roll = None
        if self._shown_token == target:
            return
        anim = QVariantAnimation(self)
        anim.setStartValue(self._shown_token)
        anim.setEndValue(int(target))
        anim.setDuration(700)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.valueChanged.connect(self._on_token_roll)
        anim.finished.connect(self._on_token_roll_done)
        anim.start()
        self._token_roll = anim

    def _on_token_roll(self, v):
        self._shown_token = int(v)
        if self.token_enabled:
            # 数字变化颜色反馈：增加 → 亮蓝（放大脉冲），消耗 → 红
            tint = "gain" if self.token > self._shown_token else "cost"
            pulse_font = self._hud_font_px() + (1 if tint != "idle" else 0)
            self.hud_card.set_content(self._shown_token, time.strftime("%H:%M:%S"),
                                      pulse_font, tint, self.hud_abbrev)
            self._apply_layout()

    def _on_token_roll_done(self):
        self._token_roll = None
        self._shown_token = self.token
        self._update_hud()

    def spend_token(self, n):
        if not self.token_enabled:
            return 0
        n = max(0, int(n))
        spend = min(n, self.token)
        self.token -= spend
        self.save()
        self._animate_token_to(self.token)
        return spend

    def add_tokens(self, amount=5200000):
        if not self.token_enabled:
            self.show_bubble_quick("Token 系统未开启")
            return
        self.token += int(amount)
        self.save()
        self._animate_token_to(self.token)
        self.show_bubble_quick("Token +520W！")

    def clear_tokens(self):
        ret = QMessageBox.question(
            self, "清空全部 Token",
            "确定要清空全部 Token 吗？\n清空后不影响点击/喂食，只是没有了 Token 余额。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.token = 0
            self.save()
            self._animate_token_to(self.token)
            self.show_bubble_quick("Token 已清空")

    def set_token_enabled(self, enabled):
        self.token_enabled = bool(enabled)
        if not self.token_enabled:
            self.token = 0
            self._shown_token = 0
            if self._token_roll is not None:
                self._token_roll.stop()
                self._token_roll = None
        self._update_hud()
        self.save()

    def show_bubble_quick(self, text):
        self.bubble.apply_color(self.bubble_color)
        self.bubble.show_lines([text], 2500, pet=self)

    def _scan_path_size(self, path):
        """统计路径大小，返回 (字节数, 是否因目录过大被截断)。
        大目录限量扫描（文件数或耗时达上限即停止），避免界面卡死。"""
        if os.path.isfile(path):
            try:
                return os.path.getsize(path), False
            except OSError:
                return 0, False
        total = 0
        count = 0
        capped = False
        start = time.monotonic()
        try:
            for root, _dirs, files in os.walk(path):
                for fn in files:
                    try:
                        total += os.path.getsize(os.path.join(root, fn))
                    except OSError:
                        pass
                    count += 1
                    if count >= SCAN_LIMIT_FILES or time.monotonic() - start > SCAN_LIMIT_SECONDS:
                        capped = True
                        break
                if capped:
                    break
        except OSError:
            pass
        return total, capped

    def feed_path(self, path):
        if not os.path.exists(path):
            return
        is_dir = os.path.isdir(path)
        name = os.path.basename(path) or path
        kind = "文件夹" if is_dir else "文件"
        size, capped = self._scan_path_size(path)
        tokens = max(1, size // 1024)
        note = ""
        if capped:
            note = (f"\n\nℹ️ 该{kind}内容很多，已只统计前 {SCAN_LIMIT_FILES:,} 个文件"
                    f"（约 {SCAN_LIMIT_SECONDS:.0f} 秒内）来换算 Token；\n"
                    f"喂食仍会删除整个{kind}。")
        ret = QMessageBox.question(
            self, "喂食 DeepSeek",
            f"是否将该{kind}喂给 DeepSeek？\n\n{kind}: {name}\n大小: {size:,} B\n"
            f"按 1KB = 1 Token 换算，将增加 {tokens:,} Token{note}\n\n"
            f"⚠️ 喂食后会真正删除该{kind}，确定继续吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret != QMessageBox.Yes:
            return
        try:
            if is_dir:
                import shutil
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError as e:
            self.show_bubble_quick(f"喂食失败：{kind}可能被占用")
            return
        if self.token_enabled:
            self.token += tokens
            self.save()
            self._animate_token_to(self.token)
            self.show_bubble_quick(f"✓ 喂食成功 +{tokens:,} Token")
        else:
            self.show_bubble_quick(f"✓ 已删除{kind}（Token 系统关闭）")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        self._stop_wander()
        self._last_interact = time.monotonic()
        handled = False
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.feed_path(url.toLocalFile())
                handled = True
        if handled:
            event.acceptProposedAction()
        else:
            event.ignore()

    # ---------- 系统能力 ----------
    def _log(self, msg):
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        except Exception:
            pass

    def _get_foreground_exe(self):
        try:
            import ctypes as _ct
            from ctypes import wintypes
            user32 = _ct.windll.user32
            kernel32 = _ct.windll.kernel32
            user32.GetForegroundWindow.restype = wintypes.HWND
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "", ""
            n = user32.GetWindowTextLengthW(hwnd)
            buf = _ct.create_unicode_buffer(max(1, n + 1))
            user32.GetWindowTextW(hwnd, buf, len(buf))
            title = buf.value
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, _ct.byref(pid))
            exe = ""
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel32.QueryFullProcessImageNameW.argtypes = [
                wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, _ct.POINTER(wintypes.DWORD)]
            hproc = kernel32.OpenProcess(0x1000, False, pid.value)
            if hproc:
                try:
                    size = wintypes.DWORD(512)
                    buf2 = _ct.create_unicode_buffer(size.value)
                    if kernel32.QueryFullProcessImageNameW(hproc, 0, buf2, _ct.byref(size)):
                        exe = os.path.basename(buf2.value)
                finally:
                    kernel32.CloseHandle(hproc)
            return exe.lower(), title
        except Exception:
            return "", ""

    def _rule_chance_hit(self, rule):
        """规则概率判定：chance 为 0~100 的百分比。"""
        chance = int(rule.get("chance", 100))
        return chance >= 100 or random.random() * 100 < chance

    def _monitor_tick(self):
        if not self.app_monitor_enabled or not self.bubble_on:
            return
        exe, title = self._get_foreground_exe()
        if not exe or "whaledesktop" in exe:
            return
        if exe == self._last_fore_exe:
            return
        self._last_fore_exe = exe
        now = time.monotonic()
        hay = exe + " " + title.lower()
        for i, rule in enumerate(self.app_rules):
            if not isinstance(rule, dict) or not rule.get("enabled"):
                continue
            match = str(rule.get("match", "")).strip().lower()
            text = str(rule.get("text", "")).strip()
            if not match or not text or match not in hay:
                continue
            if not self._rule_chance_hit(rule):
                continue        # 概率未命中：跳过这条规则            last = self._rule_fire_time.get(i, 0.0)
            if now - last < 300:
                return
            self._rule_fire_time[i] = now
            self._log(f"应用监控触发: {match} -> {text}（{exe} / {title}）")
            self.show_bubble_quick(text)
            return

    def check_update(self):
        if getattr(self, "_checking_update", False):
            return
        self._checking_update = True
        self.show_bubble_quick("正在检查更新...")
        threading.Thread(target=self._check_update_worker, daemon=True).start()

    def _check_update_worker(self):
        try:
            req = urllib.request.Request(
                "https://api.github.com/repos/shiyi312/DeepSeek-Whale-Desktop-Pet/releases/latest",
                headers={"User-Agent": "WhaleDesktopPet", "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8", "replace"))
            tag = str(data.get("tag_name", "")).strip().lstrip("vV")
            if not tag:
                raise RuntimeError("no release tag")
            local = LOCAL_VERSION.lstrip("vV")

            def _key(v):
                parts = []
                for s in v.split("."):
                    num = ""
                    for ch in s:
                        if ch.isdigit():
                            num += ch
                        else:
                            break
                    parts.append(int(num) if num else 0)
                while len(parts) < 3:
                    parts.append(0)
                return tuple(parts[:3])

            if _key(tag) > _key(local):
                self.update_done.emit(f"发现新版本 v{tag}，正在打开更新页面~")
                webbrowser.open(UPDATE_URL)
            else:
                self.update_done.emit(f"已经是最新版本啦（v{LOCAL_VERSION}）")
        except Exception as e:
            self._log(f"检查更新失败: {e}")
            msg = str(e)
            if "404" in msg or "not found" in msg.lower():
                self.update_done.emit("仓库还没有发布版本，已打开仓库页面")
            elif "timed out" in msg.lower() or "timeout" in msg.lower():
                self.update_done.emit("网络超时，已打开 GitHub 页面")
            else:
                self.update_done.emit("网络检查失败，已打开 GitHub 页面")
            try:
                webbrowser.open(UPDATE_URL)
            except Exception:
                pass
        finally:
            self._checking_update = False

    def _on_update_done(self, msg):
        self.show_bubble_quick(msg)

    def choose_custom_sound(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择自定义音效", os.path.expanduser("~"), "音频文件 (*.mp3 *.wav);;所有文件 (*.*)"
        )
        if path:
            self.custom_sound_path = path
            self._preload_sound()
            self.save()
            self.show_bubble_quick("自定义音效已设置（点击/松手/弹射全部生效）")

    def open_log(self):
        try:
            subprocess.Popen(["notepad", LOG_PATH])
        except Exception:
            pass


    # ---------- 互动玩法：跟随/躲避/漫游/右键发射 ----------
    def _center(self):
        return self.x() + self.width() / 2.0, self.y() + self.height() / 2.0

    def _move_center(self, cx, cy):
        nx, ny = self._clamp_pos(cx - self.width() / 2.0, cy - self.height() / 2.0)
        self.move(int(nx), int(ny))
        self.sync_settings_panel_position()
        self.sync_bubble_position()
        self._refresh_mirror()

    def _move_tick(self):
        dt = 1 / 60.0
        if self.lock_position:
            return
        if self.settings_panel is not None and self.settings_panel.isVisible():
            return
        if self._sling_active:
            self._sling_step(dt)
        elif self._r_dragging:
            self._right_drag_tick(dt)
        elif self.evade_mode and not self.follow_mode:
            if not self._evade_tick(dt):
                self._wander_tick(dt)
        elif self.follow_mode:
            self._follow_tick(dt)
        elif self.wander_mode:
            self._wander_tick(dt)

    def _follow_tick(self, dt):
        cur = QCursor.pos()
        cx, cy = self._center()
        tx = cur.x()
        ty = cur.y()
        dx, dy = tx - cx, ty - cy
        d = math.hypot(dx, dy)
        if d > 120:
            tx = cx + dx / d * 120
            ty = cy + dy / d * 120
        ax = 150.0 * (tx - cx) - 8.0 * self._vx
        ay = 150.0 * (ty - cy) - 8.0 * self._vy
        self._vx = max(-9000, min(9000, self._vx + ax * dt))
        self._vy = max(-9000, min(9000, self._vy + ay * dt))
        self._move_center(cx + self._vx * dt, cy + self._vy * dt)

    def _evade_tick(self, dt):
        cur = QCursor.pos()
        cx, cy = self._center()
        dx = cx - cur.x()
        dy = cy - cur.y()
        d = math.hypot(dx, dy)
        if d >= 500:
            self._vx *= 0.85
            self._vy *= 0.85
            return False
        # 被逼到角落（离两边都 <= EVADE_CORNER_MARGIN）→ 瞬移到对角，20s 冷却
        screen = QApplication.primaryScreen()
        if screen:
            g = screen.availableGeometry()
            m = 20.0
            near_left = cx <= g.left() + self.width() / 2.0 + m
            near_right = cx >= g.right() - self.width() / 2.0 - m
            near_top = cy <= g.top() + self.height() / 2.0 + m
            near_bottom = cy >= g.bottom() - self.height() / 2.0 - m
            cornered = (near_left or near_right) and (near_top or near_bottom)
            if cornered and time.monotonic() - self._evade_tele_at > 20.0:
                self._evade_tele_at = time.monotonic()
                nx = g.right() - self.width() / 2.0 - m if near_left else g.left() + self.width() / 2.0 + m
                ny = g.bottom() - self.height() / 2.0 - m if near_top else g.top() + self.height() / 2.0 + m
                self._vx = self._vy = 0.0
                self._move_center(nx, ny)
                self.play_sound("release")
                self._log("躲避：被逼到角落，瞬移到对角")
                return True
        if d < 1:
            ang = random.uniform(0, math.tau)
            ux, uy = math.cos(ang), math.sin(ang)
        else:
            ux, uy = dx / d, dy / d
        sp = 600.0 * 500.0 / max(d, 1)
        tvx, tvy = ux * sp, uy * sp
        k = min(1.0, 3.0 * dt)
        self._vx += (tvx - self._vx) * k
        self._vy += (tvy - self._vy) * k
        self._move_center(cx + self._vx * dt, cy + self._vy * dt)
        return True

    def _stop_wander(self):
        """任何用户交互立即停止漫游（对标鲸鱼娘 _touch）。"""
        if self._wander_on:
            self._wander_on = False
            self._wander_speed = 0.0
            self._wander_mode_state = "stop"

    def _wander_tick(self, dt):
        if not self._wander_on:
            if time.monotonic() - self._last_interact < 60:
                return
            # 与需要保持静止/占用的状态互斥（对标鲸鱼娘 frozen/follow/弹射/右键拖拽）
            if self.follow_mode or self._sling_active or self._r_dragging or self.lock_position:
                return
            self._wander_on = True
            self._wander_mode_state = "stop"
            self._wander_delay = random.uniform(0.5, 2.0)   # 起步前先停一会儿
            self._wander_angle = random.uniform(0, math.tau)
            self._wander_turn = 0.0
            self._wander_steps_left = 0

        if self._wander_mode_state == "stop":
            self._wander_delay -= dt
            if self._wander_delay <= 0:
                self._wander_steps_left = random.randint(2, 5)
                self._start_wander_burst()
            return

        self._wander_delay -= dt
        if self._wander_delay <= 0:
            self._wander_steps_left -= 1
            if self._wander_steps_left <= 0:
                self._wander_mode_state = "stop"
                self._wander_delay = random.uniform(2.0, 6.0)   # 停下来休息（对标鲸鱼娘）
                self._wander_speed = 0.0
                return
            self._start_wander_burst()
            return
        self._wander_turn = max(-1.2, min(1.2, self._wander_turn + random.uniform(-0.6, 0.6) * dt))
        self._wander_angle += self._wander_turn * dt
        edge = self._wander_edge_target()
        if edge is not None:
            self._wander_angle += (edge - self._wander_angle) * 0.05   # 向屏幕内弱回正
        cx, cy = self._center()
        self._move_center(cx + math.cos(self._wander_angle) * self._wander_speed * dt,
                          cy + math.sin(self._wander_angle) * self._wander_speed * dt)

    def _wander_edge_target(self):
        """靠近屏幕边缘时，把朝向慢慢拉向屏幕中心，避免走出屏幕（对标鲸鱼娘）。"""
        screen = QApplication.primaryScreen()
        if not screen:
            return None
        g = screen.availableGeometry()
        hw, hh = self.width() / 2.0, self.height() / 2.0
        near = 60.0
        cx, cy = self._center()
        if cx < g.left() + hw + near and math.cos(self._wander_angle) < 0:
            return 0.0                      # 左侧且朝左 → 转向右
        if cx > g.right() - hw - near and math.cos(self._wander_angle) > 0:
            return math.pi                  # 右侧且朝右 → 转向左
        if cy < g.top() + hh + near and math.sin(self._wander_angle) < 0:
            return math.pi / 2.0            # 顶部且朝上 → 转向下
        if cy > g.bottom() - hh - near and math.sin(self._wander_angle) > 0:
            return -math.pi / 2.0           # 底部且朝下 → 转向上
        return None

    def _start_wander_burst(self):
        self._wander_mode_state = "move"
        self._wander_speed = random.uniform(70, 150)
        self._wander_delay = random.uniform(1.0, 3.0)
        self._wander_angle += random.uniform(-0.9, 0.9)
        self._wander_turn = random.uniform(-1.2, 1.2)

    def _right_drag_tick(self, dt):
        """右键拖拽：朝鼠标方向弹簧跟随 + 橡皮筋阻尼（拉离按下点越远越重，对标鲸鱼娘）。"""
        cur = QCursor.pos()
        cx, cy = self._center()
        ax = 150.0 * ((cur.x() + self.width() / 2.0) - cx)
        ay = 150.0 * ((cur.y() + self.height() / 2.0) - cy)
        an = math.hypot(ax, ay)
        if an > 9000:
            ax *= 9000 / an
            ay *= 9000 / an
        axp, ayp = self._char_at_press or (cx, cy)
        d = math.hypot(cx - axp, cy - ayp)
        damp = min(22.0, 3.0 + 0.03 * d)
        self._vx = max(-4200, min(4200, self._vx + ax * dt))
        self._vy = max(-4200, min(4200, self._vy + ay * dt))
        decay = math.exp(-damp * dt)
        self._vx *= decay
        self._vy *= decay
        self._move_center(cx + self._vx * dt, cy + self._vy * dt)

    def _launch_sling(self):
        if self._char_at_press is None:
            return
        ax, ay = self._char_at_press
        bx, by = self._center()
        dx, dy = ax - bx, ay - by
        dist = math.hypot(dx, dy)
        if dist < 1:
            return
        ux, uy = dx / dist, dy / dist
        speed = min(8.1 * dist, 6840)
        self._sling_vx, self._sling_vy = ux * speed, uy * speed
        self._sling_active = True
        self._after_right_drag = True
        self.play_sound("release")
        self.show_bubble_quick("发射！")

    def _sling_step(self, dt):
        damp = math.exp(-1.0 * dt)
        self._sling_vx *= damp
        self._sling_vy *= damp
        cx, cy = self._center()
        nx = cx + self._sling_vx * dt
        ny = cy + self._sling_vy * dt
        screen = QApplication.primaryScreen()
        if screen:
            g = screen.availableGeometry()
            hw, hh = self.width() / 2.0, self.height() / 2.0
            hits = 0
            if nx - hw < g.left():
                nx = g.left() + hw
                self._sling_vx = abs(self._sling_vx)
                hits += 1
            elif nx + hw > g.right():
                nx = g.right() - hw
                self._sling_vx = -abs(self._sling_vx)
                hits += 1
            if ny - hh < g.top():
                ny = g.top() + hh
                self._sling_vy = abs(self._sling_vy)
                hits += 1
            elif ny + hh > g.bottom():
                ny = g.bottom() - hh
                self._sling_vy = -abs(self._sling_vy)
                hits += 1
            if hits:
                # 同帧撞到多条边（角落）时按 0.18s 间隔逐条发声，保证每条边都能听到
                now = time.monotonic()
                start = max(0.0, self._last_bounce_at + 0.18 - now)
                for i in range(hits):
                    QTimer.singleShot(int((start + i * 0.18) * 1000.0), self._play_bounce_sound)
                self._last_bounce_at = now
        self._move_center(nx, ny)
        if math.hypot(self._sling_vx, self._sling_vy) < 6:
            self._sling_active = False
            self._vx = self._vy = 0.0
            self.save()          # 弹射落点立即保存，重启不回跳

    def _play_bounce_sound(self):
        self.play_sound("click")

    # ---------- 鼠标/拖拽/边缘 ----------
    def _clamp_pos(self, x, y):
        screen = QApplication.primaryScreen()
        if not screen:
            return x, y
        geo = screen.availableGeometry()
        min_x = geo.left() - self.width() + EDGE_MARGIN
        max_x = geo.right() - EDGE_MARGIN
        min_y = geo.top() - self.height() + EDGE_MARGIN
        max_y = geo.bottom() - EDGE_MARGIN
        if self.width() <= geo.width():
            min_x = max(min_x, geo.left())
            max_x = min(max_x, geo.right() - self.width())
        if self.height() <= geo.height():
            min_y = max(min_y, geo.top())
            max_y = min(max_y, geo.bottom() - self.height())
        return max(min_x, min(max_x, x)), max(min_y, min(max_y, y))

    # ---------- 原版吸附/翻转：四边四分之一规则 ----------
    def _snap_to_edge(self):
        """原版逻辑：松手时中心落在屏幕某侧 1/4 区域即吸附该边（角落组合）。"""
        screen = QApplication.primaryScreen()
        if not screen:
            return
        g = screen.availableGeometry()
        cx = self.x() + self.width() / 2.0
        cy = self.y() + self.height() / 2.0
        x, y = self.x(), self.y()
        if cx < g.left() + g.width() / 4.0:
            x = g.left()
        elif cx > g.right() - g.width() / 4.0:
            x = g.right() - self.width()
        if cy < g.top() + g.height() / 4.0:
            y = g.top()
        elif cy > g.bottom() - g.height() / 4.0:
            y = g.bottom() - self.height()
        self.move(x, y)
        self._refresh_mirror()

    def mousePressEvent(self, event):
        card = getattr(self, "hud_card", None)
        if card is not None and card.isVisible() and card.geometry().contains(event.pos()):
            event.ignore()
            return
        self._stop_wander()
        self._last_interact = time.monotonic()
        if event.button() == Qt.RightButton:
            self._r_pressed = True
            self._r_dragging = False
            self._press_global = event.globalPos()
            self._char_at_press = self._center()
            self._after_right_drag = False
            event.accept()
            return
        if event.button() == Qt.LeftButton:
            # 仅记录状态：真正的"点击"在松手时判定（未拖动且快速松开才算）
            self._press_squish()
            self._press_at = time.monotonic()
            if self.lock_position:
                self._drag_pos = None
                self._dragging = False
                self._moved = False
            else:
                self._drag_pos = event.globalPos()
                self._dragging = True
                self._moved = False
            event.accept()

    def mouseMoveEvent(self, event):
        self._last_interact = time.monotonic()
        if self._r_pressed and (event.buttons() & Qt.RightButton):
            if self._press_global is not None:
                delta = event.globalPos() - self._press_global
                if not self._r_dragging and (abs(delta.x()) > 4 or abs(delta.y()) > 4):
                    self._r_dragging = True
                    self._vx = self._vy = 0.0
                    self._sling_active = False
            if self._r_dragging:
                self._right_drag_tick(1 / 60.0)
            event.accept()
            return
        if self._dragging and self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            delta = event.globalPos() - self._drag_pos
            if delta.manhattanLength() > 3:
                self._moved = True
            nx, ny = self._clamp_pos(self.x() + delta.x(), self.y() + delta.y())
            self.move(nx, ny)
            self.sync_settings_panel_position()
            self.sync_bubble_position()
            self._drag_pos = event.globalPos()
            self._reset_idle_timers()
            event.accept()

    def mouseReleaseEvent(self, event):
        self._last_interact = time.monotonic()
        if event.button() == Qt.LeftButton:
            was_drag = self._moved
            self._dragging = False
            self._drag_pos = None
            self._release_squish()
            # 真正的"点击"：未拖动且在按下后 0.55s 内松开（按住良久不算点击）
            is_click = (not was_drag) and (time.monotonic() - self._press_at <= 0.55)
            if is_click:
                self._click_counted()
                self.play_sound("click")
                self.spend_token(random.randint(200, 50000))
                self.show_bubble()
            elif was_drag:
                self.play_sound("release")
                if self.snap_enabled:
                    self._snap_to_edge()
                self.save()
            self._moved = False
            self._reset_idle_timers()
            event.accept()
        elif event.button() == Qt.RightButton:
            was_drag = self._r_dragging
            self._r_pressed = False
            self._r_dragging = False
            self._press_global = None
            if was_drag:
                self._launch_sling()
            else:
                self._after_right_drag = True
                self.open_settings(event.globalPos())
            event.accept()

    def contextMenuEvent(self, event):
        if self._after_right_drag:
            self._after_right_drag = False
            event.ignore()
            return
        self.open_settings(event.globalPos())

    # ---------- Q弹（原版：按压底部坐标不变，回弹带弹簧） ----------
    def _squish_rect(self, sx, sy):
        w = int(self.size_px * sx)
        h = int(self.size_px * sy)
        x = (self.size_px - w) // 2
        y = self.size_px - h
        return QRect(x, y, w, h)

    def _animate_squish(self, sx, sy, duration=120, curve=QEasingCurve.OutCubic):
        if self._squish_anim is not None:
            self._squish_anim.stop()
        anim = QPropertyAnimation(self.label, b"geometry")
        anim.setDuration(duration)
        anim.setStartValue(self.label.geometry())
        anim.setEndValue(self._squish_rect(sx, sy))
        anim.setEasingCurve(curve)
        anim.start()
        self._squish_anim = anim

    def _press_squish(self):
        self._animate_squish(1.05, 0.88, 90)

    def _release_squish(self):
        """松手：多关键帧 Q 弹（压扁 → 弹起过冲 → 回落），底部坐标不变。"""
        if self._squish_anim is not None:
            self._squish_anim.stop()
        anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(520)
        anim.valueChanged.connect(self._on_squash_frame)
        anim.finished.connect(self._on_squash_done)
        anim.start()
        self._squish_anim = anim

    def _on_squash_frame(self, t):
        sy, sx = squash_at(float(t))
        self.label.setGeometry(self._squish_rect(sx, sy))

    def _on_squash_done(self):
        self.label.setGeometry(self._squish_rect(1.0, 1.0))

    # ---------- 设置面板 ----------
    def open_settings(self, global_pos=None):
        if self.settings_panel is not None:
            try:
                self.settings_panel.close()
            except Exception:
                pass
        panel = SettingsPanel(self)
        self.settings_panel = panel
        # 记住的页签
        if 0 <= self.panel_tab < panel.tabs.count():
            panel.tabs.setCurrentIndex(self.panel_tab)
        if global_pos is not None:
            panel.move(global_pos.x(), global_pos.y())
        elif self.panel_pinned and self.panel_pos:
            panel.move(int(self.panel_pos[0]), int(self.panel_pos[1]))   # 还原上次位置
        else:
            self.sync_settings_panel_position()
        panel.show()
        panel.ensure_on_screen()

    def remember_panel_geometry(self, panel):
        """记住用户拖动后的面板位置与当前页签（此后不再随桌宠移动）。"""
        self.panel_pinned = True
        self.panel_pos = [panel.x(), panel.y()]
        self.panel_tab = panel.tabs.currentIndex()
        self.save()

    def sync_settings_panel_position(self):
        if self.settings_panel is None or not self.settings_panel.isVisible():
            return
        if getattr(self, "_panel_lock", False):
            return          # 拖动大小滑块中：面板保持不动，防止滑块断触
        if self.panel_pinned:
            return          # 用户手动摆过位置：不再跟随桌宠移动
        pw = self.settings_panel.width()
        ph = self.settings_panel.height()
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = self.x() + self.width() + 4
            if x + pw > geo.right():
                x = self.x() - pw - 4
            y = self.y() - 10
            if y < geo.top():
                y = self.y() + self.height() - ph + 10 if ph < self.height() else geo.top()
            self.settings_panel.move(max(geo.left(), min(x, geo.right() - pw)),
                                     max(geo.top(), min(y, geo.bottom() - ph)))

    def sync_bubble_position(self):
        if self.bubble is None or not self.bubble.isVisible():
            return
        w = self.bubble.width()
        h = self.bubble.height()
        x = self.x() + (self.width() - w) // 2
        y = self.y() - h - 8
        if y < 0:
            y = self.y() + self.height() + 8
        self.bubble.move(max(0, x), max(0, y))

    # ---------- 设置方法 ----------
    def set_size_level(self, level, save=True):
        self.size_level = max(SIZE_MIN, min(SIZE_MAX, int(level)))
        self.size_px = size_level_to_px(self.size_level)
        self._apply_layout()
        self.apply_expression(self.expression, save=False, play_sound=False)
        if save:
            self.save()
        self.sync_settings_panel_position()

    def begin_panel_lock(self):
        """拖动大小滑块期间冻结面板位置/自动关闭，避免滑块断触乱跳。"""
        self._panel_lock = True

    def end_panel_lock(self):
        self._panel_lock = False
        self.save()
        self.sync_settings_panel_position()

    def set_volume(self, val):
        self.volume = max(0, min(100, int(val)))
        for player in self._sfx_pool:
            player.setVolume(self.volume)
        self.save()

    def set_sound_mode(self, mode):
        self.sound_mode = mode if mode in self.sounds else "duck"
        self._preload_sound()
        self.save()

    def set_line_source(self, source):
        self.line_source = source if source in ("mood", "random", "custom", "fixed") else "mood"
        self.save()

    def set_fixed_line_and_clear_custom(self, text):
        self.fixed_line = text.strip()
        if self.line_source == "fixed" and not self.fixed_line:
            self.line_source = "mood"
        self.save()

    def add_custom_line(self, text):
        text = text.strip()
        if text and text not in self.custom_lines:
            self.custom_lines.append(text)
            self.save()

    def set_bubble_on(self, enabled):
        self.bubble_on = bool(enabled)
        if not self.bubble_on:
            self.bubble.hide()
        self.save()

    def set_bubble_close(self, sec):
        self.bubble_close_sec = max(1, min(10, int(sec)))
        self.save()

    def set_bubble_color(self, color):
        self.bubble_color = color if color in BUBBLE_COLORS else "blue"
        self.bubble.apply_color(self.bubble_color)
        self.hud_card.apply_theme(self.bubble_color)
        self.save()

    def set_show_time(self, enabled):
        self.show_time = bool(enabled)
        self.save()

    def set_show_greeting(self, enabled):
        self.show_greeting = bool(enabled)
        self.save()

    def set_bubble_font_size(self, size):
        self.bubble_font_size = max(10, min(24, int(size)))
        self.save()

    def set_bubble_scale(self, scale):
        self.bubble_scale = max(0.7, min(1.4, float(scale)))
        self.save()

    def set_bubble_freq(self, freq):
        self.bubble_freq = max(1, min(100, int(freq)))
        self.save()

    def set_auto_emotion(self, enabled):
        self.auto_emotion = bool(enabled)
        self._reset_idle_timers()
        self.save()

    def set_auto_rotate(self, enabled):
        self.auto_rotate = bool(enabled)
        self._reset_idle_timers()
        self.save()

    def set_blink_enabled(self, enabled):
        self.blink_enabled = bool(enabled)
        if enabled:
            self._blink_timer.start(self.blink_interval * 1000)
        else:
            self._blink_timer.stop()
        self.save()

    def set_blink_interval(self, sec):
        self.blink_interval = max(5, min(120, int(sec)))
        if self.blink_enabled:
            self._blink_timer.start(self.blink_interval * 1000)
        self.save()

    def set_auto_mirror(self, enabled):
        self.auto_mirror = bool(enabled)
        self._refresh_mirror()

    def set_follow_mode(self, enabled):
        self.follow_mode = bool(enabled)
        if self.follow_mode:
            self.evade_mode = False
        self._vx = self._vy = 0.0
        self.save()

    def set_evade_mode(self, enabled):
        self.evade_mode = bool(enabled)
        if self.evade_mode:
            self.follow_mode = False
        self._vx = self._vy = 0.0
        self.save()

    def set_wander_mode(self, enabled):
        self.wander_mode = bool(enabled)
        self._wander_on = False
        self.save()

    def set_click_rotate_count(self, count):
        self.click_rotate_count = max(1, min(100, int(count)))
        self.save()

    def set_auto_rotate_interval(self, sec):
        self.auto_rotate_interval = max(5, min(100, int(sec)))
        if self.auto_rotate:
            self._auto_rotate_timer.start(self.auto_rotate_interval * 1000)
        self.save()

    def set_lock_position(self, enabled):
        self.lock_position = bool(enabled)
        self.save()

    def set_sound_enabled(self, enabled):
        self.sound_enabled = bool(enabled)
        self.save()

    def set_always_on_top(self, enabled):
        self.always_on_top = enabled
        flags = Qt.FramelessWindowHint | Qt.Tool
        if enabled:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self.save()

    def set_hud_visible(self, visible):
        self.hud_visible = bool(visible)
        self._apply_layout()
        self.save()

    def set_hud_abbrev(self, enabled):
        self.hud_abbrev = bool(enabled)
        self._update_hud()
        self.save()

    def save_rules(self):
        """保存规则（写配置 + 回写外部规则文件）。"""
        self.save()
        write_rules_file(self.app_rules)

    def reload_external(self):
        """重新加载台词文件与规则文件。"""
        ensure_lines_file(RANDOM_TEXTS)
        self.lines_file = load_lines_file()
        file_rules = load_rules_file()
        if file_rules:
            self.app_rules = file_rules
        self.save_rules()
        self.show_bubble_quick("台词与规则已重新加载")
        self._log(f"重新加载外部文件：台词 {len(self.lines_file)} 条，规则 {len(self.app_rules)} 条")

    def open_lines_file(self):
        ensure_lines_file(RANDOM_TEXTS)
        try:
            subprocess.Popen(["notepad", LINES_PATH])
        except Exception:
            pass

    def open_rules_file(self):
        if not os.path.exists(RULES_PATH):
            write_rules_file(self.app_rules)
        try:
            subprocess.Popen(["notepad", RULES_PATH])
        except Exception:
            pass

    def beautify_drive_icons(self):
        """一键把磁盘图标换成大肥鱼（写盘根 desktop.ini，需要管理员权限）。"""
        png = ""
        for e in self.expressions:
            if e["name"] == "v1_fatfish":
                png = e["path"]
                break
        if not png:
            self.show_bubble_quick("没有找到大肥鱼素材")
            return
        drives = list(os.listdrives()) if hasattr(os, "listdrives") else ["C:\\"]
        if not drives:
            return
        drive, ok = QInputDialog.getItem(
            self, "美化磁盘图标", "选择要美化的磁盘（需要管理员权限）：", drives, 0, False)
        if not ok or not drive:
            return
        ico = os.path.join(drive.rstrip("\\") + "\\", "dshw_fish.ico")
        if not build_fish_ico(png, ico):
            self.show_bubble_quick("图标生成失败")
            return
        if apply_drive_icon(drive, ico):
            self._log(f"磁盘图标美化：{drive}")
            self.show_bubble_quick(f"{drive} 图标已美化，刷新/重启后生效")
        else:
            self.show_bubble_quick("写入失败：请以管理员身份运行桌宠后重试")

    def toggle_hud(self):
        self.set_hud_visible(not self.hud_visible)

    def set_snap_enabled(self, enabled):
        self.snap_enabled = bool(enabled)
        self.save()

    def set_app_monitor_enabled(self, enabled):
        self.app_monitor_enabled = bool(enabled)
        self.save()

    def clear_custom_sound(self):
        self.custom_sound_path = ""
        self._preload_sound()
        self.save()
        self.show_bubble_quick("自定义音效已清除")

    def reload_expressions(self):
        self.expressions = scan_expressions()
        names = [e["name"] for e in self.expressions]
        if self.expression not in names and self.expressions:
            self.expression = self.expressions[0]["name"]
        self.apply_expression(self.expression, save=True, play_sound=False)
        self._log("已重新加载表情")

    def toggle_always_on_top(self):
        self.set_always_on_top(not self.always_on_top)

    def set_autostart(self, enabled):
        self.autostart = bool(enabled)
        ok = set_autostart(self.autostart)
        if ok:
            self.autostart = is_autostart_enabled()      # 以注册表真实结果为准
        else:
            self.show_bubble_quick("开机自启设置失败（注册表不可写）")
        self.save()
        self._log(f"开机自启：{'开启' if self.autostart else '关闭'}"
                  f"（注册表写入{'成功' if ok else '失败'}）")

    def _sync_autostart(self):
        """启动自愈：开启自启时确保注册表指向当前程序；路径失效则修正。"""
        real = is_autostart_enabled()
        cmd_ok = autostart_command_matches()
        if self.autostart and not cmd_ok:
            if set_autostart(True):
                self._log("开机自启已写入/修正为当前程序：" + get_autostart_command())
        self.autostart = is_autostart_enabled()
        if real and not cmd_ok:
            self._log("原开机自启指向旧路径，已更新")

    def _refresh_mirror(self):
        if self._base_pixmap is not None:
            self.label.setPixmap(self._mirror_pixmap(self._base_pixmap))

    def save(self):
        cfg = dict(self.cfg)
        cfg["size_level"] = self.size_level
        cfg["expression"] = self.expression
        cfg["click_text"] = self.click_text
        cfg["line_source"] = self.line_source
        cfg["fixed_line"] = self.fixed_line
        cfg["custom_lines"] = self.custom_lines
        cfg["random_enabled"] = self.random_enabled
        cfg["bubble_on"] = self.bubble_on
        cfg["bubble_close_sec"] = self.bubble_close_sec
        cfg["bubble_color"] = self.bubble_color
        cfg["show_time"] = self.show_time
        cfg["show_greeting"] = self.show_greeting
        cfg["bubble_font_size"] = self.bubble_font_size
        cfg["bubble_scale"] = self.bubble_scale
        cfg["bubble_freq"] = self.bubble_freq
        cfg["auto_emotion"] = self.auto_emotion
        cfg["auto_rotate"] = self.auto_rotate
        cfg["auto_rotate_interval"] = self.auto_rotate_interval
        cfg["click_rotate_count"] = self.click_rotate_count
        cfg["token_enabled"] = self.token_enabled
        cfg["token"] = self.token
        cfg["blink_enabled"] = self.blink_enabled
        cfg["blink_interval"] = self.blink_interval
        cfg["auto_mirror"] = self.auto_mirror
        cfg["follow_mode"] = self.follow_mode
        cfg["evade_mode"] = self.evade_mode
        cfg["wander_mode"] = self.wander_mode
        cfg["lock_position"] = self.lock_position
        cfg["always_on_top"] = self.always_on_top
        cfg["sound_enabled"] = self.sound_enabled
        cfg["sound_mode"] = self.sound_mode
        cfg["volume"] = self.volume
        cfg["custom_sound_path"] = self.custom_sound_path
        cfg["autostart"] = self.autostart
        cfg["hud_visible"] = self.hud_visible
        cfg["hud_abbrev"] = self.hud_abbrev
        cfg["panel_pinned"] = self.panel_pinned
        cfg["panel_pos"] = self.panel_pos
        cfg["panel_tab"] = self.panel_tab
        cfg["snap_enabled"] = self.snap_enabled
        cfg["app_monitor_enabled"] = self.app_monitor_enabled
        cfg["app_rules"] = self.app_rules
        cfg["x"] = self.x()
        cfg["y"] = self.y()
        save_config(cfg)
        self.cfg = cfg

    # ---------- 托盘 ----------
    def create_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = QIcon()
        for e in self.expressions:
            if e["path"].lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                icon = QIcon(e["path"])
                break
        if icon.isNull():
            icon = self.windowIcon()
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("DeepSeek Whale Desktop Pet")
        menu = QMenu()
        settings_act = menu.addAction("打开设置")
        settings_act.triggered.connect(lambda: self.open_settings())
        toggle_act = menu.addAction("显示/隐藏")
        toggle_act.triggered.connect(self.toggle_visible)
        menu.addSeparator()
        add_token_act = menu.addAction("Token +520W")
        add_token_act.triggered.connect(lambda: self.add_tokens(5200000))
        clear_token_act = menu.addAction("清空 Token")
        clear_token_act.triggered.connect(self.clear_tokens)
        hud_act = menu.addAction("显示/隐藏 Token HUD")
        hud_act.triggered.connect(self.toggle_hud)
        menu.addSeparator()
        top_act = menu.addAction("切换始终置顶")
        top_act.triggered.connect(self.toggle_always_on_top)
        reload_act = menu.addAction("重新加载表情")
        reload_act.triggered.connect(self.reload_expressions)
        menu.addSeparator()
        update_act = menu.addAction("检查更新")
        update_act.triggered.connect(self.check_update)
        log_act = menu.addAction("打开运行日志")
        log_act.triggered.connect(self.open_log)
        menu.addSeparator()
        about_act = menu.addAction("关于小鲸鱼")
        about_act.triggered.connect(self.show_about)
        qq_act = menu.addAction(f"加入 QQ 群（{QQ_GROUP}）")
        qq_act.triggered.connect(self.open_qq_group)
        drive_act = menu.addAction("美化磁盘图标（大肥鱼）")
        drive_act.triggered.connect(self.beautify_drive_icons)
        menu.addSeparator()
        quit_act = menu.addAction("退出")
        quit_act.triggered.connect(QApplication.quit)
        self.tray_menu = menu
        self.tray.setContextMenu(menu)
        self.tray.show()

    def show_about(self):
        QMessageBox.information(
            self, "关于小鲸鱼桌宠",
            f"DeepSeek 小鲸鱼桌宠  v{LOCAL_VERSION}\n\n"
            f"作者：DeepSeek-Whale-Desktop-Pet 团队\n"
            f"QQ 交流群：{QQ_GROUP}\n"
            f"开源仓库：{UPDATE_URL}\n\n"
            f"感谢开源：MeteorNOX / comreade-123 / JiafishNB")

    def open_qq_group(self):
        try:
            webbrowser.open(QQ_GROUP_URL)
            self.show_bubble_quick(f"QQ 群号：{QQ_GROUP}")
        except Exception:
            self.show_bubble_quick(f"QQ 群号：{QQ_GROUP}")

    def toggle_visible(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    rotate_log_if_needed()
    lock = QLockFile(os.path.join(os.path.expanduser("~"), ".dshw-pet.lock"))
    lock.setStaleLockTime(30000)
    if not lock.tryLock(100):
        QMessageBox.information(None, "小鲸鱼桌宠", "小鲸鱼桌宠已经运行了，请不要重复启动。")
        return
    pet = PetWindow()
    pet.show()
    pet.create_tray()
    app.aboutToQuit.connect(lambda: pet._log("小鲸鱼桌宠退出"))
    app.aboutToQuit.connect(lock.unlock)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
