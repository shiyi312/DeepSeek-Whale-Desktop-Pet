# -*- coding: utf-8 -*-
"""自测：应用监控规则路径不再崩溃 / 回调异常被记录不退出 / 日志按时长与份数清理。"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication

import whale_pet as w

w.save_config = lambda cfg: None


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.show()
    app.processEvents()

    # 1) 规则命中路径（就是导致崩溃的那条）：不应抛异常，且要触发台词
    pet.app_monitor_enabled = True
    pet.bubble_on = True
    pet.app_rules = [{"match": "edge", "text": "上网敲代码了嘛~要注意身体哦", "chance": 100, "enabled": True}]
    pet._rule_fire_time = {}
    pet._last_fore_exe = ""
    pet._get_foreground_exe = lambda: ("msedge.exe", "Edge 浏览器")
    fired = {"n": 0}
    pet.show_bubble_quick = lambda text: fired.__setitem__("n", fired["n"] + 1)
    pet._monitor_tick()                     # 直接跑，修复前这里必然 NameError
    assert fired["n"] == 1, ("监控未触发台词", fired)
    print("1. 规则命中不再崩溃 OK（已触发台词 1 次）")

    # 2) 冷却：5 分钟内不重复触发，且不抛异常
    pet._last_fore_exe = ""
    pet._monitor_tick()
    assert fired["n"] == 1, ("冷却失效", fired)
    print("2. 冷却逻辑 OK（未重复触发）")

    # 3) 概率 0 的规则与坏规则不应导致异常
    pet.app_rules = [{"match": "edge", "text": "x", "chance": 0, "enabled": True},
                     {"match": "", "text": "", "enabled": True},
                     "坏数据"]
    pet._last_fore_exe = ""
    pet._rule_fire_time = {}
    pet._monitor_tick()
    pet.app_rules = [{"match": "edge", "text": "y", "chance": 100, "enabled": False}]
    pet._last_fore_exe = ""
    pet._monitor_tick()
    print("3. 异常规则数据安全 OK")

    # 4) 回调异常被 _guard 捕获并写日志（进程不退出）
    tmp = tempfile.mkdtemp()
    old_log = w.LOG_PATH
    w.LOG_PATH = os.path.join(tmp, "t.log")
    try:
        def boom():
            raise RuntimeError("模拟回调崩溃")
        pet._guard("测试回调", boom)()
        text = open(w.LOG_PATH, encoding="utf-8").read()
        assert "[异常] 测试回调" in text and "模拟回调崩溃" in text, text[:200]
    finally:
        w.LOG_PATH = old_log
    print("4. 回调异常被记录、进程存活 OK")

    # 5) 日志清理：超期删除 + 超量删除
    tmp2 = tempfile.mkdtemp()
    old_log, old_keep, old_days = w.LOG_PATH, w.LOG_KEEP, w.LOG_KEEP_DAYS
    w.LOG_PATH = os.path.join(tmp2, "dshw-pet.log")
    w.LOG_KEEP = 3
    w.LOG_KEEP_DAYS = 7
    try:
        base, ext = os.path.splitext(w.LOG_PATH)
        now = time.time()
        # 2 个超期（10 天前）+ 5 个新鲜
        for i, age_days in enumerate([10, 9, 0.1, 0.2, 0.3, 0.4, 0.5]):
            p = f"{base}_2026010{i}_00000{i}{ext}"
            with open(p, "w", encoding="utf-8") as f:
                f.write("x")
            os.utime(p, (now - age_days * 86400, now - age_days * 86400))
        with open(w.LOG_PATH, "w", encoding="utf-8") as f:
            f.write("cur")
        w.rotate_log_if_needed()
        import glob
        left = sorted(glob.glob(f"{base}_*{ext}"))
        assert len(left) <= 3, ("份数上限未生效", len(left))
        for p in left:
            assert now - os.path.getmtime(p) < 7 * 86400, ("超期日志未清理", p)
    finally:
        w.LOG_PATH, w.LOG_KEEP, w.LOG_KEEP_DAYS = old_log, old_keep, old_days
    print("5. 日志自动清理 OK（超 7 天 + 超 3 份已删）")

    app.quit()
    print("ALL OK")


if __name__ == "__main__":
    main()
