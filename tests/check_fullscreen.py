# -*- coding: utf-8 -*-
"""全屏判定专项：纯函数用例（桌面/任务栏/最大化/真全屏）+ 桌宠集成用例。

背景：旧判定是"窗口矩形盖住整屏即全屏"，于是
  ① 桌面（Progman/WorkerW）本身就铺满整屏 → 刷新桌面时桌宠被误隐藏且很久不恢复；
  ② 浏览器最大化时矩形同样等于整块显示器 → 打开浏览器桌宠就消失。
本脚本用假数据直接单测新的纯函数 is_fullscreen_window()，不依赖真实的前台窗口。

用法：python tests/check_fullscreen.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication

import whale_pet as w

w.save_config = lambda cfg: None

MON = (0, 0, 1920, 1080)            # 显示器矩形（含任务栏所占的那条）
WORK = (0, 0, 1920, 1040)           # 工作区矩形（不含 40px 任务栏）


def win(**kw):
    """构造一份窗口信息：默认是"别的进程、无边框、铺满显示器"的真全屏。"""
    info = {"visible": True, "minimized": False, "zoomed": False, "is_shell": False,
            "class_name": "UnityWndClass", "style": 0, "pid": 4242,
            "rect": MON, "monitor_rect": MON, "self_pid": 9999}
    info.update(kw)
    return info


CASES = [
    ("真全屏游戏（无边框铺满显示器）", win(), True),
    ("浏览器 F11 全屏（无边框、非最大化）", win(class_name="Chrome_WidgetWin_1"), True),
    ("无边框最大化的全屏（同样算全屏）", win(zoomed=True, style=0), True),
    ("桌面 Progman（铺满屏幕但不是全屏应用）", win(class_name="Progman", is_shell=True), False),
    ("桌面 WorkerW", win(class_name="WorkerW"), False),
    ("桌面子窗口 SHELLDLL_DefView", win(class_name="SHELLDLL_DefView"), False),
    ("任务栏 Shell_TrayWnd", win(class_name="Shell_TrayWnd", rect=(0, 1040, 1920, 1080)), False),
    ("Win11 任务视图 / Alt+Tab 浮层", win(class_name="XamlExplorerHostIslandWindow"), False),
    ("浏览器最大化（带标题栏 + 边框）", win(zoomed=True, style=0x00CF0000), False),
    ("普通窗口手动拉到铺满工作区（没盖住任务栏）", win(rect=WORK), False),
    ("半屏窗口（Win + 左）", win(rect=(0, 0, 960, 1080)), False),
    ("桌宠自己的窗口（同进程号）", win(pid=9999), False),
    ("最小化的全屏游戏", win(minimized=True), False),
    ("不可见窗口", win(visible=False), False),
    ("拿不到显示器信息（采集失败）", win(monitor_rect=None), False),
    ("拿不到窗口矩形（采集失败）", win(rect=None), False),
    ("前台窗口为空（采集失败）", None, False),
]

INTERSECT_CASES = [
    ("主屏桌宠 + 主屏全屏 → 重叠", (0, 0, 1920, 1080), (0, 0, 1920, 1080), True),
    ("主屏桌宠 + 右副屏全屏 → 不重叠", (0, 0, 1920, 1080), (1920, 0, 3840, 1080), False),
    ("主屏桌宠 + 上副屏全屏 → 不重叠", (0, 0, 1920, 1080), (0, -1080, 1920, 0), False),
    ("信息缺失 → 不重叠", (0, 0, 1920, 1080), None, False),
]


def main():
    app = QApplication(sys.argv)            # 集成用例需要 Qt
    ok = True

    print("=" * 56)
    print("一、纯函数用例 is_fullscreen_window()")
    print("=" * 56)
    for name, info, expect in CASES:
        got = w.is_fullscreen_window(info)
        if got != expect:
            ok = False
        print(f"[{'OK  ' if got == expect else 'FAIL'}] {name}：判定={got} 期望={expect}")

    print()
    print("=" * 56)
    print("二、同屏判定 rects_intersect()（副屏全屏不该藏主屏桌宠）")
    print("=" * 56)
    for name, a, b, expect in INTERSECT_CASES:
        got = w.rects_intersect(a, b)
        if got != expect:
            ok = False
        print(f"[{'OK  ' if got == expect else 'FAIL'}] {name}：判定={got} 期望={expect}")

    print()
    print("=" * 56)
    print("三、桌宠集成：前台是桌面时不隐藏、真全屏才隐藏")
    print("=" * 56)
    pet = w.PetWindow()
    pet.show()
    app.processEvents()
    pet.hide_in_fullscreen = True

    def tick(times=2):
        """防抖：连续两次判定才隐藏（恢复是立即的），这里统一多打几次。"""
        for _ in range(times):
            pet._fullscreen_tick()
        app.processEvents()

    real_probe = w.foreground_window_info
    try:
        w.foreground_window_info = lambda self_pid=None: win(class_name="Progman", is_shell=True)
        tick()
        if pet.isVisible():
            print("[OK  ] 前台是桌面（刷新桌面/点桌面）→ 桌宠保持显示")
        else:
            ok = False
            print("[FAIL] 前台是桌面时桌宠被隐藏（旧 bug 复现）")

        w.foreground_window_info = lambda self_pid=None: win(zoomed=True, style=0x00CF0000)
        tick()
        if pet.isVisible():
            print("[OK  ] 前台是最大化浏览器 → 桌宠保持显示")
        else:
            ok = False
            print("[FAIL] 最大化浏览器被误判为全屏，桌宠被隐藏")

        w.foreground_window_info = lambda self_pid=None: win()
        tick()
        if not pet.isVisible():
            print("[OK  ] 前台是真全屏应用 → 桌宠自动隐藏（不挡游戏画面）")
        else:
            ok = False
            print("[FAIL] 真全屏应用没有隐藏桌宠")

        w.foreground_window_info = lambda self_pid=None: win(class_name="Progman", is_shell=True)
        pet._fullscreen_tick()
        app.processEvents()
        if pet.isVisible():
            print("[OK  ] 退出全屏后立即恢复显示")
        else:
            ok = False
            print("[FAIL] 退出全屏后没有恢复显示")
    finally:
        w.foreground_window_info = real_probe

    print()
    print("=" * 56)
    print("四、真实环境自检（采集函数能正确读到当前前台窗口）")
    print("=" * 56)
    info = w.foreground_window_info(self_pid=os.getpid())
    if info is None:
        print("[WARN] 采集前台窗口失败（可能不在 Windows 桌面会话中）")
    else:
        keys = ("hwnd", "visible", "zoomed", "class_name", "style", "pid",
                "rect", "monitor_rect")
        missing = [k for k in keys if k not in info]
        if missing:
            ok = False
            print("[FAIL] 采集结果缺少字段：", missing)
        else:
            print(f"[OK  ] 当前前台窗口：class={info['class_name']!r} pid={info['pid']} "
                  f"rect={info['rect']} monitor={info['monitor_rect']} "
                  f"zoomed={info['zoomed']}")
            print(f"[OK  ] 判定结果：is_fullscreen={w.is_fullscreen_window(info)}")

    # 桌宠所在显示器矩形必须与窗口矩形同源（否则缩放屏/副屏偏移下同屏判定会错位）
    pet_rect = pet._screen_rect()
    win32_rect = w.win32_monitor_rect(int(pet.winId()))
    if win32_rect is None:
        print("[WARN] Win32 显示器矩形读取失败，已退回 QScreen 坐标")
    elif pet_rect == win32_rect:
        print(f"[OK  ] 桌宠所在显示器：{pet_rect}（与 Win32 坐标同源）")
    else:
        ok = False
        print(f"[FAIL] 桌宠显示器矩形与 Win32 不一致：{pet_rect} != {win32_rect}")

    print()
    print("=" * 56)
    print("五、隐藏/恢复时序（防抖 + 立即恢复 + 轮询间隔）")
    print("=" * 56)
    try:
        pet.hide_in_fullscreen = True
        pet.show()
        app.processEvents()

        w.foreground_window_info = lambda self_pid=None: win()      # 真全屏
        pet._fullscreen_tick()
        if pet.isVisible():
            print("[OK  ] 第 1 次判定为全屏：暂不隐藏（防抖，切换窗口不闪）")
        else:
            ok = False
            print("[FAIL] 防抖失效：第 1 次判定就隐藏了")

        pet._fullscreen_tick()
        if not pet.isVisible():
            print("[OK  ] 第 2 次判定为全屏：隐藏桌宠")
        else:
            ok = False
            print("[FAIL] 连续两次全屏仍未隐藏")

        w.foreground_window_info = lambda self_pid=None: win(zoomed=True, style=0x00CF0000)
        pet._fullscreen_tick()                                      # 恢复只需要 1 次
        app.processEvents()
        if pet.isVisible():
            print("[OK  ] 切回最大化浏览器：立即恢复显示（无防抖延迟）")
        else:
            ok = False
            print("[FAIL] 退出全屏后没有立即恢复")

        w.foreground_window_info = lambda self_pid=None: win()
        pet._fullscreen_tick()
        pet._fullscreen_tick()
        pet.hide_in_fullscreen = False                              # 隐藏着关掉开关
        pet._fullscreen_tick()
        app.processEvents()
        if pet.isVisible():
            print("[OK  ] 隐藏期间关闭「全屏时自动隐藏」：立刻恢复显示")
        else:
            ok = False
            print("[FAIL] 关掉开关后桌宠仍被隐藏（会一直不出现）")
        pet.hide_in_fullscreen = True

        if pet._fg_timer.isActive() and pet._fg_timer.interval() == w.FG_POLL_MS:
            print(f"[OK  ] 前台轮询间隔 {w.FG_POLL_MS}ms"
                  f"（退出全屏后 ≤{w.FG_POLL_MS / 1000:.2f}s 恢复）")
        else:
            ok = False
            print(f"[FAIL] 前台轮询定时器异常：interval={pet._fg_timer.interval()}")
    finally:
        w.foreground_window_info = real_probe
        pet.hide_in_fullscreen = True

    app.quit()
    print()
    print("全屏判定专项结果:", "通过" if ok else "有失败用例")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
