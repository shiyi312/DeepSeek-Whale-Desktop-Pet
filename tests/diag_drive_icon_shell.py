# -*- coding: utf-8 -*-
r"""诊断：Windows 壳层现在实际给某个盘用的图标，是不是我们放的「大肥鱼」。

原理：SHGetFileInfoW(SHGFI_ICON) 返回的就是资源管理器「此电脑」里显示的那个图标，
把它和 icon.ico 的图标都画到 32x32 位图上比对像素 —— 一致就说明壳层已经认了。
用来判断「图标没变」到底是壳层没认（要改做法），还是只是界面没刷新（要改刷新方式）。

用法：python tests/diag_drive_icon_shell.py [盘符...]      例如：D:\ C:\
"""
import ctypes
import hashlib
import os
import sys
from ctypes import wintypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

shell32 = ctypes.windll.shell32
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# 64 位下句柄必须声明类型，否则会截断成 int 直接崩
shell32.SHGetFileInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
                                   ctypes.c_void_p, ctypes.c_uint,
                                   ctypes.c_uint]
shell32.SHGetFileInfoW.restype = ctypes.c_void_p
user32.DrawIconEx.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.HICON,
                              ctypes.c_int, ctypes.c_int, wintypes.UINT, wintypes.HBRUSH,
                              wintypes.UINT]
user32.DrawIconEx.restype = wintypes.BOOL
user32.DestroyIcon.argtypes = [wintypes.HICON]
user32.DestroyIcon.restype = wintypes.BOOL
user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.UINT,
                                   ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE,
                                   wintypes.DWORD]
gdi32.CreateDIBSection.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HANDLE]
gdi32.SelectObject.restype = wintypes.HANDLE
gdi32.DeleteObject.argtypes = [wintypes.HANDLE]
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.PatBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                         ctypes.c_int, wintypes.DWORD]

SHGFI_ICON = 0x000000100
SIZE = 32
DI_NORMAL = 0x0003


class SHFILEINFOW(ctypes.Structure):
    _fields_ = [("hIcon", wintypes.HICON), ("iIcon", ctypes.c_int),
                ("dwAttributes", wintypes.DWORD),
                ("szDisplayName", ctypes.c_wchar * 260),
                ("szTypeName", ctypes.c_wchar * 80)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def icon_pixels(hicon, size=SIZE):
    """把 HICON 画到 32 位 DIB 上，返回原始像素（BGRA）。"""
    hdc = user32.GetDC(None)
    memdc = gdi32.CreateCompatibleDC(hdc)
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = size
    bmi.bmiHeader.biHeight = -size              # 负数 = 自上而下
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bits = ctypes.c_void_p()
    hbmp = gdi32.CreateDIBSection(memdc, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0)
    old = gdi32.SelectObject(memdc, hbmp)
    gdi32.PatBlt(memdc, 0, 0, size, size, 0x00FF0062)        # 先涂白，便于比对
    user32.DrawIconEx(memdc, 0, 0, hicon, size, size, 0, None, DI_NORMAL)
    data = ctypes.string_at(bits, size * size * 4)
    gdi32.SelectObject(memdc, old)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(memdc)
    user32.ReleaseDC(None, hdc)
    return data


def shell_icon_hash(path):
    """问壳层：这个路径现在用哪个图标（返回像素哈希）。"""
    shfi = SHFILEINFOW()
    r = shell32.SHGetFileInfoW(path, 0, ctypes.byref(shfi), ctypes.sizeof(shfi), SHGFI_ICON)
    if not r or not shfi.hIcon:
        return None, "拿不到图标"
    try:
        return hashlib.sha256(icon_pixels(shfi.hIcon)).hexdigest()[:16], ""
    finally:
        user32.DestroyIcon(shfi.hIcon)


# ---- 分级刷新：看看哪种通知能让壳层重新读取 desktop.ini ----
SHCNE_ASSOCCHANGED = 0x08000000
SHCNE_UPDATEDIR = 0x00001000
SHCNE_UPDATEITEM = 0x00002000
SHCNE_ATTRIBUTES = 0x00000800
SHCNF_PATHW = 0x0005
SHCNF_IDLIST = 0x0000


def notify(event, path=None):
    try:
        if path is None:
            shell32.SHChangeNotify(event, SHCNF_IDLIST, None, None)
        else:
            shell32.SHChangeNotify(event, SHCNF_PATHW, ctypes.c_wchar_p(path), None)
        return True
    except Exception:
        return False


def try_refresh_chain(drive, target_hash):
    """依次尝试各种刷新手段，返回第一个让壳层认账的那一步（失败返回 None）。"""
    steps = [
        ("① 广播「文件关联变了」(现在程序里用的就是这个)",
         lambda: notify(SHCNE_ASSOCCHANGED)),
        ("② 通知「D 盘这个目录变了」", lambda: notify(SHCNE_UPDATEDIR, drive)),
        ("③ 通知「desktop.ini 这个文件变了」",
         lambda: notify(SHCNE_UPDATEITEM, os.path.join(drive, "desktop.ini"))),
        ("④ 通知「D 盘的属性变了」", lambda: notify(SHCNE_ATTRIBUTES, drive)),
        ("⑤ ie4uinit.exe -show（重建图标缓存）", lambda: _ie4uinit()),
    ]
    for label, fn in steps:
        fn()
        h, _ = shell_icon_hash(drive)
        ok = (h == target_hash)
        print(f"  {label:<44} → {h}  {'✅ 认了' if ok else '❌ 还是旧的'}")
        if ok:
            return label
    return None


def _ie4uinit():
    import subprocess
    try:
        subprocess.Popen(["ie4uinit.exe", "-show"],
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:
        pass


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    do_refresh = "--refresh" in sys.argv
    drives = args or ["D:\\", "C:\\"]
    print("=" * 70)
    print("壳层实际使用的图标（哈希相同 = 同一个图案）")
    print("=" * 70)
    for d in drives:
        d = d.rstrip("\\") + "\\"
        ico = os.path.join(d, "icon.ico")
        ini = os.path.join(d, "desktop.ini")
        drive_hash, err = shell_icon_hash(d)
        print(f"\n{d}")
        print(f"  驱动器图标   : {drive_hash or ('失败：' + err)}")
        print(f"  desktop.ini  : {'有' if os.path.exists(ini) else '无'}"
              f"   icon.ico : {'有' if os.path.exists(ico) else '无'}")
        if os.path.exists(ico):
            ico_hash, err2 = shell_icon_hash(ico)
            print(f"  icon.ico 图标: {ico_hash or ('失败：' + err2)}")
            matched = (drive_hash == ico_hash)
            print(f"  → 驱动器是否在用我们放的图标：{'是 ✅' if matched else '否 ❌'}")
            if do_refresh and not matched:
                print("  现在逐级刷新，看哪一步能让壳层认账：")
                hit = try_refresh_chain(d, ico_hash)
                print(f"  → 结论：{'【' + hit + '】有效' if hit else '所有刷新都无效（壳层就是不认这个 desktop.ini）'}")
    print("\n提示：若显示「否」，说明壳层没认 desktop.ini（要换做法）；")
    print("      若显示「是」但界面上还是旧图标，说明只是界面没刷新（要改刷新方式）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
