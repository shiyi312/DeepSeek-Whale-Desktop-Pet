# -*- coding: utf-8 -*-
"""回归专项：桌宠可见性 / 面板尺寸 / 拖动保护 / 漫游卡住。

用法：python tests/check_regression.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect

import whale_pet as w

w.save_config = lambda cfg: None

BASE = {"size_level": 10, "expression": "DSniang1", "volume": 20, "sound_mode": "duck",
        "token": 1000, "token_enabled": True, "bubble_on": True, "wander_mode": False,
        "follow_mode": False, "evade_mode": False}


def main():
    app = QApplication(sys.argv)
    geo = app.primaryScreen().availableGeometry()

    # 1) 配置坐标在屏幕外（换分辨率/缩放后的旧坐标）→ 启动后桌宠必须可见
    w.load_config = lambda: dict(BASE, x=99999, y=99999)
    pet = w.PetWindow()
    pet.show()
    app.processEvents()
    rect = QRect(pet.x(), pet.y(), pet.width(), pet.height())
    inter = rect.intersected(geo)
    area = max(0, inter.width()) * max(0, inter.height())
    assert area >= rect.width() * rect.height() * 0.35, \
        ("桌宠启动后不可见！", (pet.x(), pet.y()), geo)
    print(f"1. 屏幕外坐标兜底 OK（重定位到 {pet.x()},{pet.y()}，可见面积充足）")

    # 2) 面板尺寸受控（不会占满屏幕）
    panel = w.SettingsPanel(pet)
    pet.settings_panel = panel
    panel.show()
    end = time.time() + 0.4
    while time.time() < end:
        app.processEvents()
    content_w = panel.card.minimumSizeHint().width() + 40
    assert panel.width() <= max(content_w, int(geo.width() * 0.34)), \
        ("面板过宽", panel.width(), geo.width())
    assert panel.height() <= max(400, int(geo.height() * 0.94)), \
        ("面板过高（占了整屏）", panel.height(), geo.height())
    print(f"2. 面板尺寸受控 OK（{panel.width()}x{panel.height()}，屏 {geo.width()}x{geo.height()}）")

    # 3) 拖动保护：拖动时自动移动必须停止（否则和拖动抢位置 → 平移/抖动/重影）
    pet.settings_panel.close()
    app.processEvents()
    pet._dragging = True
    before = pet._center()
    for _ in range(40):
        pet._move_tick()
    assert pet._center() == before, ("拖动时仍在自动移动", before, pet._center())
    pet._dragging = False
    print("3. 拖动时自动移动已让位 OK（不再抢位置）")

    # 4) 拖动期间 HUD 布局冻结（窗口尺寸不变 → 不抖动/重影）
    h_before = pet.height()
    pet._drag_hold = True
    pet._shown_token += 123456
    pet._update_hud()
    assert pet.height() == h_before, ("拖动中窗口尺寸变化了", h_before, pet.height())
    pet._drag_hold = False
    pet._update_hud()
    print("4. 拖动中 HUD 布局冻结 OK（窗口尺寸稳定）")

    # 5) 漫游卡住检测：贴边无法移动时应结束该段并换方向
    pet.wander_mode = True
    pet._last_interact = 0
    pet._wander_tick(1 / 60.0)
    pet._wander_mode_state = "move"
    pet._wander_delay = 30.0
    pet._wander_speed = 120.0
    pet._wander_stuck = 0
    pet.move(geo.left() - pet.width() + 10, geo.top())     # 极端贴边，移动会被限制
    for _ in range(30):
        pet._wander_tick(1 / 60.0)
    stuck_handled = (pet._wander_mode_state == "stop") or (pet._wander_stuck == 0)
    assert stuck_handled, ("漫游卡住未处理（会原地鬼畜）", pet._wander_stuck, pet._wander_mode_state)
    print("5. 漫游卡住检测 OK（贴边卡住会休息并换方向）")

    app.quit()
    print()
    print("回归专项结果: 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
