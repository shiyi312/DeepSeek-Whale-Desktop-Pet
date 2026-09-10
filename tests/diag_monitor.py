# -*- coding: utf-8 -*-
"""应用监控诊断：逐个场景复现"打开 Edge 没触发台词"的可能原因。"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication

import whale_pet as w

w.save_config = lambda cfg: None

RULE = {"match": "edge", "text": "上网敲代码了嘛~要注意身体哦", "chance": 100, "enabled": True}


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.app_monitor_enabled = True
    pet.bubble_on = True
    fired = []
    pet.show_bubble_quick = lambda t: fired.append(t)
    pet.app_rules = [dict(RULE)]
    pet._rule_fire_time = {}

    def scene(name, exe_title, times=1, reset_last=True):
        del fired[:]
        if reset_last:
            pet._last_fore_exe = ""
        for _ in range(times):
            pet._get_foreground_exe = lambda et=exe_title: et
            pet._monitor_tick()
        print(f"   {name}: 触发 {len(fired)} 次")
        return len(fired)

    print("【场景复现】")
    # 1) 后台切到 Edge（首次）
    scene("1. 从别的应用切到 Edge（首次）", ("msedge.exe", "Edge - 新建标签页"))

    # 2) 立刻再切一次（5 分钟冷却内）
    scene("2. 冷却期内再次切到 Edge", ("msedge.exe", "Edge"))

    print("   ↑ 若为 0 次，说明被 5 分钟冷却拦住了（这就是你遇到的）")

    # 3) 等冷却过去（把上次触发时间往前推 301 秒）
    pet._rule_fire_time = {0: time.monotonic() - 301}
    scene("3. 距上次触发超过 5 分钟后", ("msedge.exe", "Edge"))

    # 4) 一直停在 Edge（exe 未变化）
    scene("4. 停留在 Edge（前台未变化）", ("msedge.exe", "Edge"), reset_last=False)

    # 5) 规则列表变动导致冷却索引错位
    pet.app_rules = [{"match": "chrome", "text": "chrome 台词", "chance": 100, "enabled": True},
                     dict(RULE)]
    pet._rule_fire_time = {0: time.monotonic()}      # 旧索引 0 记过时间
    print("   5. 增删规则后冷却错位:", end=" ")
    del fired[:]
    pet._last_fore_exe = ""
    pet._get_foreground_exe = lambda: ("msedge.exe", "Edge")
    pet._monitor_tick()
    print(f"触发 {len(fired)} 次（规则被移到索引 1，冷却记录还挂在索引 0）")

    # 6) OpenProcess 拿不到进程名（权限/受保护进程）→ exe 为空
    print("   6. 拿不到进程名时:", end=" ")
    del fired[:]
    pet._last_fore_exe = ""
    pet._get_foreground_exe = lambda: ("", "Edge - 新建标签页")
    pet._monitor_tick()
    print(f"触发 {len(fired)} 次（exe 为空直接 return，标题完全不参与匹配）")

    # 7) 概率 100 的规则命中判定本身
    print("   7. 概率 100 判定:", all(pet._rule_chance_hit(RULE) for _ in range(50)), "(50 次全中)")

    # 8) 气泡开关/监控开关关闭时
    pet.bubble_on = False
    print("   8. 关闭气泡显示时触发:", scene("8. 气泡关闭", ("msedge.exe", "Edge")), "次（符合预期=0）")
    pet.bubble_on = True

    # 9) 多显示器/标题匹配（规则写 'Edge' 但 exe 是 msedge.exe）
    pet.app_rules = [{"match": "Edge", "text": "标题匹配", "chance": 100, "enabled": True}]
    pet._rule_fire_time = {}
    print("   9. 规则写 'Edge'（大写）匹配 msedge.exe:",
          scene("9. 大小写混合匹配", ("msedge.exe", "Edge - 新建标签页")), "次")

    app.quit()


if __name__ == "__main__":
    main()
