# -*- coding: utf-8 -*-
"""启动性能与启动瞬间朝向自测。"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication

import whale_pet as w

w.save_config = lambda cfg: None

BASE_CFG = {"size_level": 10, "expression": "DSniang1", "volume": 20, "sound_mode": "duck",
            "token": 1000, "token_enabled": True, "bubble_on": True, "auto_rotate": True,
            "blink_enabled": True, "app_monitor_enabled": True, "hud_visible": True}


def timeit(label, fn):
    t0 = time.monotonic()
    r = fn()
    ms = (time.monotonic() - t0) * 1000
    print(f"   {label}: {ms:.0f} ms")
    return r, ms


def main():
    app = QApplication(sys.argv)

    # 分段测量
    print("[分段耗时]")
    _, t_scan = timeit("scan_expressions", w.scan_expressions)
    _, t_sounds = timeit("scan_sounds", w.scan_sounds)

    t0 = time.monotonic()
    pet = w.PetWindow()
    init_ms = (time.monotonic() - t0) * 1000
    print(f"   PetWindow.__init__ 合计: {init_ms:.0f} ms")
    t0 = time.monotonic()
    pet.show()
    app.processEvents()
    show_ms = (time.monotonic() - t0) * 1000
    print(f"   show() + 首帧: {show_ms:.0f} ms")
    print(f"   → 启动到可见合计: {init_ms + show_ms:.0f} ms")
    assert init_ms < 1500, ("初始化过慢", init_ms)

    # 音效预加载已延后，启动后 1 秒内应完成
    time.sleep(0.9)
    app.processEvents()
    loaded = [getattr(p, "_dsh_path", "") for p in pet._sfx_pool]
    assert any(loaded), ("音效未预加载", loaded)
    print("1. 音效延迟预加载 OK（启动不被阻塞，稍后自动加载）")

    # 启动瞬间朝向：把位置放在贴左边缘，新建实例后应立即是翻转状态
    w.load_config = lambda: dict(BASE_CFG, x=0, y=400)
    t0 = time.monotonic()
    left_pet = w.PetWindow()
    ms = (time.monotonic() - t0) * 1000
    left_pet.move(0, 400)
    assert left_pet._near_left_edge(), "位置未判定为贴左边缘"
    shown = left_pet.label.pixmap().toImage()
    expect = left_pet._mirror_pixmap(left_pet._base_pixmap).toImage()
    assert shown == expect, "启动瞬间未翻转（贴左边缘却是正向贴图）"
    print(f"2. 启动瞬间翻转 OK（贴左边缘→立即镜像，初始化 {ms:.0f} ms）")

    # 右侧位置应为正常朝向
    w.load_config = lambda: dict(BASE_CFG, x=1200, y=400)
    right_pet = w.PetWindow()
    right_pet.move(1200, 400)
    assert not right_pet._near_left_edge()
    assert right_pet.label.pixmap().toImage() == right_pet._base_pixmap.toImage(), "右侧不该翻转"
    print("3. 非贴边位置朝向正常 OK")

    # 启动耗时日志已写入
    log = open(w.LOG_PATH, encoding="utf-8", errors="replace").read()
    assert "启动完成" in log, "启动耗时应写入日志"
    print("4. 启动耗时写入日志 OK")

    app.quit()
    print("ALL OK")


if __name__ == "__main__":
    main()
