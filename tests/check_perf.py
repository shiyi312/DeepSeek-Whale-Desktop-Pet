# -*- coding: utf-8 -*-
"""性能专项：静止降频 / 全屏隐藏暂停定时器 / 进程名按 PID 缓存 / 镜像位图缓存。

用法：python tests/check_perf.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

import whale_pet as w

w.save_config = lambda cfg: None


def main():
    app = QApplication(sys.argv)
    ok = True
    pet = w.PetWindow()
    pet.show()
    app.processEvents()

    def check(name, cond, extra=""):
        nonlocal ok
        if cond:
            print(f"[OK  ] {name}{extra}")
        else:
            ok = False
            print(f"[FAIL] {name}{extra}")

    # 1) 静止时移动节拍自动降到 10fps，开启跟随/漫游立刻回到 60fps
    pet.follow_mode = pet.evade_mode = pet.wander_mode = False
    pet._sling_active = pet._r_dragging = pet._dragging = False
    pet._drag_hold = False
    pet._wander_on = False
    pet._reset_move_timer()
    check("静止时移动节拍降频", pet._move_timer.interval() == w.MOVE_MS_IDLE,
          f"（{pet._move_timer.interval()}ms）")

    pet.set_follow_mode(True)
    check("开启跟随 → 立刻 60fps", pet._move_timer.interval() == w.MOVE_MS_ACTIVE,
          f"（{pet._move_timer.interval()}ms）")
    pet.set_follow_mode(False)
    check("关闭跟随 → 回到静止节拍", pet._move_timer.interval() == w.MOVE_MS_IDLE,
          f"（{pet._move_timer.interval()}ms）")

    pet.set_wander_mode(True)
    check("开启漫游 → 立刻 60fps", pet._move_timer.interval() == w.MOVE_MS_ACTIVE)
    pet.set_wander_mode(False)
    pet._reset_move_timer()

    # 2) 静止时一次 tick 的开销（1000 次应远低于 0.5s）
    t0 = time.perf_counter()
    for _ in range(1000):
        pet._move_tick()
    cost = time.perf_counter() - t0
    check("静止 tick 开销", cost < 0.5, f"（1000 次 {cost * 1000:.1f}ms）")

    # 3) 全屏隐藏期间暂停重定时器，恢复后重新启动
    #    （把前台探测打桩成"真全屏"，否则下一次 tick 会判定已退出全屏而立刻恢复）
    real_probe = w.foreground_window_info
    w.foreground_window_info = lambda self_pid=None: {
        "visible": True, "minimized": False, "zoomed": False, "is_shell": False,
        "class_name": "UnityWndClass", "style": 0, "pid": 1,
        "rect": (0, 0, 1920, 1080), "monitor_rect": (0, 0, 1920, 1080)}
    try:
        pet._hide_for_fullscreen()
        app.processEvents()
        running = [t.isActive() for t in (pet._hud_timer, pet._move_timer,
                                          pet._blink_timer, pet._auto_rotate_timer)]
        check("全屏隐藏 → HUD/移动/眨眼/轮换全部暂停", not any(running), f"（{running}）")
        check("全屏隐藏期间前台轮询仍在跑（否则无法自动恢复）", pet._fg_timer.isActive())

        pet._restore_from_fullscreen("性能测试")
        app.processEvents()
        resumed = [pet._hud_timer.isActive(), pet._move_timer.isActive(),
                   pet._blink_timer.isActive(), pet._auto_rotate_timer.isActive()]
        # 眨眼/自动轮换是配置项，关掉时本就不该启动，按配置推导期望值
        expected = [True, True, pet.blink_enabled, pet.auto_rotate]
        check("退出全屏 → 定时器按配置恢复", resumed == expected,
              f"（实际 {resumed} / 期望 {expected}；配置 blink={pet.blink_enabled} "
              f"rotate={pet.auto_rotate}）")
    finally:
        w.foreground_window_info = real_probe

    # 4) 进程名按 PID 缓存：第二次不再查系统
    calls = {"n": 0}
    real_win32 = w._win32

    def counting_win32():
        calls["n"] += 1
        return real_win32()

    w._win32 = counting_win32
    try:
        pet._exe_by_pid.clear()
        pet._exe_name_of(999999)            # 不存在的进程号：OpenProcess 会失败，同样算一次查询
        first = calls["n"]
        pet._exe_name_of(999999)
        second = calls["n"]
        check("同进程只查一次（缓存生效）", second == first,
              f"（首次查询 {first} 次，二次 {second - first} 次）")
        check("当前进程能取到 exe 名", pet._exe_name_of(os.getpid()).endswith(".exe"),
              f"（{pet._exe_name_of(os.getpid())}）")
        exe, title = pet._get_foreground_exe()
        check("前台窗口进程名/标题查询正常",
              isinstance(exe, str) and isinstance(title, str)
              and (not exe or exe in pet._exe_by_pid.values()),
              f"（exe={exe!r} title={title[:24]!r}）")
    finally:
        w._win32 = real_win32

    # 5) 贴左边时的镜像位图缓存：同一张图只翻转一次
    geo = app.primaryScreen().availableGeometry()
    pet.auto_mirror = True
    pet.move(geo.left(), geo.top() + 100)   # 贴左边缘 → 触发镜像
    app.processEvents()
    pix = QPixmap(16, 16)
    a = pet._mirror_pixmap(pix)
    b = pet._mirror_pixmap(pix)
    check("镜像位图命中缓存（同一对象）", a is b)
    other = QPixmap(20, 20)
    check("换图后缓存自动失效", pet._mirror_pixmap(other) is not a)

    # 6) 设置面板关掉后不再空转 150ms 悬停轮询
    panel = w.SettingsPanel(pet)
    pet.settings_panel = panel
    panel.show()
    app.processEvents()
    check("设置面板打开 → 悬停轮询运行", panel._hover_timer.isActive())
    panel.close()
    app.processEvents()
    check("设置面板关闭 → 悬停轮询停止（不再后台空转）", not panel._hover_timer.isActive())

    app.quit()
    print()
    print("性能专项结果:", "通过" if ok else "有失败用例")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
