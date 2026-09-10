# -*- coding: utf-8 -*-
"""气泡边界自测：贴屏幕四边时气泡必须完整可见（不被边缘截断）。

用法：python tests/check_bubble.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect

import whale_pet as w

w.save_config = lambda cfg: None


def in_screen(rect, geo):
    return geo.contains(rect)


def main():
    app = QApplication(sys.argv)
    geo = app.primaryScreen().availableGeometry()
    pet = w.PetWindow()
    pet.show()
    app.processEvents()

    long_line = "这是一条很长的台词，用来验证贴边时气泡不会被屏幕边缘截断掉一半啊"
    cases = [
        ("贴右边缘", geo.right() - pet.width(), geo.top() + 300),
        ("贴左边缘", geo.left(), geo.top() + 300),
        ("贴右下角", geo.right() - pet.width(), geo.bottom() - pet.height()),
        ("贴顶部", geo.center().x(), geo.top()),
        ("屏幕正中", geo.center().x() - pet.width() // 2, geo.center().y()),
    ]
    for name, x, y in cases:
        pet.move(int(x), int(y))
        app.processEvents()
        pet.bubble.show_lines([long_line], 4000, pet=pet)
        app.processEvents()
        time.sleep(0.12)
        app.processEvents()
        r = QRect(pet.bubble.x(), pet.bubble.y(), pet.bubble.width(), pet.bubble.height())
        assert in_screen(r, geo), (f"{name} 时气泡超出屏幕（会被截断）", r, geo)
        # 同步位置后再验证一次（拖动/移动过程中的路径）
        pet.sync_bubble_position()
        r2 = QRect(pet.bubble.x(), pet.bubble.y(), pet.bubble.width(), pet.bubble.height())
        assert in_screen(r2, geo), (f"{name} 移动后气泡超出屏幕", r2, geo)
        pet.bubble.hide()
        app.processEvents()
    print(f"1. 贴四边气泡完整可见 OK（{len(cases)} 个位置 × 显示+移动两次检查）")

    # 2) 气泡在角色上方（有空间时）
    pet.move(geo.center().x(), geo.center().y())
    app.processEvents()
    pet.bubble.show_lines(["测试"], 3000, pet=pet)
    app.processEvents()
    assert pet.bubble.y() < pet.y(), "屏幕中间时气泡应显示在角色上方"
    print("2. 气泡默认在角色上方 OK")
    pet.bubble.hide()

    # 3) 角色贴顶时气泡自动落到下方
    pet.move(geo.center().x(), geo.top())
    app.processEvents()
    pet.bubble.show_lines(["测试贴顶"], 3000, pet=pet)
    app.processEvents()
    assert pet.bubble.y() > pet.y(), ("贴顶时气泡应在下方", pet.bubble.y(), pet.y())
    print("3. 贴顶时气泡自动落到下方 OK")
    pet.bubble.hide()

    app.quit()
    print()
    print("气泡边界自测结果: 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
