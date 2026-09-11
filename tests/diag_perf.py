# -*- coding: utf-8 -*-
"""性能诊断：对本次优化的热点做微观基准（不是断言，是给数字）。

用法：python tests/diag_perf.py
"""
import ctypes
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtWidgets import QApplication

import whale_pet as w

w.save_config = lambda cfg: None
N = 200


def bench(label, fn, n=N):
    fn()                                 # 预热
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    dt = time.perf_counter() - t0
    print(f"{label:<38} {dt * 1000 / n:8.3f} ms/次   （{n} 次共 {dt * 1000:.1f} ms）")
    return dt / n


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.show()
    app.processEvents()

    print("=" * 74)
    print("1. 贴左边缘移动时的镜像位图（优化前每帧翻转，优化后命中缓存）")
    print("=" * 74)
    geo = app.primaryScreen().availableGeometry()
    pet.auto_mirror = True
    pet.move(geo.left(), geo.top() + 100)          # 贴左边缘 → 每帧都要镜像
    app.processEvents()
    pix = QPixmap(550, 550)                        # size_level 20 的位图尺寸
    t_raw = bench("直接 transformed（旧行为）", lambda: pix.transformed(QTransform().scale(-1, 1)))
    t_cached = bench("_mirror_pixmap（新：命中缓存）", lambda: pet._mirror_pixmap(pix))
    saved = (t_raw - t_cached) * 60
    print(f"→ 60fps 移动时每秒省下 {saved * 1000:.1f} ms CPU"
          f"（约 {saved * 100:.2f}% 单核）")

    print()
    print("=" * 74)
    print("2. 应用监控取前台进程名（优化前每秒 OpenProcess，优化后按 PID 缓存）")
    print("=" * 74)
    api = w._win32()
    kernel32, user32, wt = api["kernel32"], api["user32"], api["wt"]
    pid = os.getpid()

    def raw_query():
        h = kernel32.OpenProcess(0x1000, False, pid)
        if h:
            try:
                size = wt.DWORD(512)
                buf = ctypes.create_unicode_buffer(size.value)
                kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size))
            finally:
                kernel32.CloseHandle(h)

    t_open = bench("OpenProcess + 取路径（旧行为）", raw_query)
    pet._exe_by_pid.clear()
    pet._exe_name_of(pid)
    t_hit = bench("_exe_name_of（新：命中缓存）", lambda: pet._exe_name_of(pid))
    print(f"→ 每秒一次应用监控：省下 {(t_open - t_hit) * 1000:.3f} ms/秒")

    print()
    print("=" * 74)
    print("3. 空闲时的移动节拍（旧 16ms=60 次/秒 空转 → 新 100ms=10 次/秒）")
    print("=" * 74)
    pet.follow_mode = pet.evade_mode = pet.wander_mode = False
    pet._sling_active = pet._r_dragging = pet._dragging = False
    pet._wander_on = False
    pet._reset_move_timer()
    t_tick = bench("静止时一次 _move_tick()", pet._move_tick, 1000)
    print(f"→ 旧：60 次/秒 = {t_tick * 60 * 1000:.3f} ms/秒；"
          f"新：10 次/秒 = {t_tick * 10 * 1000:.3f} ms/秒")

    print()
    print("=" * 74)
    print("4. 全屏隐藏期间（旧：所有定时器照跑 → 新：HUD/移动/眨眼/轮换全停）")
    print("=" * 74)
    t_hud = bench("一次 HUD 刷新（每秒 1 次）", pet._update_hud, 100)
    real_probe = w.foreground_window_info
    w.foreground_window_info = lambda self_pid=None: {
        "visible": True, "minimized": False, "zoomed": False, "is_shell": False,
        "class_name": "UnityWndClass", "style": 0, "pid": 1,
        "rect": (0, 0, 1920, 1080), "monitor_rect": (0, 0, 1920, 1080)}
    try:
        pet._hide_for_fullscreen()
        app.processEvents()
        stopped = [t.isActive() for t in (pet._hud_timer, pet._move_timer,
                                          pet._blink_timer, pet._auto_rotate_timer)]
        print(f"隐藏后定时器状态（应为全 False）：{stopped}")
        print(f"→ 旧：全屏玩游戏时每秒仍烧 {t_hud * 1000:.3f} ms 刷 HUD + 移动空转；新：0")
        pet._restore_from_fullscreen("诊断结束")
    finally:
        w.foreground_window_info = real_probe
    app.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
