#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek Whale Desktop Pet v4
完整对标原版/plus：原版气泡、自动情绪动画、台词系统、完整悬浮菜单。
"""

import copy
import ctypes
import glob
import inspect
import json
import math
import os
import random
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser

from PyQt5.QtCore import (
    Qt, QEvent, QTimer, QUrl, QSize, QRect, QRectF, QPointF, QObject,
    QPropertyAnimation, QEasingCurve, QLockFile, pyqtSignal, QVariantAnimation
)
from PyQt5.QtGui import (
    QPixmap, QMovie, QIcon, QColor, QPainter, QPen, QBrush,
    QPainterPath, QFont, QFontMetrics, QLinearGradient, QTransform, QCursor
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

LOCAL_VERSION = "4.4.1"
LOG_KEEP = 100
LOG_KEEP_DAYS = 7
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
    """启动时把上一次的日志归档；按天数与份数自动清理，日志不会一直堆积缓存。"""
    try:
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 0:
            stamp = time.strftime("%Y%m%d_%H%M%S")
            base, ext = os.path.splitext(LOG_PATH)
            os.replace(LOG_PATH, f"{base}_{stamp}{ext}")
        base, ext = os.path.splitext(LOG_PATH)
        logs = sorted(glob.glob(f"{base}_*{ext}"))
        cutoff = time.time() - LOG_KEEP_DAYS * 86400
        for old in list(logs):
            try:
                if os.path.getmtime(old) < cutoff:
                    os.remove(old)
                    logs.remove(old)
            except OSError:
                pass
        for old in logs[:-LOG_KEEP]:
            try:
                os.remove(old)
            except OSError:
                pass
    except OSError:
        pass


def install_excepthook():
    """把未捕获异常写进日志（打包成 exe 后看不到控制台，没有这个就无从排查）。"""
    def _hook(tp, val, tb):
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [未捕获异常] {tp.__name__}: {val}\n")
                traceback.print_exception(tp, val, tb, file=f)
        except Exception:
            pass
        try:
            sys.__excepthook__(tp, val, tb)
        except Exception:
            pass
    sys.excepthook = _hook


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
#       ⚠️ 概率 ≠ 冷却：概率是每次打开时的命中几率（这里填 100 就是每次都命中），
#          冷却在「设置 → 系统 → 应用打开监控 → 触发冷却」里调，默认 0 秒（每次都触发）。
#   · 是否启用：1 = 开启这条规则；0 = 暂时关闭（不用删掉）
#
# 注意：
#   · 以 # 开头的整行是注释，空白行忽略；
#   · 默认不需要冷却：每次切到该应用都会说；若嫌唠叨，把「触发冷却」调成 60~300 秒；
#   · 进程名取不到时（应用以管理员运行等）会自动改用**窗口标题**匹配；
#   · 改完保存本文件会自动重新加载（也可以点「重新加载规则」）。
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
def is_admin():
    """当前进程是否以管理员身份运行。"""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def set_file_attrs(path, hidden=True, system=True, readonly=None):
    """用 ctypes 直接设置文件属性（比 attrib 命令可靠，不依赖子进程）。

    每个参数都是「目标状态」：True=设上、False=去掉、None=不动。
    旧版只做 |= 不做 &=，于是传 False 时什么也没清掉 —— 而带隐藏+系统属性的文件
    在覆盖/删除时会「拒绝访问」，所以这里必须真的能清。"""
    try:
        HIDDEN, SYSTEM, READONLY = 0x02, 0x04, 0x01
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == -1:
            return False
        new = attrs
        for flag, want in ((HIDDEN, hidden), (SYSTEM, system), (READONLY, readonly)):
            if want is None:
                continue
            new = (new | flag) if want else (new & ~flag)
        if new == attrs:
            return True
        return bool(ctypes.windll.kernel32.SetFileAttributesW(str(path), new))
    except Exception:
        return False


def delete_files_elevated(paths):
    """用管理员权限删除这些文件（会弹一次 UAC）。返回 (是否已发起, 原因)。

    用于删除「当初以管理员身份写入、带 High 完整性标签」的文件：
    这种文件普通权限连删都不让删（WinError 5），只能借管理员权限来删。"""
    paths = [p for p in paths if p]
    if not paths:
        return False, ""
    try:
        quoted = " ".join(f'"{p}"' for p in paths)
        # SW_HIDE(0)：提权的 cmd 不显示黑框
        r = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", "cmd.exe", f"/c del /f /q {quoted}", None, 0)
        if int(r) <= 32:
            return False, f"提权请求被取消或失败（代码 {int(r)}）"
        return True, ""
    except Exception as e:
        return False, f"提权删除失败：{e}"


def lower_integrity_to_medium(path):
    """把文件的完整性标签降回「中等」。需要管理员权限，失败返回 False。

    管理员身份写入的文件会被系统自动标成 High（并带 No-Write-Up），
    之后普通权限的桌宠既改不了也删不掉；写入后立刻降回 Medium 就不会留后患。"""
    try:
        advapi32 = ctypes.windll.advapi32
        advapi32.ConvertStringSidToSidW.argtypes = [ctypes.c_wchar_p,
                                                    ctypes.POINTER(ctypes.c_void_p)]
        advapi32.ConvertStringSidToSidW.restype = ctypes.c_int
        advapi32.SetNamedSecurityInfoW.argtypes = [
            ctypes.c_wchar_p, ctypes.c_int, ctypes.c_uint, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        advapi32.SetNamedSecurityInfoW.restype = ctypes.c_int

        class SID_AND_ATTRIBUTES(ctypes.Structure):
            _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", ctypes.c_uint32)]

        class TOKEN_MANDATORY_LABEL(ctypes.Structure):
            _fields_ = [("Label", SID_AND_ATTRIBUTES)]

        sid = ctypes.c_void_p()
        if not advapi32.ConvertStringSidToSidW("S-1-16-8192", ctypes.byref(sid)):
            return False                       # S-1-16-8192 = 中等完整性
        try:
            label = TOKEN_MANDATORY_LABEL()
            label.Label.Sid = sid
            label.Label.Attributes = 0x20      # SE_GROUP_INTEGRITY
            # SE_FILE_OBJECT 传 1；LABEL_SECURITY_INFORMATION 传 0x00000004
            return advapi32.SetNamedSecurityInfoW(
                str(path), 1, 0x00000004, None, None, None, ctypes.byref(label)) == 0
        finally:
            ctypes.windll.kernel32.LocalFree(sid)
    except Exception:
        return False


def build_fish_ico(png_path, ico_path, size=256):
    """把 PNG 转成 ICO（单张 PNG 内嵌，Vista 及以上支持）。返回 (成功?, 原因)。"""
    import struct
    pix = QPixmap(png_path)
    if pix.isNull():
        return False, "素材读取失败"
    pix = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    tmp = os.path.join(os.environ.get("TEMP", "."), "dshw_fish_tmp.png")
    if not pix.save(tmp, "PNG"):
        return False, "临时图片写出失败"
    try:
        with open(tmp, "rb") as f:
            data = f.read()
    except OSError as e:
        return False, f"读取临时图片失败：{e}"
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
    except PermissionError as e:
        return False, f"无权限写入 {ico_path}（需要管理员）：{e}"
    except OSError as e:
        return False, f"写入 ICO 失败：{e}"
    return True, ""


def refresh_icon_cache():
    """刷新图标缓存：ie4uinit + SHChangeNotify（都不重启 explorer，不会黑屏）。

    注意（实测结论）：盘符图标是缓存在**登录会话**里的，上面这些通知刷不动它，
    只有注销/重启才会重新读取 —— 所以美化/恢复后必须如实告诉用户这一点。"""
    ok = False
    try:
        subprocess.Popen(["ie4uinit.exe", "-show"],
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        ok = True
    except Exception:
        pass
    try:
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)   # SHCNE_ASSOCCHANGED
        ok = True
    except Exception:
        pass
    return ok


DRIVE_ICON_BAK = os.path.join(os.path.expanduser("~"), ".dshw-drive-icon.ico")


def drive_letter_of(path):
    """从 "D:\\" 这样的盘根取出盘符（返回 "D"）；不是单纯盘根则返回 ""。"""
    text = str(path or "").strip().rstrip("\\/")
    if len(text) == 2 and text[1] == ":" and text[0].isalpha():
        return text[0].upper()
    return ""


def set_drive_icon_registry(letter, ico_path):
    """把盘符图标写进当前用户注册表（HKCU，不需要管理员权限）。

    这是 Windows 另一个盘符图标入口，好处是图标文件放在用户目录里，
    即使磁盘根的图标文件被删掉，也不会像 C 盘那次一样变成「白纸」坏图标。"""
    try:
        if winreg is None or not letter:
            return False
        key_path = (r"Software\Microsoft\Windows\CurrentVersion\Explorer"
                    rf"\DriveIcons\{letter}\DefaultIcon")
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0,
                                winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"{ico_path},0")
        return True
    except Exception:
        return False


def clear_drive_icon_registry(letter):
    """删掉上面写的盘符图标设置；返回是否真的删掉了。"""
    try:
        if winreg is None or not letter:
            return False
        base = r"Software\Microsoft\Windows\CurrentVersion\Explorer\DriveIcons"
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"{base}\{letter}\DefaultIcon")
        except FileNotFoundError:
            return False
        for key in (rf"{base}\{letter}", base):
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)   # 顺手收掉空壳父键
            except OSError:
                pass
        return True
    except Exception:
        return False


def apply_drive_icon(drive, ico_src, set_root_system=False):
    """设置磁盘图标。返回 (成功?, 原因)。

    写入 desktop.ini（主）+ autorun.inf/icon.ico（兼容），全程只给文件设属性。
    注意：Windows 11 的**驱动器根目录**常常还要求盘根带「系统 + 只读」属性才显示自定义图标，
    这一步需要管理员权限，因此由 set_root_system 控制（管理员模式下自动开启）。
    重复应用时目标文件已带隐藏属性，会挡住覆盖，所以写入前先清属性。
    另外会顺手写一份当前用户的注册表盘符图标（HKCU，不需要管理员）作为补充。
    实测结论：图标是否**立刻**变化取决于登录会话缓存 —— 不生效时注销/重启一次即可。"""
    import shutil
    root = drive.rstrip("\\") + "\\"
    ico = os.path.join(root, "icon.ico")
    inf = os.path.join(root, "autorun.inf")
    ini = os.path.join(root, "desktop.ini")
    for path in (ico, inf, ini):
        if os.path.exists(path):
            set_file_attrs(path, hidden=False, system=False)

    # 1) icon.ico
    try:
        shutil.copyfile(ico_src, ico)
    except PermissionError:
        try:
            os.remove(ico)
            shutil.copyfile(ico_src, ico)
        except OSError:
            return False, f"无法写入 {ico}（被占用或被安全软件拦截）"
    except OSError as e:
        return False, f"写入 icon.ico 失败：{e}"

    # 2) desktop.ini：用**相对路径**（驱动器根目录更可靠），UTF-16 编码
    ini_text = ("[.ShellClassInfo]\r\n"
                "IconResource=icon.ico,0\r\n"
                "IconFile=icon.ico\r\n"
                "IconIndex=0\r\n"
                "ConfirmFileOp=0\r\n")
    try:
        with open(ini, "wb") as f:
            f.write(ini_text.encode("utf-16"))
    except PermissionError:
        try:
            os.remove(ini)
            with open(ini, "wb") as f:
                f.write(ini_text.encode("utf-16"))
        except OSError:
            return False, f"无法写入 {ini}（被占用或被安全软件拦截）"
    except OSError as e:
        return False, f"写入 desktop.ini 失败：{e}"

    # 3) autorun.inf（兼容补充）
    try:
        with open(inf, "wb") as f:
            f.write(b"[autorun]\r\nICON = icon.ico,0\r\n")
    except OSError:
        pass

    set_file_attrs(ico, hidden=True, system=False)
    set_file_attrs(inf, hidden=True, system=False)
    ok_ini = set_file_attrs(ini, hidden=True, system=True)
    if not ok_ini:
        return False, "desktop.ini 已写入但属性设置失败（图标可能不刷新）"
    if set_root_system:
        # 部分 Win11 电脑要求盘根带「系统」+「只读」属性才显示自定义图标（需管理员）。
        # hidden 传 None：不动盘根原有的隐藏属性。
        if not set_file_attrs(root, hidden=None, system=True, readonly=True):
            return False, "已写入，但设置磁盘根目录属性失败（需要管理员权限）"
    letter = drive_letter_of(root)
    if letter:
        # 额外挂一份注册表图标（HKCU，不需要管理员）：图标文件放用户目录，
        # 磁盘根的图标文件就算被删掉，也不会留下「白纸」坏图标
        try:
            shutil.copyfile(ico_src, DRIVE_ICON_BAK)
            set_drive_icon_registry(letter, DRIVE_ICON_BAK)
        except OSError:
            pass
    if is_admin():
        # 管理员身份写入的文件会被标成 High 完整性（No-Write-Up），
        # 之后普通权限的桌宠连删都删不掉（点「恢复默认图标」会报拒绝访问）。
        # 这里立刻降回「中等」，保证以后能正常恢复。
        for path in (ico, inf, ini):
            lower_integrity_to_medium(path)
    refresh_icon_cache()
    return True, ""


def remove_drive_icon(drive):
    """恢复默认磁盘图标：删除我们放过的文件（含旧版遗留）。

    两个坑：
      1) 文件带隐藏+系统属性时，删之前必须真的把属性清掉，否则「拒绝访问」；
      2) 之前以「管理员身份」写入过的文件带 High 完整性标签（No-Write-Up），
         普通权限的桌宠连删都删不了（WinError 5）→ 自动改用管理员权限删除（弹一次 UAC）。"""
    root = drive.rstrip("\\") + "\\"
    removed, denied, busy = [], [], []
    for name in ("desktop.ini", "autorun.inf", "icon.ico", "dshw_fish.ico"):
        p = os.path.join(root, name)
        if not os.path.exists(p):
            continue
        set_file_attrs(p, hidden=False, system=False, readonly=False)
        try:
            os.remove(p)
            removed.append(name)
        except PermissionError:
            denied.append(p)
        except OSError as e:
            if getattr(e, "winerror", None) == 32:      # 文件被占用
                busy.append(name)
            else:
                denied.append(p)

    if clear_drive_icon_registry(drive_letter_of(root)):
        removed.append("注册表图标项")

    note = ""
    if denied and not is_admin():
        started, why = delete_files_elevated(denied)
        if started:
            for _ in range(25):                 # 最多等 2.5 秒，等提权进程删完
                if not any(os.path.exists(p) for p in denied):
                    break
                time.sleep(0.1)
            still = [p for p in denied if os.path.exists(p)]
            removed += [os.path.basename(p) for p in denied if p not in still]
            denied = still                      # 只有"仍然存在"的才算真失败
            note = ("需要管理员权限的文件已通过 UAC 删除" if not still else
                    "已请求管理员权限删除（UAC 弹窗点「是」），但这些文件仍在："
                    + "、".join(os.path.basename(p) for p in still))
        else:
            names = "、".join(os.path.basename(p) for p in denied)
            note = (f"{names} 需要管理员权限才能删除（{why}）——"
                    "也可以先以管理员身份运行桌宠，再点「恢复默认图标」")
    elif denied:
        note = ("已是管理员仍删不掉：" + "、".join(os.path.basename(p) for p in denied)
                + "（可能被安全软件占用）")

    refresh_icon_cache()
    if busy:
        note = (note + "；" if note else "") + \
            "、".join(busy) + " 正被占用（关掉相关资源管理器窗口后重试）"
    if removed:
        msg = "已删除：" + "、".join(removed) + "（图标缓存已刷新）"
        return (not denied), (msg if not note else f"{msg}；{note}")
    if note:
        return False, note
    return True, "该磁盘没有需要删除的图标文件"


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


class NoWheelSlider(QSlider):
    """不响应鼠标滚轮的滑块：避免在面板上滚动时误改设置值。"""

    def wheelEvent(self, event):
        event.ignore()


class NoWheelComboBox(QComboBox):
    """不响应鼠标滚轮的下拉框：避免滚动时误切换选项（表情/音效/颜色等）。"""

    def wheelEvent(self, event):
        event.ignore()


class WheelBlocker(QObject):
    """吃掉滚轮事件：用于标签栏等本不该被滚轮改变状态的控件。"""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            return True
        return super().eventFilter(obj, event)


def clamp_to_screen(x, y, w, h, margin=4):
    """把矩形限制在屏幕可用区域内，避免气泡/窗口被屏幕边缘截断。"""
    screen = QApplication.primaryScreen()
    if not screen:
        return max(0, int(x)), max(0, int(y))
    geo = screen.availableGeometry()
    x = max(geo.left() + margin, min(int(x), geo.right() - w - margin))
    y = max(geo.top() + margin, min(int(y), geo.bottom() - h - margin))
    return int(x), int(y)


class BubbleWidget(QWidget):
    """原版风格气泡：独立顶层窗口、圆角、尾巴、动态尺寸，不遮挡桌宠。"""

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.lines = []
        self.color_key = "blue"
        self.tail_up = False          # True = 气泡在角色下方（思考泡泡的圆点朝上）
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self.font_size = 13
        self.scale = 1.0
        self._timer.timeout.connect(self.hide)
        # 注意：不要用 QGraphicsDropShadowEffect —— 在透明分层窗口上会导致
        # UpdateLayeredWindowIndirect 失败（气泡显示残缺/残留旧画面）。
        # 柔和阴影改为在 paintEvent 里自绘。

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

        w = max(230, min(420, int(max_w * 1.5) + 36))
        h = max(120, int(total_h * 1.5) + 78)
        self.setFixedSize(w, h)

        if pet is not None:
            w = self.width()
            h = self.height()
            geo = QApplication.primaryScreen().availableGeometry()
            x = pet.x() + (pet.width() - w) // 2
            y = pet.y() - h - 8
            self.tail_up = False
            if y < geo.top():
                # 上方空间不足（角色贴顶）→ 放到角色下方，尖头朝上指向角色
                below = pet.y() + pet.height() + 8
                if below + h <= geo.bottom():
                    y = below
                    self.tail_up = True
            x, y = clamp_to_screen(x, y, w, h)      # 左右上下都不越出屏幕
            self.move(x, y)

        self.update()
        self.show()
        self.raise_()
        self._timer.start(duration)

    def _text_rect(self):
        """文字区：椭圆内居中的可读区域（避开圆点区）。"""
        if self.tail_up:
            return QRect(26, 52, self.width() - 52, self.height() - 74)
        return QRect(26, 18, self.width() - 52, self.height() - 74)

    def paintEvent(self, event):
        """思考泡泡样式（与参考项目一致）：椭圆主体 + 小尾巴 + 两个递减圆点；
        圆点方向跟着气泡位置走（在角色上方时朝下、在下方时朝上）。"""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        c = BUBBLE_COLORS.get(self.color_key, BUBBLE_COLORS["blue"])
        border = QColor(c["border"])
        bg = QColor(*c["bg"])
        w, h = self.width(), self.height()
        tail_zone = 46                      # 尾巴 + 圆点所占高度

        p.save()
        if self.tail_up:                    # 垂直镜像：圆点跑到上方，指向角色
            p.translate(0, h)
            p.scale(1, -1)
        body = QRectF(5, 5, w - 10, h - tail_zone)
        cx = body.center().x()
        # 自绘柔和阴影（外层更大更淡 → 内层更浓），避免使用 graphics effect
        for grow, alpha in ((9, 10), (6, 16), (3, 22)):
            sp = QPainterPath()
            sp.addEllipse(body.adjusted(-grow, -grow + 2, grow, grow + 2))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, alpha))
            p.drawPath(sp)
        # 椭圆与小尖尾巴合并成一个轮廓，描边只走外圈（避免出现"V"形内线）
        body_path = QPainterPath()
        body_path.addEllipse(body)
        tail_path = QPainterPath()
        tail_path.moveTo(cx - 8, body.bottom() - 12)
        tail_path.lineTo(cx - 1, body.bottom() + 12)
        tail_path.lineTo(cx + 8, body.bottom() - 12)
        tail_path.closeSubpath()
        p.setPen(QPen(border, 3))
        p.setBrush(QBrush(bg))
        p.drawPath(body_path.united(tail_path))
        # 两个递减小圆点（思考泡泡特征）
        for dx, dy, r in ((-6, 22, 7), (0, 35, 4)):
            p.setPen(QPen(border, 3))
            p.setBrush(QBrush(bg))
            p.drawEllipse(QPointF(cx + dx, body.bottom() + dy), r, r)
        p.restore()

        p.setPen(QColor(c["text"]))
        p.setFont(QFont("Microsoft YaHei", self.font_size))
        content = self._text_rect()
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
        self.data = {}
        self.font_px = 16
        self.theme = "blue"
        self.tint = "idle"
        self.abbrev = True

    def apply_theme(self, key):
        self.theme = key if key in self.THEMES else "blue"
        self.update()

    def set_content(self, data, font_px, tint="idle", abbrev=True):
        """data: {"token": 数字或None, "time": "HH:MM:SS", "date": "2026-09-11 周五"}"""
        self.data = dict(data or {})
        self.font_px = max(12, min(26, int(font_px)))
        self.tint = tint if tint in ("idle", "gain", "cost") else "idle"
        self.abbrev = bool(abbrev)
        self.update()

    def _font(self):
        f = QFont("Microsoft YaHei UI")
        f.setPixelSize(self.font_px)
        f.setBold(True)
        return f

    def _rows(self):
        """返回 [[(文本,颜色), ...], ...]：Token 一行、日期时间一行（竖排更好看）。"""
        rows = []
        token = self.data.get("token")
        if token is not None:
            if self.abbrev:
                num, unit = fmt_token(int(token))
            else:
                num, unit = f"{int(token):,}", ""
            color = {"idle": self.NUM_IDLE, "gain": self.NUM_GAIN, "cost": self.NUM_COST}[self.tint]
            row = [("Token：", self.PREFIX), (num, color)]
            if unit:
                row.append((unit, self.PREFIX))
            rows.append(row)
        date = str(self.data.get("date") or "")
        tm = str(self.data.get("time") or "")
        if date or tm:
            tcolor = self.THEMES.get(self.theme, self.THEMES["blue"])["time"]
            row = []
            if date:
                row.append((date, tcolor))
            if tm:
                row.append((("　" + tm) if date else tm, tcolor))
            rows.append(row)
        return rows

    def row_count(self):
        return len(self._rows())

    def _parts(self):
        """兼容旧接口：首行分段（测试与宽度估算用）。"""
        rows = self._rows()
        return rows[0] if rows else []

    def desired_width(self):
        f = self._font()
        fm = QFontMetrics(f)
        widest = max((sum(fm.horizontalAdvance(t) for t, _ in row)
                      for row in self._rows()), default=0)
        return widest + 42

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

        # 分行居中绘制：Token 一行、日期时间一行
        rows = self._rows()
        if not rows:
            return
        f = self._font()
        p.setFont(f)
        fm = QFontMetrics(f)
        line_h = fm.height()
        gap = 4
        total_h = len(rows) * line_h + (len(rows) - 1) * gap
        y = r.top() + (r.height() - total_h) / 2.0
        for row in rows:
            total_w = sum(fm.horizontalAdvance(t) for t, _ in row)
            x = r.center().x() - total_w / 2.0
            baseline = y + fm.ascent()
            for text, color in row:
                p.setPen(color)
                p.drawText(QPointF(x, baseline), text)
                x += fm.horizontalAdvance(text)
            y += line_h + gap


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

    def paintEvent(self, event):
        """标题栏底部的细渐变色带（青 → 紫），提升设计感。"""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.00, QColor(34, 211, 238, 0))
        grad.setColorAt(0.25, QColor(34, 211, 238, 120))
        grad.setColorAt(0.62, QColor(124, 58, 237, 120))
        grad.setColorAt(1.00, QColor(124, 58, 237, 0))
        band = QPainterPath()
        band.addRoundedRect(QRectF(18, self.height() - 7, max(10, self.width() - 36), 3), 1.5, 1.5)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(grad))
        p.drawPath(band)


class Card(QFrame):
    """设置面板分区卡片：标题 + 说明 + 可选「?」提示 + 内容区。"""

    def __init__(self, title, desc="", tip="", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 11)
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
        self.body.setSpacing(7)
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
            QFrame#card:hover { background: rgba(255,255,255,0.085);
                border: 1px solid rgba(148,163,184,0.38); }
            QLabel#cardTitle { font-size: 16px; font-weight: 800; color: #67e8f9; }
            QLabel#cardDesc { font-size: 13px; color: #94a3b8; }
            QLabel#cardTip { background: rgba(148,163,184,0.30); border-radius: 10px;
                color: #e2e8f0; font-size: 13px; font-weight: 800; }
            QLabel#tokenLabel { color: #fbbf24; font-size: 16px; font-weight: 700; }
            QComboBox, QLineEdit {
                background: rgba(255,255,255,0.10); border: 1.5px solid rgba(255,255,255,0.22);
                border-radius: 10px; padding: 7px 11px; color: white; font-size: 16px; font-weight: 600;
            }
            QComboBox QAbstractItemView { background: #0f172a; color: white; selection-background-color: #2563eb;
                font-size: 15px; padding: 6px; border-radius: 10px; }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #7c3aed);
                border: none; border-radius: 10px; padding: 8px 12px; color: white;
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
        p1.setSpacing(8)

        self.expr_combo = NoWheelComboBox()
        for e in pet.expressions:
            self.expr_combo.addItem(e["display"], e["name"])
        idx = self.expr_combo.findData(pet.expression)
        if idx >= 0:
            self.expr_combo.setCurrentIndex(idx)
        self.expr_combo.currentIndexChanged.connect(self._ok(self._on_expr))

        self.click_rotate_slider = NoWheelSlider(Qt.Horizontal)
        self.click_rotate_slider.setRange(1, 100)
        self.click_rotate_slider.setValue(pet.click_rotate_count)
        self.click_rotate_value = QLabel(f"{pet.click_rotate_count} 下")
        self.click_rotate_slider.valueChanged.connect(self._ok(self._on_click_rotate))

        self.size_slider = NoWheelSlider(Qt.Horizontal)
        self.size_slider.setRange(SIZE_MIN, SIZE_MAX)
        self.size_slider.setValue(pet.size_level)
        self.size_value = QLabel(str(pet.size_level))
        self.size_slider.valueChanged.connect(self._ok(self._on_size))
        self.size_slider.sliderPressed.connect(pet.begin_panel_lock)
        self.size_slider.sliderReleased.connect(self._ok(self._on_size_done))

        card_look = Card("🎨 外观", "表情、连点换表情次数与角色大小",
                         tip="连点换表情：连续点击这么多次后换下一个表情（1~100）\n"
                             "大小：档位 1~20，对应 0.6~2.5 倍")
        card_look.add(self.expr_combo)
        card_look.add(QLabel("连点换表情"))
        card_look.add_layout(self._row(self.click_rotate_slider, self.click_rotate_value))
        card_look.add(QLabel("大小"))
        card_look.add_layout(self._row(self.size_slider, self.size_value))
        p1.addWidget(card_look)

        self.vol_slider = NoWheelSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(pet.volume)
        self.vol_value = QLabel(f"{pet.volume}%")
        self.vol_slider.valueChanged.connect(self._ok(self._on_vol))

        self.sound_combo = NoWheelComboBox()
        self.sound_combo.addItem("小黄鸭", "duck")
        self.sound_combo.addItem("音效1", "fx1")
        for mode in pet.sounds:
            if mode not in ("duck", "fx1"):
                self.sound_combo.addItem(mode, mode)
        idx = self.sound_combo.findData(pet.sound_mode)
        if idx >= 0:
            self.sound_combo.setCurrentIndex(idx)
        self.sound_combo.currentIndexChanged.connect(self._ok(self._on_sound_mode))
        self.sound_check = QCheckBox("启用音效")
        self.sound_check.setChecked(pet.sound_enabled)
        self.sound_check.toggled.connect(self._ok(self._on_sound))

        card_sound = Card("🔊 声音", "音效开关、音效选择与音量",
                          tip="音效文件放在程序 sounds 目录里即可出现在列表中")
        card_sound.add(self.sound_combo)
        card_sound.add(self.sound_check)
        card_sound.add(QLabel("音量"))
        card_sound.add_layout(self._row(self.vol_slider, self.vol_value))
        p1.addWidget(card_sound)

        self.follow_check = QCheckBox("鼠标跟随")
        self.follow_check.setChecked(pet.follow_mode)
        self.follow_check.toggled.connect(self._ok(self._on_follow_mode))
        self.evade_check = QCheckBox("躲避鼠标")
        self.evade_check.setChecked(pet.evade_mode)
        self.evade_check.toggled.connect(self._ok(self._on_evade_mode))
        self.wander_check = QCheckBox("待机漫游")
        self.wander_check.setChecked(pet.wander_mode)
        self.wander_check.toggled.connect(self._ok(self._on_wander_mode))

        card_act = Card("🕹️ 行为", "怎么动由你决定",
                        tip="跟随与躲避互斥（同时只会生效一个）；\n"
                            "待机漫游可以和躲避共存：设置「漫游启动延迟」秒内没有互动，\n"
                            "她自己开始散步（0 秒 = 不自动漫游）；\n"
                            "「躲避触发距离」= 鼠标离多近开始逃跑")
        card_act.add_checks([self.follow_check, self.evade_check, self.wander_check])
        card_act.add(QLabel("漫游启动延迟"))
        self.wander_delay_slider = NoWheelSlider(Qt.Horizontal)
        self.wander_delay_slider.setRange(0, 600)
        self.wander_delay_slider.setValue(pet.wander_delay)
        self.wander_delay_value = QLabel("不自动漫游" if pet.wander_delay == 0
                                        else f"{pet.wander_delay} 秒")
        self.wander_delay_slider.valueChanged.connect(self._ok(self._on_wander_delay))
        card_act.add_layout(self._row(self.wander_delay_slider, self.wander_delay_value))
        card_act.add(QLabel("躲避触发距离"))
        self.evade_range_slider = NoWheelSlider(Qt.Horizontal)
        self.evade_range_slider.setRange(100, 1500)
        self.evade_range_slider.setValue(pet.evade_range)
        self.evade_range_value = QLabel(f"{pet.evade_range}px")
        self.evade_range_slider.valueChanged.connect(self._ok(self._on_evade_range))
        card_act.add_layout(self._row(self.evade_range_slider, self.evade_range_value))
        p1.addWidget(card_act)

        self.mirror_check = QCheckBox("贴边自动镜像")
        self.mirror_check.setChecked(pet.auto_mirror)
        self.mirror_check.toggled.connect(self._ok(self._on_mirror))
        self.lock_check = QCheckBox("固定位置")
        self.lock_check.setToolTip("防止误拖动")
        self.lock_check.setChecked(pet.lock_position)
        self.lock_check.toggled.connect(self._ok(self._on_lock))
        self.top_check = QCheckBox("始终置顶")
        self.top_check.setChecked(pet.always_on_top)
        self.top_check.toggled.connect(self._ok(self._on_top))
        self.snap_check = QCheckBox("拖拽吸附边缘")
        self.snap_check.setToolTip("松手时角色中心在屏幕某侧 1/4 区域内即贴边")
        self.snap_check.setChecked(pet.snap_enabled)
        self.snap_check.toggled.connect(self._ok(self._on_snap))

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
        p2.setSpacing(8)
        self.token_check = QCheckBox("开启 Token 系统")
        self.token_check.setChecked(pet.token_enabled)
        self.token_check.toggled.connect(self._ok(self._on_token_enabled))
        self.hud_check = QCheckBox("显示 HUD")
        self.hud_check.setToolTip("在角色下方显示 Token / 时间卡片")
        self.hud_check.setChecked(pet.hud_visible)
        self.hud_check.toggled.connect(self._ok(self._on_hud_visible))
        self.hud_abbrev_check = QCheckBox("数字缩写")
        self.hud_abbrev_check.setToolTip("大数字缩写显示，例如 388.4W")
        self.hud_abbrev_check.setChecked(pet.hud_abbrev)
        self.hud_abbrev_check.toggled.connect(self._ok(self._on_hud_abbrev))
        self.hud_token_check = QCheckBox("显示 Token")
        self.hud_token_check.setChecked(pet.hud_show_token)
        self.hud_token_check.toggled.connect(self._ok(self._on_hud_show_token))
        self.hud_time_check = QCheckBox("显示时间")
        self.hud_time_check.setChecked(pet.hud_show_time)
        self.hud_time_check.toggled.connect(self._ok(self._on_hud_show_time))
        self.hud_date_check = QCheckBox("显示日期星期")
        self.hud_date_check.setChecked(pet.hud_show_date)
        self.hud_date_check.toggled.connect(self._ok(self._on_hud_show_date))
        self.token_label = QLabel(f"当前 Token：{pet.token:,}")
        self.token_label.setObjectName("tokenLabel")
        token_row = QHBoxLayout()
        add_btn = QPushButton("+520W Token")
        add_btn.clicked.connect(self._ok(self._on_add_tokens))
        clear_btn = QPushButton("清空 Token")
        clear_btn.setObjectName("danger")
        clear_btn.clicked.connect(self._ok(self._on_clear_tokens))
        token_row.addWidget(add_btn)
        token_row.addWidget(clear_btn)

        card_token = Card("💰 趣味 Token", "点击/喂食消耗，可随时充值或清空",
                          tip="关闭 Token 系统后不影响互动与喂食，只是不再计数；\n"
                              "拖文件到桌宠身上也能喂食（会真实删除文件）")
        card_token.add(self.token_check)
        card_token.add(self.token_label)
        card_token.add_layout(token_row)
        p2.addWidget(card_token)

        card_hud = Card("🧾 HUD 显示", "桌宠下方的 Token / 时间显示（可分别开关）",
                        tip="Token 与时间互不绑定：只想要时间就把「显示 Token」关掉；\n"
                            "时间可单独显示日期与星期；字号随角色大小自动放大（15~24px）\n"
                            "数字缩写示例：388.4W")
        card_hud.add_checks([self.hud_check, self.hud_abbrev_check,
                             self.hud_token_check, self.hud_time_check, self.hud_date_check])
        p2.addWidget(card_hud)
        p2.addStretch()

        # ============ 气泡页 ============
        page_bubble = QWidget()
        p3 = QVBoxLayout(page_bubble)
        p3.setSpacing(8)
        self.line_mode = NoWheelComboBox()
        self.line_mode.addItem("今日心情", "mood")
        self.line_mode.addItem("随机台词", "random")
        self.line_mode.addItem("自定义台词", "custom")
        self.line_mode.addItem("固定台词", "fixed")
        idx = self.line_mode.findData(pet.line_source)
        if idx >= 0:
            self.line_mode.setCurrentIndex(idx)
        self.line_mode.currentIndexChanged.connect(self._ok(self._on_line_source))
        p3.addWidget(self.line_mode)

        self.custom_line_edit = QLineEdit(pet.fixed_line)
        self.custom_line_edit.setPlaceholderText("输入一句台词")
        self.custom_line_edit.textChanged.connect(self._ok(self._on_fixed_line))
        p3.addWidget(self.custom_line_edit)
        self.custom_empty = QLabel("⚠️ 自定义台词库为空，请先添加")
        self.custom_empty.setStyleSheet("color:#fca5a5; font-size:14px; font-weight:700;")
        self.custom_list = QListWidget()
        self.custom_list.setMaximumHeight(104)
        self.custom_list.setWordWrap(True)
        self.custom_list.setSpacing(2)
        self.custom_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.custom_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.custom_list.setStyleSheet(LIST_QSS)
        add_btn = QPushButton("添加为自定义台词")
        add_btn.clicked.connect(self._ok(self._on_add_custom))
        delete_btn = QPushButton("删除选中台词")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self._ok(self._on_delete_custom))
        lines_btn = QPushButton("编辑台词文件（每行一句，txt）")
        lines_btn.clicked.connect(self._ok(self._on_open_lines))

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
        self.bubble_check.toggled.connect(self._ok(self._on_bubble))
        self.auto_close_slider = NoWheelSlider(Qt.Horizontal)
        self.auto_close_slider.setRange(1, 10)
        self.auto_close_slider.setValue(max(1, pet.bubble_close_sec))
        self.auto_close_value = QLabel(f"{pet.bubble_close_sec}秒")
        self.auto_close_slider.valueChanged.connect(self._ok(self._on_bubble_close))
        self.color_combo = NoWheelComboBox()
        self.color_combo.addItem("蓝色", "blue")
        self.color_combo.addItem("粉色", "pink")
        self.color_combo.addItem("深色", "dark")
        self.color_combo.addItem("绿色", "green")
        idx = self.color_combo.findData(pet.bubble_color)
        if idx >= 0:
            self.color_combo.setCurrentIndex(idx)
        self.color_combo.currentIndexChanged.connect(self._ok(self._on_bubble_color))
        self.show_time_check = QCheckBox("显示当前时间")
        self.show_time_check.setChecked(pet.show_time)
        self.show_time_check.toggled.connect(self._ok(self._on_show_time))
        self.show_greeting_check = QCheckBox("时间问候")
        self.show_greeting_check.setChecked(pet.show_greeting)
        self.show_greeting_check.toggled.connect(self._ok(self._on_show_greeting))

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

        self.bubble_font_slider = NoWheelSlider(Qt.Horizontal)
        self.bubble_font_slider.setRange(10, 24)
        self.bubble_font_slider.setValue(pet.bubble_font_size)
        self.bubble_font_value = QLabel(f"{pet.bubble_font_size}px")
        self.bubble_font_slider.valueChanged.connect(self._ok(self._on_bubble_font))
        self.bubble_scale_slider = NoWheelSlider(Qt.Horizontal)
        self.bubble_scale_slider.setRange(70, 140)
        self.bubble_scale_slider.setValue(int(pet.bubble_scale * 100))
        self.bubble_scale_value = QLabel(f"{int(pet.bubble_scale * 100)}%")
        self.bubble_scale_slider.valueChanged.connect(self._ok(self._on_bubble_scale))
        self.bubble_freq_slider = NoWheelSlider(Qt.Horizontal)
        self.bubble_freq_slider.setRange(1, 100)
        self.bubble_freq_slider.setValue(pet.bubble_freq)
        self.bubble_freq_value = QLabel(f"{pet.bubble_freq}%")
        self.bubble_freq_slider.valueChanged.connect(self._ok(self._on_bubble_freq))

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
        p4.setSpacing(8)
        self.auto_rotate_check = QCheckBox("自动轮换表情")
        self.auto_rotate_check.setChecked(pet.auto_rotate)
        self.auto_rotate_check.toggled.connect(self._ok(self._on_auto_rotate_setting))
        self.auto_rotate_interval_slider = NoWheelSlider(Qt.Horizontal)
        self.auto_rotate_interval_slider.setRange(5, 100)
        self.auto_rotate_interval_slider.setValue(pet.auto_rotate_interval)
        self.auto_rotate_interval_value = QLabel(f"{pet.auto_rotate_interval} 秒")
        self.auto_rotate_interval_slider.valueChanged.connect(self._ok(self._on_auto_rotate_interval))
        self.idle_anim_check = QCheckBox("空闲自动表情动画")
        self.idle_anim_check.setChecked(pet.auto_emotion)
        self.idle_anim_check.toggled.connect(self._ok(self._on_auto_emotion))
        self.blink_check = QCheckBox("空闲自动眨眼")
        self.blink_check.setChecked(pet.blink_enabled)
        self.blink_check.toggled.connect(self._ok(self._on_blink))
        self.blink_slider = NoWheelSlider(Qt.Horizontal)
        self.blink_slider.setRange(5, 120)
        self.blink_slider.setValue(pet.blink_interval)
        self.blink_value = QLabel(f"{pet.blink_interval}秒")
        self.blink_slider.valueChanged.connect(self._ok(self._on_blink_interval))

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
        self.monitor_check.toggled.connect(self._ok(self._on_app_monitor))
        self.rule_match_edit = QLineEdit()
        self.rule_match_edit.setPlaceholderText("匹配词：进程名/窗口标题，如 steam")
        self.rule_text_edit = QLineEdit()
        self.rule_text_edit.setPlaceholderText("触发台词，如：又在打游戏啦？")
        rule_btn_row = QHBoxLayout()
        add_rule_btn = QPushButton("添加规则")
        add_rule_btn.clicked.connect(self._ok(self._on_add_rule))
        toggle_rule_btn = QPushButton("启用/停用")
        toggle_rule_btn.clicked.connect(self._ok(self._on_toggle_rule))
        del_rule_btn = QPushButton("删除选中规则")
        del_rule_btn.setObjectName("danger")
        del_rule_btn.clicked.connect(self._ok(self._on_delete_rule))
        rule_btn_row.addWidget(add_rule_btn)
        rule_btn_row.addWidget(toggle_rule_btn)
        rule_btn_row.addWidget(del_rule_btn)
        self.rule_list = QListWidget()
        self.rule_list.setMaximumHeight(88)
        self.rule_list.setWordWrap(True)
        self.rule_list.setSpacing(2)
        self.rule_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rule_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.rule_list.setStyleSheet(LIST_QSS)
        self.rule_list.itemDoubleClicked.connect(lambda item: self._on_toggle_rule())

        card_monitor = Card("🖥️ 应用打开监控", "打开指定软件时让她说一句",
                            tip="每行规则格式：匹配词 | 台词 | 触发概率 | 启用\n"
                                "触发概率 0~100（如 30 表示 30% 几率），与冷却无关\n"
                                "触发冷却 0 秒 = 每次打开都触发；嫌唠叨可调 60~300 秒\n"
                                "进程名取不到时会自动改用窗口标题匹配\n"
                                "也可以直接编辑 .dshw-pet-rules.txt（文件内有详细说明，改完自动生效）")
        card_monitor.add(self.monitor_check)
        card_monitor.add(self.rule_match_edit)
        card_monitor.add(self.rule_text_edit)
        card_monitor.add_layout(rule_btn_row)
        card_monitor.add(self.rule_list)
        card_monitor.add(QLabel("触发冷却"))
        self.cooldown_slider = NoWheelSlider(Qt.Horizontal)
        self.cooldown_slider.setRange(0, 600)
        self.cooldown_slider.setValue(pet.app_rule_cooldown)
        self.cooldown_value = QLabel("每次打开都触发" if pet.app_rule_cooldown == 0
                                     else f"{pet.app_rule_cooldown} 秒")
        self.cooldown_slider.valueChanged.connect(self._ok(self._on_app_rule_cooldown))
        card_monitor.add_layout(self._row(self.cooldown_slider, self.cooldown_value))
        card_monitor.add_row(self._plain_btn("编辑规则文件", self._on_open_rules),
                             self._plain_btn("重新加载规则", self._on_reload_external))
        p4.addWidget(card_monitor)
        self._refresh_rules()

        self.autostart_check = QCheckBox("开机自启")
        self.autostart_check.setChecked(is_autostart_enabled())
        self.autostart_check.toggled.connect(self._ok(self._on_autostart))
        self.fullscreen_hide_check = QCheckBox("全屏时自动隐藏")
        self.fullscreen_hide_check.setToolTip("玩全屏游戏或看全屏视频时临时隐藏桌宠，退出全屏后自动恢复")
        self.fullscreen_hide_check.setChecked(pet.hide_in_fullscreen)
        self.fullscreen_hide_check.toggled.connect(self._ok(self._on_fullscreen_hide))
        self.auto_update_check = QCheckBox("自动检查更新")
        self.auto_update_check.setToolTip("启动后与每隔一段时间自动检查 GitHub 新版本并提示（默认每 24 小时）")
        self.auto_update_check.setChecked(pet.auto_check_update)
        self.auto_update_check.toggled.connect(self._ok(self._on_auto_update))

        card_tools = Card("🛠️ 系统与工具", "开机自启、更新、全屏隐藏与磁盘图标",
                          tip="全屏隐藏：玩游戏时桌宠不会挡住画面\n"
                              "自动检查更新：发现新版本会弹窗询问是否下载\n"
                              "美化磁盘图标：写入 desktop.ini，普通权限即可；"
                              "Win11 若图标不显示可选用管理员模式重试")
        card_tools.add_checks([self.autostart_check, self.fullscreen_hide_check,
                               self.auto_update_check])
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

        about_card = Card("ℹ️ 关于", "版本、作者与交流群",
                          tip="点「检查更新」会读取 GitHub Releases 的最新版本号对比")
        about_link = QLabel(
            f'<a href="{UPDATE_URL}" style="color:#93c5fd; text-decoration:none;">'
            f'小鲸鱼桌宠 v{LOCAL_VERSION} · 访问更新源</a>')
        about_link.setOpenExternalLinks(True)
        info_label = QLabel(f"作者：shiyi312（辻弌）　·　QQ 群：{QQ_GROUP}")
        info_label.setStyleSheet("color:#94a3b8; font-size:13px;")
        about_card.add(about_link)
        about_card.add(info_label)
        p4.addWidget(about_card)
        p4.addStretch()

        self.tabs.addTab(page_interact, "互动")
        self.tabs.addTab(page_token, "Token")
        self.tabs.addTab(page_bubble, "气泡")
        self.tabs.addTab(page_system, "系统")
        self.tabs.currentChanged.connect(self._ok(self._on_tab_changed))
        # 标签栏不吃滚轮（否则在面板上滚动会误切换标签页）
        self._wheel_blocker = WheelBlocker(self)
        self.tabs.tabBar().installEventFilter(self._wheel_blocker)

        # 搜索框：过滤卡片（匹配卡片标题/说明/内部控件文字）
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索设置项（如 音量、泡泡、自启）")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._ok(self._on_search))
        root_layout.insertWidget(1, self.search_edit)     # 放在标题栏下方
        self._cards = self.findChildren(Card)

        # 统一用滚动容器包裹卡片：内容不超高时视觉与原来一致（无滚动条），
        # 内容超出屏幕时自动限高可滚动（各页按自身内容定高，见 _fit_to_page）
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
        self.card = card                     # 供 _fit_to_page 计算内容高度
        self.low_res_scroll = False

        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(150)
        self._hover_timer.timeout.connect(self.pet._guard("面板悬停", self._check_hover))
        self._fit_to_page()          # 初始按当前页内容定高
        self._open_time = time.monotonic()
        # 悬停轮询只在面板显示期间跑（起停见 showEvent / hideEvent）：
        # 面板关掉后还挂着每秒 6~7 次的空转没有意义，开多次设置还会越攒越多

    def showEvent(self, event):
        """面板显示出来才开始悬停轮询（自动关闭靠它）。"""
        super().showEvent(event)
        if not self._hover_timer.isActive():
            self._hover_timer.start()

    def hideEvent(self, event):
        """面板一关就停掉轮询，避免关掉之后还在后台空转。"""
        super().hideEvent(event)
        self._hover_timer.stop()

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

    def _ok(self, fn):
        """包装面板槽函数：异常写日志并继续运行（否则 PyQt 会直接终止进程）。"""
        return self.pet._guard(getattr(fn, "__name__", "面板操作"), fn)

    def _on_search(self, text):
        """全局搜索：跨所有标签页匹配卡片，并自动切到第一个命中的页。"""
        key = text.strip().lower()
        first_idx = None
        for idx in range(self.tabs.count()):
            page = self.tabs.widget(idx)
            hit_in_page = False
            for card in page.findChildren(Card):
                hit = (not key) or (key in card.keywords.lower())
                card.setVisible(hit)
                if hit and key:
                    hit_in_page = True
            if hit_in_page and first_idx is None:
                first_idx = idx
        if key and first_idx is not None and self.tabs.currentIndex() != first_idx:
            self.tabs.setCurrentIndex(first_idx)      # 自动跳到第一个命中的页
        self._fit_to_page()

    def _on_tab_changed(self, index):
        """记住上次所在的标签页，并让面板高度贴合该页内容。"""
        self.pet.panel_tab = int(index)
        self.pet.save()
        self._fit_to_page()

    def _fit_to_page(self):
        """面板尺寸：宽度按**所有页的最大需求**固定一次（切页不再变胖变瘦）；
        高度按当前页内容，上限为屏幕 85%（配合紧凑排版，尽量不用滚动）。"""
        page = self.tabs.currentWidget()
        if page is None:
            return
        if not getattr(self, "_width_fixed", False):
            max_w = max((c.minimumSizeHint().width() for c in self._cards), default=418)
            self.setFixedWidth(max(470, max_w + 38))
            self._width_fixed = True
        page_h = page.sizeHint().height()
        bar_h = self.tabs.tabBar().sizeHint().height()
        self.tabs.setFixedHeight(page_h + bar_h + 8)
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        need = self.card.sizeHint().height() + 24 + 8
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry() if screen else None
        limit = max(400, int(geo.height() * 0.92)) if geo else 1000
        self.low_res_scroll = need > limit
        self.setFixedHeight(min(need, limit))

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

    def _on_fullscreen_hide(self, enabled):
        self.pet.hide_in_fullscreen = bool(enabled)
        self.pet.save()

    def _on_auto_update(self, enabled):
        self.pet.set_auto_check_update(enabled)

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

    def _on_hud_show_token(self, enabled):
        self.pet.set_hud_show_token(enabled)

    def _on_hud_show_time(self, enabled):
        self.pet.set_hud_show_time(enabled)

    def _on_hud_show_date(self, enabled):
        self.pet.set_hud_show_date(enabled)

    def _on_app_rule_cooldown(self, val):
        self.cooldown_value.setText("每次打开都触发" if val == 0 else f"{val} 秒")
        self.pet.set_app_rule_cooldown(val)

    def _on_wander_delay(self, val):
        self.wander_delay_value.setText("不自动漫游" if val == 0 else f"{val} 秒")
        self.pet.set_wander_delay(val)

    def _on_evade_range(self, val):
        self.evade_range_value.setText(f"{val}px")
        self.pet.set_evade_range(val)

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

# ---------- 前台窗口 / 全屏判定（纯函数 + Win32 采集，可离线单测） ----------
# "全屏时自动隐藏桌宠"的判定逻辑。旧实现只看"窗口矩形盖住整屏"，于是：
#   1) 桌面（Progman/WorkerW）本身就铺满整屏 → 刷新桌面/点桌面时桌宠被当成"有全屏应用"而隐藏；
#   2) 最大化窗口（浏览器等）的矩形同样等于整块显示器 → 一打开浏览器桌宠就消失。
# 现在把判定拆成纯函数 is_fullscreen_window()（测试可直接喂假数据，
# 见 tests/check_fullscreen.py），采集 Win32 信息的部分单独放在 foreground_window_info()。

WS_CAPTION = 0x00C00000             # 标题栏（含 WS_BORDER | WS_DLGFRAME）
WS_THICKFRAME = 0x00040000          # 可调整大小的粗边框
GWL_STYLE = -16                     # 取窗口样式的索引
GA_ROOT = 2                         # GetAncestor：取顶层窗口
MONITOR_DEFAULTTONEAREST = 2        # MonitorFromWindow：取最近的显示器
FULLSCREEN_TOLERANCE = 2            # 像素容差：吸收边框/DPI 取整误差
FG_POLL_MS = 250                    # 前台窗口/全屏判定轮询间隔（退出全屏后 ≤0.5s 恢复）
FULLSCREEN_CONFIRM_TICKS = 2        # 连续几次判定为全屏才隐藏（防抖，切换窗口时不闪）
MOVE_MS_ACTIVE = 16                 # 移动节拍：真的在动时约 60fps
MOVE_MS_IDLE = 100                  # 移动节拍：静止时降到 10fps（每秒 60 次空转纯属浪费）
HWND_TOPMOST = -1                   # SetWindowPos：置于最前
SWP_NOSIZE = 0x0001                 # 保持尺寸
SWP_NOMOVE = 0x0002                 # 保持位置
SWP_NOACTIVATE = 0x0010             # 不抢焦点

# 桌面、任务栏这类 shell 窗口天生铺满屏幕，绝不能被当成"全屏应用"（小写比较）
SHELL_WINDOW_CLASSES = frozenset({
    "progman", "workerw", "shelldll_defview",         # 桌面本体（Win10 / Win11）
    "shell_traywnd", "shell_secondarytraywnd",        # 主屏 / 副屏任务栏
    "traynotifywnd", "tasklist_thumnail",             # 托盘溢出窗、任务栏缩略图
    "multitaskingviewframe",                          # 任务视图（Win10）
    "xamlexplorerhostislandwindow",                   # 任务视图 / Alt+Tab 浮层（Win11）
})

_win32_api = None                   # user32 原型缓存：只声明一次


def _win32():
    """集中声明 user32 / kernel32 原型（只做一次），返回 {"user32", "kernel32",
    "get_style", "monitor_info", "wt"}。
    64 位下句柄不声明类型会被当 int 传递而溢出，直接让整个进程崩掉。"""
    global _win32_api
    if _win32_api is not None:
        return _win32_api
    from ctypes import wintypes

    class MONITORINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

    user32 = ctypes.windll.user32
    for name in ("GetForegroundWindow", "GetShellWindow"):
        fn = getattr(user32, name)
        fn.argtypes = []
        fn.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, ctypes.c_uint]
    user32.GetAncestor.restype = wintypes.HWND
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL
    user32.IsZoomed.argtypes = [wintypes.HWND]
    user32.IsZoomed.restype = wintypes.BOOL
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.MonitorFromWindow.restype = wintypes.HANDLE
    user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MONITORINFO)]
    user32.GetMonitorInfoW.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                    ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    get_style = getattr(user32, "GetWindowLongPtrW", None) or user32.GetWindowLongW
    get_style.argtypes = [wintypes.HWND, ctypes.c_int]
    get_style.restype = ctypes.c_ssize_t
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _win32_api = {"user32": user32, "kernel32": kernel32, "get_style": get_style,
                  "monitor_info": MONITORINFO, "wt": wintypes}
    return _win32_api


def _monitor_rect_of(user32, monitor_info, handle):
    """取显示器句柄的矩形 (left, top, right, bottom)。拿不到返回 None。"""
    if not handle:
        return None
    mi = monitor_info()
    mi.cbSize = ctypes.sizeof(monitor_info)
    if not user32.GetMonitorInfoW(handle, ctypes.byref(mi)):
        return None
    r = mi.rcMonitor
    return (r.left, r.top, r.right, r.bottom)


def win32_monitor_rect(hwnd):
    """某个窗口所在显示器的矩形，坐标与窗口矩形同为 Win32 物理像素。
    高 DPI 缩放或副屏有偏移时，用它才不会和 Qt 的逻辑像素坐标错位。失败返回 None。"""
    try:
        api = _win32()
        user32 = api["user32"]
        handle = user32.MonitorFromWindow(api["wt"].HWND(hwnd), MONITOR_DEFAULTTONEAREST)
        return _monitor_rect_of(user32, api["monitor_info"], handle)
    except Exception:
        return None


def foreground_hwnd():
    """当前前台窗口句柄（0 表示拿不到）。用于判断焦点是否切换过。"""
    try:
        api = _win32()
        hwnd = api["user32"].GetForegroundWindow()
        return int(hwnd) if hwnd else 0
    except Exception:
        return 0


def foreground_window_info(self_pid=None):
    """采集前台窗口信息（供纯函数 is_fullscreen_window 判定）。失败返回 None。"""
    try:
        api = _win32()
        user32, wt = api["user32"], api["wt"]
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        root = user32.GetAncestor(hwnd, GA_ROOT) or hwnd     # 前台可能是子控件，取顶层窗口
        shell = user32.GetShellWindow()
        info = {
            "hwnd": int(root),
            "visible": bool(user32.IsWindowVisible(root)),
            "minimized": bool(user32.IsIconic(root)),
            "zoomed": bool(user32.IsZoomed(root)),
            "is_shell": bool(shell and root == shell),       # 桌面窗口本身
            "class_name": "",
            "style": 0,
            "pid": 0,
            "rect": None,
            "monitor_rect": None,
        }
        buf = ctypes.create_unicode_buffer(256)
        if user32.GetClassNameW(root, buf, len(buf)):
            info["class_name"] = buf.value
        info["style"] = int(api["get_style"](root, GWL_STYLE) or 0)
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(root, ctypes.byref(pid))
        info["pid"] = int(pid.value)
        rect = wt.RECT()
        if user32.GetWindowRect(root, ctypes.byref(rect)):
            info["rect"] = (rect.left, rect.top, rect.right, rect.bottom)
        info["monitor_rect"] = _monitor_rect_of(
            user32, api["monitor_info"],
            user32.MonitorFromWindow(root, MONITOR_DEFAULTTONEAREST))
        if self_pid is not None:
            info["self_pid"] = int(self_pid)
        return info
    except Exception:
        return None


def rect_covers(inner, outer, tolerance=FULLSCREEN_TOLERANCE):
    """纯函数：inner 矩形是否盖住 outer 矩形（容差 tolerance 像素）。"""
    if not inner or not outer:
        return False
    left, top, right, bottom = inner
    o_left, o_top, o_right, o_bottom = outer
    return (left <= o_left + tolerance and top <= o_top + tolerance
            and right >= o_right - tolerance and bottom >= o_bottom - tolerance)


def rects_intersect(a, b):
    """纯函数：两个 (left, top, right, bottom) 矩形是否有重叠。"""
    if not a or not b:
        return False
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def is_fullscreen_window(info, tolerance=FULLSCREEN_TOLERANCE):
    """纯函数：前台窗口是不是"真的全屏应用"（游戏 / 全屏视频）。

    info 的键由 foreground_window_info() 采集，测试可以直接喂假数据。
    任一条不满足即不算全屏：
      1. 窗口可见、且没有最小化；
      2. 不是桌面/任务栏这类 shell 窗口（它们天生铺满屏幕，不是全屏应用）；
      3. 不是桌宠自己的窗口（进程号相同）；
      4. 矩形要盖住"它所在的那块显示器"——注意是显示器，不是工作区
         （最大化窗口只盖住工作区，真全屏会连任务栏一起盖住）；
      5. "最大化"状态且带标题栏/边框的窗口不算全屏（浏览器最大化因此不再被误判）。
    """
    if not info or not info.get("visible") or info.get("minimized"):
        return False
    if info.get("is_shell"):
        return False
    if str(info.get("class_name") or "").strip().lower() in SHELL_WINDOW_CLASSES:
        return False
    if info.get("self_pid") is not None and info.get("pid") == info.get("self_pid"):
        return False
    if not rect_covers(info.get("rect"), info.get("monitor_rect"), tolerance):
        return False
    if info.get("zoomed") and int(info.get("style") or 0) & (WS_CAPTION | WS_THICKFRAME):
        return False
    return True


class PetWindow(QWidget):
    update_done = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        _t0 = time.monotonic()          # 启动耗时统计
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
        self._drag_hold = False
        self._wander_stuck = 0
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
        self.hud_show_token = bool(self.cfg.get("hud_show_token", True))
        self.hud_show_time = bool(self.cfg.get("hud_show_time", True))
        self.hud_show_date = bool(self.cfg.get("hud_show_date", True))
        self.panel_pinned = bool(self.cfg.get("panel_pinned", False))
        _pos = self.cfg.get("panel_pos")
        self.panel_pos = list(_pos) if isinstance(_pos, (list, tuple)) and len(_pos) == 2 else None
        self.panel_tab = max(0, min(3, int(self.cfg.get("panel_tab", 0))))
        self.snap_enabled = bool(self.cfg.get("snap_enabled", True))
        self.app_monitor_enabled = bool(self.cfg.get("app_monitor_enabled", True))
        self.hide_in_fullscreen = bool(self.cfg.get("hide_in_fullscreen", True))
        self._hidden_by_fullscreen = False
        self._fs_streak = 0             # 连续判定为全屏的次数（防抖计数）
        self.auto_check_update = bool(self.cfg.get("auto_check_update", True))
        self.update_check_interval_hours = max(1, min(168, int(self.cfg.get("update_check_interval_hours", 24))))
        self._update_tag = ""
        self._auto_check = False
        self.app_rule_cooldown = max(0, min(600, int(self.cfg.get("app_rule_cooldown", 0))))
        self.wander_delay = max(0, min(600, int(self.cfg.get("wander_delay", 60))))
        self.evade_range = max(100, min(1500, int(self.cfg.get("evade_range", 500))))
        self._last_rules_check = 0.0
        try:
            self._rules_mtime = os.path.getmtime(RULES_PATH)
        except OSError:
            self._rules_mtime = None
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
        self._hud_timer.timeout.connect(self._guard("HUD刷新", self._update_hud))
        self._hud_timer.start(1000)
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._guard("应用监控", self._monitor_tick))
        self._monitor_timer.start(1000)
        # 前台窗口 / 全屏判定单独走 250ms：只做几个轻量 Win32 调用，
        # 退出全屏后最多 0.5 秒就能恢复，不必等应用监控那 1 秒的节拍
        self._fg_timer = QTimer(self)
        self._fg_timer.timeout.connect(self._guard("前台窗口检测", self._foreground_tick))
        self._fg_timer.start(FG_POLL_MS)
        self._last_fore_hwnd = 0
        self._last_fore_exe = ""
        self._rule_fire_time = {}
        self._checking_update = False
        self.update_done.connect(self._ok(self._on_update_done))
        self._update_hud()

        self._sfx_pool = []
        self._sfx_seq = 0
        self._evade_tele_at = 0.0
        self._panel_lock = False
        self.sounds = {}
        self._squish_anim = None
        self._fade_anim = None
        self._base_pixmap = None
        self._mirror_cache = None           # 贴左边缘时的翻转位图缓存
        self._mirror_cache_src = None
        self._exe_by_pid = {}               # 进程号 → exe 名（避免每秒 OpenProcess）

        self.movie = None
        self._drag_pos = None
        self._dragging = False
        self._moved = False
        self.settings_panel = None

        self._last_expression = self.expression
        self._idle_8s = QTimer(self)
        self._idle_8s.setSingleShot(True)
        self._idle_8s.timeout.connect(self._guard("空闲8秒", self._on_idle_8s))
        self._idle_120s = QTimer(self)
        self._idle_120s.setSingleShot(True)
        self._idle_120s.timeout.connect(self._guard("空闲120秒", self._on_idle_120s))
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._guard("眨眼", self._do_blink))
        self._blink_back_timer = QTimer(self)
        self._blink_back_timer.setSingleShot(True)
        self._blink_back_timer.timeout.connect(self._guard("眨眼恢复", self._restore_after_blink))
        self._auto_rotate_timer = QTimer(self)
        self._auto_rotate_timer.timeout.connect(self._guard("自动轮换", self._on_auto_rotate))
        self._move_timer = QTimer(self)
        self._move_timer.timeout.connect(self._guard("移动", self._move_tick))
        self._move_timer.start(MOVE_MS_IDLE)     # 静止时 10fps，真动起来自动切 60fps

        self.expressions = scan_expressions()

        # 先把窗口放到最终位置、再生成贴图：这样启动瞬间的朝向（贴左边缘翻转）就是对的
        if self.cfg.get("x") is not None and self.cfg.get("y") is not None:
            self.move(int(self.cfg["x"]), int(self.cfg["y"]))
        else:
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(geo.right() - self.width() - 30, geo.bottom() - self.height() - 60)
        self.ensure_visible_on_screen()      # 位置兜底：绝不出现"程序在跑但看不到桌宠"

        self.apply_expression(self.expression, save=False, play_sound=False)
        self._refresh_mirror()

        self._load_sounds()
        self._sync_autostart()
        self._reset_idle_timers()
        # 启动 5 秒后自动检查一次更新（异步、不阻塞启动、静默失败）
        QTimer.singleShot(5000, self._guard("自动检查更新", lambda: self.check_update(auto=True)))
        self._log(f"小鲸鱼桌宠启动完成（初始化耗时 {int((time.monotonic() - _t0) * 1000)} ms）")

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
        # 预加载放到启动之后异步做，避免拖慢启动（首次点击也会即时加载，不影响播放）
        QTimer.singleShot(600, self._guard("音效预加载", self._preload_sound))

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
        if pix is None:
            return pix
        if self.auto_mirror and self._near_left_edge():
            # 贴左边缘时每一帧都翻转整张位图太浪费（移动时 60fps），缓存翻转结果
            if self._mirror_cache is not None and self._mirror_cache_src is pix:
                return self._mirror_cache
            self._mirror_cache_src = pix
            self._mirror_cache = pix.transformed(QTransform().scale(-1, 1))
            return self._mirror_cache
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

    def _pause_idle_timers(self):
        """全屏隐藏期间停掉 HUD/移动/眨眼/轮换：玩游戏时不再白烧 CPU。"""
        for timer in (self._hud_timer, self._move_timer, self._blink_timer,
                      self._auto_rotate_timer, self._idle_8s, self._idle_120s):
            timer.stop()

    def _resume_idle_timers(self):
        """恢复显示时把上面停掉的定时器按原逻辑重新起起来。"""
        if not self._hud_timer.isActive():
            self._hud_timer.start(1000)
        self._reset_idle_timers()
        self._reset_move_timer()

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
        if getattr(self, "_drag_hold", False):
            return          # 拖动中冻结布局：窗口尺寸/位置保持稳定，避免 HUD 抖动、重影
        # 卡片高度按"行数"自适应（Token 一行 / 日期时间一行）
        font = self.hud_card._font()
        fm = QFontMetrics(font)
        rows = max(1, self.hud_card.row_count())
        card_h = fm.height() * rows + 4 * (rows - 1) + 18
        # 关键：HUD 宽度不超过角色宽度 —— 这样窗口宽度 = 角色宽度，
        # 贴边时是"角色本人贴边"，不会出现"HUD 碰到边、人却没碰到"
        card_w = min(self.size_px, max(140, self.hud_card.desired_width()))
        win_w = self.size_px
        has_content = bool(self._hud_parts())
        if self.hud_visible and has_content:
            win_h = self.size_px + card_h + HUD_GAP
        else:
            win_h = self.size_px + 4
        if self.width() != win_w or self.height() != win_h:
            self.setFixedSize(win_w, win_h)
        self.hud_card.setFixedHeight(card_h)
        self.label.setGeometry(0, 0, self.size_px, self.size_px)
        self.hud_card.setGeometry((win_w - card_w) // 2, self.size_px + HUD_GAP, card_w, card_h)
        self.hud_card.setVisible(self.hud_visible and has_content)
        self.label.raise_()

    def _hud_font_px(self):
        # 字号跟随角色适度缩放（13~18px）：既能看清，又不会把时间日期撑得很大
        return max(13, min(18, int(self.size_px * 0.065)))

    def _hud_parts(self):
        """组装 HUD 内容：Token 与时间/日期各自独立开关，谁关掉就不显示谁。"""
        now = time.localtime()
        data = {}
        if self.hud_show_token and self.token_enabled:
            data["token"] = self._shown_token
        if self.hud_show_time:
            data["time"] = time.strftime("%H:%M:%S", now)
            if self.hud_show_date:
                data["date"] = time.strftime("%Y-%m-%d", now) + " 周" + "一二三四五六日"[now.tm_wday]
        return data

    def _update_hud(self):
        self.hud_card.apply_theme(self.bubble_color)
        self.hud_card.set_content(self._hud_parts(), self._hud_font_px(), "idle", self.hud_abbrev)
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
        anim.valueChanged.connect(self._ok(self._on_token_roll))
        anim.finished.connect(self._ok(self._on_token_roll_done))
        anim.start()
        self._token_roll = anim

    def _on_token_roll(self, v):
        self._shown_token = int(v)
        if self.token_enabled:
            tint = "gain" if self.token > self._shown_token else "cost"
            pulse_font = self._hud_font_px() + (1 if tint != "idle" else 0)
            self.hud_card.set_content(self._hud_parts(), pulse_font, tint, self.hud_abbrev)
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
            self._log(f"喂食失败: {path} ({e!r})")
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
    def _guard(self, name, fn):
        """把定时器回调/信号槽包一层：异常写日志并继续运行，绝不让进程静默退出。
        同时按原函数签名裁剪 Qt 多传的参数（clicked 会带 checked，
        PyQt 原生会裁剪，包一层后必须自己裁，否则会 TypeError）。"""
        try:
            params = [p for p in inspect.signature(fn).parameters.values()
                      if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
            n_pos = len(params)
            var_args = any(p.kind == p.VAR_POSITIONAL
                           for p in inspect.signature(fn).parameters.values())
        except (TypeError, ValueError):
            n_pos, var_args = 0, True

        def wrapper(*args, **kwargs):
            try:
                if not var_args and len(args) > n_pos:
                    args = args[:n_pos]
                return fn(*args, **kwargs)
            except Exception as e:
                self._log(f"[异常] {name}: {e!r}\n{traceback.format_exc()}")
                return None
        return wrapper

    def _ok(self, fn):
        """同 _guard，自动取函数名（供信号连接使用）。"""
        return self._guard(getattr(fn, "__name__", "回调"), fn)

    def _log(self, msg):
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        except Exception:
            pass

    def _get_foreground_exe(self):
        """前台窗口的 (进程名, 标题)，进程名小写；拿不到返回 ("", "")。
        进程名按进程号缓存：OpenProcess 每秒做一次纯属浪费，标题则每次都读。"""
        try:
            api = _win32()
            user32, wt = api["user32"], api["wt"]
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "", ""
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(max(1, n + 1))
            user32.GetWindowTextW(hwnd, buf, len(buf))
            pid = wt.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            return self._exe_name_of(int(pid.value)), buf.value
        except Exception:
            return "", ""

    def _exe_name_of(self, pid):
        """按进程号取 exe 文件名（小写）。同一进程只查一次（结果含空值也缓存）。"""
        if not pid:
            return ""
        if pid in self._exe_by_pid:
            return self._exe_by_pid[pid]
        exe = ""
        try:
            api = _win32()
            kernel32, wt = api["kernel32"], api["wt"]
            hproc = kernel32.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
            if hproc:
                try:
                    size = wt.DWORD(512)
                    buf = ctypes.create_unicode_buffer(size.value)
                    if kernel32.QueryFullProcessImageNameW(hproc, 0, buf, ctypes.byref(size)):
                        exe = os.path.basename(buf.value).lower()
                finally:
                    kernel32.CloseHandle(hproc)
        except Exception:
            exe = ""
        if len(self._exe_by_pid) > 64:      # 缓存别无限长（长时间运行会换很多前台进程）
            self._exe_by_pid.clear()
        self._exe_by_pid[pid] = exe
        return exe

    def _rule_chance_hit(self, rule):
        """规则概率判定：chance 为 0~100 的百分比。"""
        chance = int(rule.get("chance", 100))
        return chance >= 100 or random.random() * 100 < chance

    def _rule_key(self, rule):
        """冷却按规则内容记录（不用序号，增删规则不会错位）。"""
        return f"{str(rule.get('match', '')).strip().lower()}|{str(rule.get('text', '')).strip()}"

    def _maybe_reload_rules(self):
        """规则文件被记事本改过后自动重载（无需手动点按钮）。"""
        now = time.monotonic()
        if now - self._last_rules_check < 3:
            return
        self._last_rules_check = now
        try:
            mtime = os.path.getmtime(RULES_PATH)
        except OSError:
            return
        if self._rules_mtime is not None and mtime != self._rules_mtime:
            self._rules_mtime = mtime
            rules = load_rules_file()
            if rules:
                self.app_rules = rules
                self._rule_fire_time = {}
                self._log(f"检测到规则文件变化，已自动重新加载（{len(rules)} 条）")
                panel = self.settings_panel
                if panel is not None and panel.isVisible():
                    try:
                        panel._refresh_rules()
                    except Exception:
                        pass
        else:
            self._rules_mtime = mtime

    def _is_fullscreen_foreground(self):
        """前台窗口是否真的是全屏应用（游戏/全屏视频）→ 用于临时隐藏桌宠，避免遮挡。
        判定细节在模块级纯函数 is_fullscreen_window()（tests/check_fullscreen.py 单测它）。
        另外只认"与桌宠同一块显示器被全屏占用"：副屏全屏看电影时，主屏的桌宠不该被藏起来。"""
        info = foreground_window_info(self_pid=os.getpid())
        if not is_fullscreen_window(info):
            return False
        return rects_intersect(info.get("monitor_rect"), self._screen_rect())

    def _screen_rect(self):
        """桌宠所在显示器的矩形 (left, top, right, bottom)，用于和窗口矩形比较。

        优先用 Win32 的 MonitorFromWindow：它和窗口矩形同属物理像素坐标系，
        高 DPI 缩放、副屏有偏移时不会与 Qt 的逻辑像素错位；拿不到再退回 QScreen。
        """
        rect = win32_monitor_rect(int(self.winId()))
        if rect:
            return rect
        screen = None
        try:
            screen = self.screen()                      # Qt >= 5.14
        except Exception:
            screen = None
        if screen is None:
            try:
                screen = QApplication.screenAt(self.geometry().center())
            except Exception:
                screen = None
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            return None
        g = screen.geometry()
        return (g.left(), g.top(), g.right(), g.bottom())

    def _fullscreen_tick(self):
        """全屏应用时临时隐藏桌宠与气泡；退出全屏后立即恢复。

        判定见 _is_fullscreen_foreground()（严格全屏：桌面、任务栏、最大化窗口都不算）。
        连续 FULLSCREEN_CONFIRM_TICKS 次判定为全屏才隐藏（防抖，切换窗口瞬间不闪），
        但只要有一次不是全屏就立刻恢复显示。"""
        if not self.hide_in_fullscreen:
            self._fs_streak = 0
            if self._hidden_by_fullscreen:
                self._restore_from_fullscreen("已关闭「全屏时自动隐藏」")
            return
        self._fs_streak = self._fs_streak + 1 if self._is_fullscreen_foreground() else 0
        if self._fs_streak >= FULLSCREEN_CONFIRM_TICKS and not self._hidden_by_fullscreen:
            self._hide_for_fullscreen()
        elif self._fs_streak == 0 and self._hidden_by_fullscreen:
            self._restore_from_fullscreen("全屏应用已退出")

    def _foreground_tick(self):
        """每 250ms 一次：跟踪前台窗口变化 + 全屏判定。

        只在前台窗口真的换了的时候补一次置顶（有些程序抢焦点会把桌宠压到下面），
        其余时候不碰 z-order，避免频繁 SetWindowPos 造成抖动。"""
        hwnd = foreground_hwnd()
        if hwnd != self._last_fore_hwnd:
            self._last_fore_hwnd = hwnd
            self._reassert_topmost()
        self._fullscreen_tick()

    def _hide_for_fullscreen(self):
        self._hidden_by_fullscreen = True
        try:
            self.bubble.hide()
        except Exception:
            pass
        self.hide()
        self._pause_idle_timers()           # 隐藏期间不再刷 HUD / 空转移动
        info = foreground_window_info() or {}
        self._log(f"检测到全屏应用[{info.get('class_name') or '未知'}]，"
                  "已临时隐藏桌宠（退出全屏后自动恢复）")

    def _restore_from_fullscreen(self, reason):
        self._hidden_by_fullscreen = False
        self._fs_streak = 0
        self.show()
        self.raise_()
        self._resume_idle_timers()
        self._reassert_topmost()
        self._log(f"{reason}，桌宠恢复显示")

    def _reassert_topmost(self):
        """把桌宠重新顶到最前（HWND_TOPMOST）。

        Qt 的 WindowStaysOnTopHint 只在建窗时生效一次，别的程序抢焦点或最大化时
        可能把桌宠压到 z-order 下面（表现为"被浏览器盖住、看不见了"），这里兜底补一次。"""
        if not self.always_on_top or not self.isVisible():
            return
        try:
            api = _win32()
            api["user32"].SetWindowPos(
                api["wt"].HWND(int(self.winId())), api["wt"].HWND(HWND_TOPMOST),
                0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        except Exception:
            pass

    def _update_schedule_tick(self):
        """按间隔自动检查更新（默认每 24 小时一次，可在设置里关闭）。"""
        if not self.auto_check_update:
            return
        if getattr(self, "_checking_update", False):
            return
        interval = max(1, int(self.update_check_interval_hours)) * 3600
        now = time.time()
        if now - float(self.cfg.get("last_update_check", 0) or 0) >= interval:
            self.cfg["last_update_check"] = now
            self.save()
            self.check_update(auto=True)

    def _monitor_tick(self):
        self._update_schedule_tick()
        if not self.app_monitor_enabled:
            return
        self._maybe_reload_rules()
        exe, title = self._get_foreground_exe()
        if "whaledesktop" in exe:
            return
        # 进程名拿不到时（应用以更高权限运行等）改用窗口标题兜底匹配
        ident = exe if exe else ("title:" + title.strip().lower())
        if not ident or ident == self._last_fore_exe:
            return
        self._last_fore_exe = ident
        hay = (exe + " " + title).lower()
        if not hay.strip():
            return
        now = time.monotonic()
        for rule in self.app_rules:
            if not isinstance(rule, dict) or not rule.get("enabled"):
                continue
            match = str(rule.get("match", "")).strip().lower()
            text = str(rule.get("text", "")).strip()
            if not match or not text or match not in hay:
                continue
            if not self._rule_chance_hit(rule):
                self._log(f"应用监控：规则[{match}] 概率未命中（{rule.get('chance', 100)}%）")
                continue
            last = self._rule_fire_time.get(self._rule_key(rule), 0.0)
            if self.app_rule_cooldown > 0 and now - last < self.app_rule_cooldown:
                left = int(self.app_rule_cooldown - (now - last))
                self._log(f"应用监控：规则[{match}] 冷却中，{left} 秒后可再触发"
                          f"（可在设置面板把「触发冷却」调成 0 秒=每次都触发）")
                return
            self._rule_fire_time[self._rule_key(rule)] = now
            self._log(f"应用监控触发: {match} -> {text}"
                      f"（{exe or '仅标题匹配'} / {title}）")
            if not self.bubble_on:
                self._log("应用监控：气泡显示已关闭，本次未弹出（可在设置里开启气泡）")
                return
            self.show_bubble_quick(text)
            return

    def check_update(self, auto=False):
        if getattr(self, "_checking_update", False):
            return
        self._auto_check = bool(auto)
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
                self._update_tag = tag
                self.update_done.emit(f"发现新版本 v{tag}")
                if not getattr(self, "_auto_check", False):
                    webbrowser.open(UPDATE_URL)      # 手动检查：直接打开下载页
            else:
                self._update_tag = ""
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
        self._log(f"检查更新：{msg}")
        tag = getattr(self, "_update_tag", "")
        if getattr(self, "_auto_check", False) and tag:
            # 自动检查：只在发现新版本时提示一次，不自动打开浏览器、不打扰
            if tag == (self.cfg.get("skipped_version") or ""):
                self.show_bubble_quick(f"新版本 v{tag} 可用（你已选择忽略）")
                return
            ret = QMessageBox.question(
                self, "发现新版本",
                f"小鲸鱼桌宠新版本 v{tag} 已发布（当前版本 v{LOCAL_VERSION}）。\n\n"
                "是否前往 GitHub 下载更新？\n"
                "（选“否”则本次忽略，下次启动不再提示这个版本）",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if ret == QMessageBox.Yes:
                webbrowser.open(UPDATE_URL)
                self.show_bubble_quick(f"正在打开下载页 v{tag}")
            else:
                self.cfg["skipped_version"] = tag
                self.save()
                self.show_bubble_quick("已忽略本次更新提示")
        else:
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
        try:
            self._move_step()
        finally:
            self._reset_move_timer()

    def _reset_move_timer(self):
        """按需调整移动节拍：真的在动（拖动/跟随/躲避/漫游/弹射）才 60fps，
        静止时降到 10fps —— 否则每秒 60 次空转唤醒纯属白烧 CPU。"""
        moving = (self._sling_active or self._r_dragging or self._dragging
                  or self.follow_mode or self.evade_mode or self.wander_mode
                  or self._wander_on or getattr(self, "_drag_hold", False))
        want = MOVE_MS_ACTIVE if moving else MOVE_MS_IDLE
        if not self._move_timer.isActive() or self._move_timer.interval() != want:
            self._move_timer.start(want)

    def _move_step(self):
        dt = 1 / 60.0
        if self.lock_position:
            return
        if self.settings_panel is not None and self.settings_panel.isVisible():
            return
        # 用户正在拖动/按住时，自动移动（漫游/跟随/躲避）必须让位，
        # 否则会和拖动抢位置 → 表现为平移、抖动、重影
        if self._dragging or getattr(self, "_drag_hold", False):
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
        if d >= self.evade_range:
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
        sp = 600.0 * self.evade_range / max(d, 1)
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
            if self.wander_delay <= 0:
                return                      # 0 秒 = 不自动开始漫游
            if time.monotonic() - self._last_interact < self.wander_delay:
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
        # 卡住检测：贴边或受限导致位置几乎没动 → 结束这一段，休息后换个方向（避免原地抖动）
        nx, ny = self._center()
        if abs(nx - cx) < 0.5 and abs(ny - cy) < 0.5:
            self._wander_stuck = getattr(self, "_wander_stuck", 0) + 1
            if self._wander_stuck >= 6:
                self._wander_stuck = 0
                self._wander_mode_state = "stop"
                self._wander_delay = random.uniform(1.5, 3.0)
                self._wander_speed = 0.0
                self._wander_angle = random.uniform(0, math.tau)
                self._wander_turn = 0.0
        else:
            self._wander_stuck = 0

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
    def ensure_visible_on_screen(self):
        """确保窗口大部分在屏幕可见范围内（换分辨率/缩放/显示器后旧坐标可能在屏幕外，
        会导致"程序在运行但桌面上看不到桌宠"）。"""
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        rect = QRect(self.x(), self.y(), max(1, self.width()), max(1, self.height()))
        inter = rect.intersected(geo)
        visible = max(0, inter.width()) * max(0, inter.height())
        total = rect.width() * rect.height()
        if total <= 0 or visible < total * 0.35:
            nx = geo.right() - self.width() - 40
            ny = geo.bottom() - self.height() - 80
            nx = max(geo.left(), min(nx, geo.right() - self.width()))
            ny = max(geo.top(), min(ny, geo.bottom() - self.height()))
            self._log(f"启动位置 ({rect.x()},{rect.y()}) 超出屏幕可见范围，已重置到 ({nx},{ny})")
            self.move(int(nx), int(ny))
            self.save()

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
                if not self._moved:
                    # 一旦进入拖动，取消按压压扁，避免拖拽时图像变形（看起来像重影/断触）
                    self._animate_squish(1.0, 1.0, 80)
                    self._drag_hold = True      # 拖动期间冻结 HUD 布局更新
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
            if getattr(self, "_drag_hold", False):
                self._drag_hold = False
                self._update_hud()          # 拖动结束后再刷新 HUD 布局
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
        anim.valueChanged.connect(self._ok(self._on_squash_frame))
        anim.finished.connect(self._ok(self._on_squash_done))
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
        screen = QApplication.primaryScreen()
        top = screen.availableGeometry().top() if screen else 0
        w = self.bubble.width()
        h = self.bubble.height()
        x = self.x() + (self.width() - w) // 2
        y = self.y() - h - 8
        self.bubble.tail_up = False
        if y < top:
            y = self.y() + self.height() + 8
            self.bubble.tail_up = True          # 气泡在下方 → 尖头朝上
        x, y = clamp_to_screen(x, y, w, h)      # 贴边时气泡不会被屏幕截断
        self.bubble.move(x, y)

    def moveEvent(self, event):
        """任何方式的位置变化（吸附、瞬移、拖动、自动移动）都让气泡跟上。"""
        super().moveEvent(event)
        self.sync_bubble_position()

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
        self._reset_move_timer()        # 立刻切到 60fps，跟随不迟滞
        self.save()

    def set_evade_mode(self, enabled):
        self.evade_mode = bool(enabled)
        if self.evade_mode:
            self.follow_mode = False
        self._vx = self._vy = 0.0
        self._reset_move_timer()
        self.save()

    def set_wander_mode(self, enabled):
        self.wander_mode = bool(enabled)
        self._wander_on = False
        self._reset_move_timer()
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
        if not self._hidden_by_fullscreen:
            self.show()                 # 正被全屏隐藏时不要把它弹出来
        self._reassert_topmost()
        self.save()

    def set_hud_visible(self, visible):
        self.hud_visible = bool(visible)
        self._apply_layout()
        self.save()

    def set_hud_abbrev(self, enabled):
        self.hud_abbrev = bool(enabled)
        self._update_hud()
        self.save()

    def set_hud_show_token(self, enabled):
        self.hud_show_token = bool(enabled)
        self._update_hud()
        self.save()

    def set_hud_show_time(self, enabled):
        self.hud_show_time = bool(enabled)
        self._update_hud()
        self.save()

    def set_hud_show_date(self, enabled):
        self.hud_show_date = bool(enabled)
        self._update_hud()
        self.save()

    def set_app_rule_cooldown(self, sec):
        self.app_rule_cooldown = max(0, min(600, int(sec)))
        self.save()

    def set_wander_delay(self, sec):
        self.wander_delay = max(0, min(600, int(sec)))
        self.save()

    def set_evade_range(self, px):
        self.evade_range = max(100, min(1500, int(px)))
        self.save()

    def set_auto_check_update(self, enabled):
        self.auto_check_update = bool(enabled)
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
        """磁盘图标美化 / 恢复（autorun.inf + icon.ico，普通权限即可）。"""
        png = ""
        for e in self.expressions:
            if e["name"] == "v1_fatfish":
                png = e["path"]
                break
        drives = list(os.listdrives()) if hasattr(os, "listdrives") else ["C:\\"]
        if not drives:
            self.show_bubble_quick("没有找到可用磁盘")
            return
        drive, ok = QInputDialog.getItem(
            self, "磁盘图标", "选择磁盘：", drives, 0, False)
        if not ok or not drive:
            return
        # 选择操作：应用 / 恢复
        box = QMessageBox(self)
        box.setWindowTitle("磁盘图标")
        box.setText(f"对 {drive} 要做什么？")
        apply_btn = box.addButton("应用大肥鱼图标", QMessageBox.AcceptRole)
        restore_btn = box.addButton("恢复默认图标", QMessageBox.DestructiveRole)
        box.addButton("取消", QMessageBox.RejectRole)
        box.exec_()
        clicked = box.clickedButton()

        if clicked is restore_btn:
            ok, msg = remove_drive_icon(drive)
            self._log(f"磁盘图标恢复：{drive} - {msg}")
            if ok:
                self.show_bubble_quick(msg[:40])
                QMessageBox.information(
                    self, "已恢复默认图标",
                    f"{drive} {msg}\n\n"
                    "⚠️ 如果「此电脑」里图标还没变：Windows 把盘符图标缓存在**登录会话**里，"
                    "F5、重启资源管理器都刷不掉 —— **注销一次或重启电脑**就会变回默认图标。")
            else:
                # 需要用户动手时（比如去点 UAC 弹窗）不能只弹个几十字就消失的气泡
                QMessageBox.warning(self, "恢复默认图标", msg)
            return
        if clicked is not apply_btn:
            return

        if not png:
            self.show_bubble_quick("没有找到大肥鱼素材")
            return
        # 先在临时目录生成 ico（不需要盘根权限），再复制到磁盘根目录
        tmp_ico = os.path.join(os.environ.get("TEMP", "."), "dshw_fish.ico")
        ok, reason = build_fish_ico(png, tmp_ico)
        if not ok:
            self._log(f"磁盘图标：生成失败 - {reason}")
            self.show_bubble_quick(f"图标生成失败：{reason[:34]}")
            return
        ok, reason = apply_drive_icon(drive, tmp_ico, set_root_system=is_admin())
        if ok:
            self._log(f"磁盘图标应用成功：{drive}"
                      f"（desktop.ini + autorun.inf，管理员模式={is_admin()}）")
            self.show_bubble_quick(f"{drive} 图标已设置")
            if not is_admin():
                ret = QMessageBox.question(
                    self, "图标已设置",
                    f"{drive} 图标已设置完成。\n\n"
                    "⚠️ 如果「此电脑」里图标还没变，这是正常的：Windows 把盘符图标缓存在"
                    "**登录会话**里，F5、重启资源管理器都刷不掉 —— **注销一次或重启电脑**就会显示。\n\n"
                    "另外：部分 Windows 11 电脑还要求磁盘根目录带「系统 + 只读」属性才认自定义图标，"
                    "这一步需要管理员权限。\n\n"
                    "是否现在以管理员身份重启桌宠，并自动补上盘根属性后重新设置？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if ret == QMessageBox.Yes:
                    self.relaunch_as_admin()
            else:
                QMessageBox.information(
                    self, "磁盘图标已设置",
                    f"{drive} 磁盘图标已设置成功（管理员模式，已包含盘根属性）。\n\n"
                    "⚠️ 图标没变的话：**注销一次或重启电脑**就会生效"
                    "（Windows 会缓存盘符图标，F5 / 重启资源管理器都刷不掉）。\n\n"
                    "想还原：再点一次「美化磁盘图标」选「恢复默认图标」。")
        else:
            self._log(f"磁盘图标：应用失败（{drive}）- {reason}")
            self.show_bubble_quick(f"失败：{reason[:32]}")
            if not is_admin():
                ret = QMessageBox.question(
                    self, "可以重试",
                    f"{reason}\n\n是否以管理员身份重启桌宠后重试？\n"
                    "（会弹出系统“用户账户控制”窗口，点“是”即可）",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if ret == QMessageBox.Yes:
                    self.relaunch_as_admin()

    def relaunch_as_admin(self):
        """以管理员身份重新启动自己（弹 UAC），成功后退出当前实例。"""
        try:
            exe = sys.executable
            if getattr(sys, "frozen", False):
                params = " ".join(f'"{a}"' for a in sys.argv[1:])
            else:
                params = f'"{os.path.abspath(__file__)}"'
            # 先释放单实例锁，否则新实例会被判定为"已在运行"
            lock = getattr(self, "_lock", None)
            if lock is not None:
                try:
                    lock.unlock()
                except Exception:
                    pass
            r = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
            if int(r) <= 32:
                self._log(f"提权重启被拒绝（ShellExecuteW 返回 {r}）")
                self.show_bubble_quick("提权被取消，已保持当前运行")
                return
            self._log("已请求以管理员身份重启桌宠")
            QApplication.quit()
        except Exception as e:
            self._log(f"提权重启失败: {e!r}")
            self.show_bubble_quick("提权失败，请手动以管理员身份运行")

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
        cfg["hide_in_fullscreen"] = self.hide_in_fullscreen
        cfg["auto_check_update"] = self.auto_check_update
        cfg["update_check_interval_hours"] = self.update_check_interval_hours
        cfg["app_rule_cooldown"] = self.app_rule_cooldown
        cfg["wander_delay"] = self.wander_delay
        cfg["evade_range"] = self.evade_range
        cfg["hud_show_token"] = self.hud_show_token
        cfg["hud_show_time"] = self.hud_show_time
        cfg["hud_show_date"] = self.hud_show_date
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
        settings_act.triggered.connect(self._guard("托盘:open_settings", lambda: self.open_settings()))
        toggle_act = menu.addAction("显示/隐藏")
        toggle_act.triggered.connect(self._guard("托盘:toggle_visible", self.toggle_visible))
        menu.addSeparator()
        add_token_act = menu.addAction("Token +520W")
        add_token_act.triggered.connect(self._guard("托盘:add_tokens", lambda: self.add_tokens(5200000)))
        clear_token_act = menu.addAction("清空 Token")
        clear_token_act.triggered.connect(self._guard("托盘:clear_tokens", self.clear_tokens))
        hud_act = menu.addAction("显示/隐藏 Token HUD")
        hud_act.triggered.connect(self._guard("托盘:toggle_hud", self.toggle_hud))
        menu.addSeparator()
        top_act = menu.addAction("切换始终置顶")
        top_act.triggered.connect(self._guard("托盘:toggle_always_on_top", self.toggle_always_on_top))
        reload_act = menu.addAction("重新加载表情")
        reload_act.triggered.connect(self._guard("托盘:reload_expressions", self.reload_expressions))
        menu.addSeparator()
        update_act = menu.addAction("检查更新")
        update_act.triggered.connect(self._guard("托盘:check_update", self.check_update))
        log_act = menu.addAction("打开运行日志")
        log_act.triggered.connect(self._guard("托盘:open_log", self.open_log))
        menu.addSeparator()
        about_act = menu.addAction("关于小鲸鱼")
        about_act.triggered.connect(self._guard("托盘:show_about", self.show_about))
        qq_act = menu.addAction(f"加入 QQ 群（{QQ_GROUP}）")
        qq_act.triggered.connect(self._guard("托盘:open_qq_group", self.open_qq_group))
        drive_act = menu.addAction("美化磁盘图标（大肥鱼）")
        drive_act.triggered.connect(self._guard("托盘:beautify_drive_icons", self.beautify_drive_icons))
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
            f"作者：shiyi312（辻弌）\n"
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


def enable_high_dpi():
    """启用高 DPI 缩放（必须在 QApplication 创建前调用）。
    否则在 125%/150% 缩放屏幕上，鼠标坐标（物理像素）与窗口移动（逻辑像素）
    不一致，拖动会漂移、跳位甚至方向错乱（表现为"断触/重影"）。"""
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def main():
    # 注意：不启用 AA_EnableHighDpiScaling。
    # 它在 125%/150% 缩放的屏幕上会把整个界面按比例放大渲染（面板/HUD 视觉变大），
    # 与"界面小巧、桌宠能真正贴边"的初衷冲突；拖拽漂移已由
    # "_move_tick 拖动让位 + 拖动时取消压扁" 解决，无需全局缩放。
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    install_excepthook()
    rotate_log_if_needed()
    lock = QLockFile(os.path.join(os.path.expanduser("~"), ".dshw-pet.lock"))
    lock.setStaleLockTime(30000)
    if not lock.tryLock(100):
        QMessageBox.information(None, "小鲸鱼桌宠", "小鲸鱼桌宠已经运行了，请不要重复启动。")
        return
    pet = PetWindow()
    pet._lock = lock            # 供"以管理员身份重启"时释放单实例锁
    pet.show()
    pet.create_tray()
    app.aboutToQuit.connect(lambda: pet._log("小鲸鱼桌宠退出"))
    app.aboutToQuit.connect(lock.unlock)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
