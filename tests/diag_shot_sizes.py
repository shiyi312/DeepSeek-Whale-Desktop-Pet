# -*- coding: utf-8 -*-
"""抓图：桌宠 + HUD（确认尺寸恢复小巧、贴边正确）与面板观感。"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication

import whale_pet as w

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "_shots")
os.makedirs(OUT, exist_ok=True)
w.save_config = lambda cfg: None


def settle(app, sec=0.4):
    end = time.time() + sec
    while time.time() < end:
        app.processEvents()


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.move(300, 300)
    pet.show()
    settle(app)
    pet.grab().save(os.path.join(OUT, "pet_hud.png"))
    print("桌宠窗口:", pet.width(), "x", pet.height(), "| 角色:", pet.size_px, "| HUD:", pet.hud_card.width(), "x", pet.hud_card.height(), "| 字号:", pet._hud_font_px())
    panel = w.SettingsPanel(pet)
    pet.settings_panel = panel
    panel.move(80, 40)
    panel.show()
    settle(app)
    panel.tabs.setCurrentIndex(1)
    settle(app)
    panel.grab().save(os.path.join(OUT, "panel_token.png"))
    print("面板:", panel.width(), "x", panel.height())
    app.quit()
    print("DONE")


if __name__ == "__main__":
    main()
