# -*- coding: utf-8 -*-
"""诊断：气泡圆点方向在多种角色位置下是否正确 + 磁盘图标覆盖已存在文件的行为。"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication

import whale_pet as w

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "_shots")
os.makedirs(OUT, exist_ok=True)
w.save_config = lambda cfg: None


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.show()
    app.processEvents()
    geo = app.primaryScreen().availableGeometry()

    print("=== 气泡方向（圆点在角色上方时 tail_up 应为 True）===")
    cases = [
        ("贴顶", geo.center().x(), geo.top()),
        ("偏上1/5", geo.center().x(), geo.top() + geo.height() // 5),
        ("中间", geo.center().x(), geo.center().y()),
        ("偏下", geo.center().x(), geo.bottom() - pet.height() - 20),
    ]
    for name, x, y in cases:
        pet.move(int(x), int(y))
        app.processEvents()
        pet.bubble.show_lines(["方向测试台词一行", "第二行示例"], 4000, pet=pet)
        end = time.time() + 0.4
        while time.time() < end:
            app.processEvents()
        above = pet.bubble.y() + pet.bubble.height() <= pet.y()
        below = pet.bubble.y() >= pet.y() + pet.height()
        print(f"  {name}: 气泡{'在角色上方' if above else '在角色下方' if below else '与角色重叠'} "
              f"| 圆点朝{'上' if pet.bubble.tail_up else '下'} | 期望朝{'上' if below else '下'}")
        pet.bubble.grab().save(os.path.join(OUT, f"dir_{name}.png"))
        pet.bubble.hide()
        app.processEvents()

    print()
    print("=== 磁盘图标：重复应用（文件已存在且带隐藏/系统属性）===")
    png = os.path.join(w.EXPR_DIR, "v1_fatfish.png")
    tmp_dir = tempfile.mkdtemp()
    tmp_ico = os.path.join(tempfile.gettempdir(), "dshw_fish.ico")
    ok, reason = w.build_fish_ico(png, tmp_ico)
    print(f"  生成 ICO: {ok} {reason}")
    ok1, r1 = w.apply_drive_icon(tmp_dir + "\\", tmp_ico)
    print(f"  第 1 次应用: ok={ok1} reason={r1!r}")
    ok2, r2 = w.apply_drive_icon(tmp_dir + "\\", tmp_ico)
    print(f"  第 2 次应用: ok={ok2} reason={r2!r}  ← 若失败说明重复应用有 bug")
    ok3, r3 = w.remove_drive_icon(tmp_dir + "\\")
    print(f"  恢复: ok={ok3} {r3!r}")
    app.quit()
    print("DONE")


if __name__ == "__main__":
    main()
