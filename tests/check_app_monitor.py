# -*- coding: utf-8 -*-
"""应用监控行为自测：冷却可调（默认每次触发）/ 标题兜底 / 冷却按规则内容 /
规则文件自动重载 / 未弹时写日志 / 停留不刷屏。

用法：python tests/check_app_monitor.py
"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication

import whale_pet as w

w.save_config = lambda cfg: None

RULE = {"match": "edge", "text": "上网敲代码了嘛~", "chance": 100, "enabled": True}


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    fired = []
    logs = []
    pet.show_bubble_quick = lambda t: fired.append(t)
    orig_log = pet._log
    pet._log = lambda m: (logs.append(str(m)), orig_log(m))[1]
    pet.app_monitor_enabled = True
    pet.bubble_on = True
    pet.app_rules = [dict(RULE)]
    pet._rule_fire_time = {}

    def switch_to(ident):
        pet._last_fore_exe = ""
        pet._get_foreground_exe = lambda i=ident: i
        pet._monitor_tick()

    # 1) 默认冷却 0 → 反复切到 Edge 每次都触发
    assert pet.app_rule_cooldown == 0, pet.app_rule_cooldown
    del fired[:]
    for _ in range(5):
        switch_to(("msedge.exe", "Edge - 新建标签页"))
    assert len(fired) == 5, ("冷却 0 时应每次都触发", len(fired))
    print("1. 触发冷却默认 0 秒 → 连续 5 次切换全部触发 OK")

    # 2) 冷却设为 60 秒 → 冷却期内只触发一次，并写日志说明
    pet.set_app_rule_cooldown(60)
    pet._rule_fire_time = {}
    del fired[:]
    logs.clear()
    for _ in range(3):
        switch_to(("msedge.exe", "Edge"))
    assert len(fired) == 1, ("冷却 60 秒内应只 1 次", len(fired))
    assert any("冷却中" in l for l in logs), "冷却应写日志说明"
    print("2. 冷却可调 OK（60 秒内只 1 次，并写日志说明）")

    # 3) 冷却按规则内容记录：增删规则后不错位
    pet.app_rules = [{"match": "chrome", "text": "chrome", "chance": 100, "enabled": True},
                     dict(RULE)]
    pet._rule_fire_time = {pet._rule_key(dict(RULE)): time.monotonic() - 10}
    del fired[:]
    switch_to(("msedge.exe", "Edge"))       # 规则被挪到索引 1，内容键仍命中冷却
    assert len(fired) == 0, ("内容键冷却失效", len(fired))
    print("3. 冷却按规则内容记录 OK（增删规则不错位）")

    # 4) 进程名取不到时用窗口标题兜底
    pet.set_app_rule_cooldown(0)
    pet.app_rules = [dict(RULE)]
    pet._rule_fire_time = {}
    del fired[:]
    logs.clear()
    switch_to(("", "Edge - 新建标签页"))
    assert len(fired) == 1, ("标题兜底未触发", len(fired))
    assert any("仅标题匹配" in l for l in logs), "应记录仅标题匹配"
    print("4. 进程名取不到时按窗口标题匹配 OK")

    # 5) 气泡关闭时写日志（不再静默）
    pet.bubble_on = False
    pet._rule_fire_time = {}
    del fired[:]
    logs.clear()
    switch_to(("msedge.exe", "Edge"))
    assert len(fired) == 0 and any("气泡显示已关闭" in l for l in logs)
    pet.bubble_on = True
    print("5. 气泡关闭时写日志说明 OK（可自查原因）")

    # 6) 概率未命中写日志
    pet._rule_fire_time = {}
    pet.app_rules = [dict(RULE, chance=0)]
    del fired[:]
    logs.clear()
    switch_to(("msedge.exe", "Edge"))
    assert len(fired) == 0 and any("概率未命中" in l for l in logs)
    print("6. 概率未命中写日志 OK")

    # 7) 规则文件改动自动重载
    tmp = tempfile.mkdtemp()
    old_rules_path = w.RULES_PATH
    w.RULES_PATH = os.path.join(tmp, "rules.txt")
    try:
        with open(w.RULES_PATH, "w", encoding="utf-8") as f:
            f.write("notepad | 打开记事本啦 | 100 | 1\n")
        pet._rules_mtime = 0.0
        pet._last_rules_check = 0.0
        pet.app_rules = [dict(RULE)]
        pet._maybe_reload_rules()
        assert any(r.get("match") == "notepad" for r in pet.app_rules), pet.app_rules
        print("7. 规则文件改动自动重载 OK（无需手动点按钮）")
    finally:
        w.RULES_PATH = old_rules_path

    # 8) 停留在同一应用不重复刷屏
    pet.set_app_rule_cooldown(0)
    pet.app_rules = [dict(RULE)]
    pet._rule_fire_time = {}
    del fired[:]
    pet._last_fore_exe = ""
    pet._get_foreground_exe = lambda: ("msedge.exe", "Edge")
    for _ in range(3):
        pet._monitor_tick()
    assert len(fired) == 1, ("同一应用停留应只触发一次", len(fired))
    print("8. 停留在同一应用不重复刷屏 OK")

    pet._log = orig_log
    app.quit()
    print()
    print("应用监控行为自测结果: 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
