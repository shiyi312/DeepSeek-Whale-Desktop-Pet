# -*- coding: utf-8 -*-
"""HUD 显示自测：Token 与时间互不绑定、日期/星期、字号随角色放大、点击不误触。

用法：python tests/check_hud.py
"""
import os
import sys
import re
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication

import whale_pet as w

w.save_config = lambda cfg: None


def hud_text(pet):
    """把 HUD 各行拼成文本，便于断言。"""
    return "　".join("".join(t for t, _ in row) for row in pet.hud_card._rows())


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.show()
    app.processEvents()

    # 1) 默认：Token + 日期 + 星期 + 时间
    pet.hud_show_token = pet.hud_show_time = pet.hud_show_date = True
    pet.token_enabled = True
    pet._shown_token = 4851838
    pet._update_hud()
    text = hud_text(pet)
    assert "Token" in text, text
    assert re.search(r"\d{4}-\d{2}-\d{2} 周[一二三四五六日]", text), text
    assert re.search(r"\d{2}:\d{2}:\d{2}", text), text
    rows = pet.hud_card._rows()
    assert len(rows) == 2, ("Token 与时间应分成两行显示", rows)
    assert "Token" in "".join(t for t, _ in rows[0]), rows[0]
    assert re.search(r"\d{2}:\d{2}:\d{2}", "".join(t for t, _ in rows[1])), rows[1]
    print(f"1. 默认显示 OK（两行）→ {text}")

    # 2) 只显示时间（关掉 Token）——时间与 Token 不绑定
    pet.set_hud_show_token(False)
    text = hud_text(pet)
    assert "Token" not in text and re.search(r"\d{2}:\d{2}:\d{2}", text), text
    print(f"2. 只显示时间 OK → {text}")

    # 3) 只显示 Token（关掉时间）
    pet.set_hud_show_token(True)
    pet.set_hud_show_time(False)
    text = hud_text(pet)
    assert "Token" in text and not re.search(r"\d{2}:\d{2}:\d{2}", text), text
    print(f"3. 只显示 Token OK → {text}")

    # 4) 日期开关：关掉日期后仍有时间，但没有"周X"
    pet.set_hud_show_time(True)
    pet.set_hud_show_date(False)
    text = hud_text(pet)
    assert re.search(r"\d{2}:\d{2}:\d{2}", text) and "周" not in text, text
    print(f"4. 日期可单独关闭 OK → {text}")

    # 5) 时间显示到秒且每秒刷新（1 秒后文本应变化）
    pet.set_hud_show_date(True)
    t1 = hud_text(pet)
    end = time.time() + 1.3
    while time.time() < end:
        app.processEvents()
    pet._update_hud()
    t2 = hud_text(pet)
    assert t1 != t2, ("时间未按秒刷新", t1, t2)
    print("5. 时间按秒刷新 OK")

    # 6) 字号随角色变大，且有下限（不会小到看不清）
    pet.set_size_level(w.SIZE_MIN, save=False)
    small = pet._hud_font_px()
    pet.set_size_level(w.SIZE_MAX, save=False)
    big = pet._hud_font_px()
    assert small >= 15, ("最小字号过低", small)
    assert big > small and big <= 24, (small, big)
    print(f"6. 字号 OK（最小档 {small}px → 最大档 {big}px）")

    # 7) 全部关掉时不显示 HUD（窗口自动收缩），不会留白框
    pet.hud_show_token = pet.hud_show_time = pet.hud_show_date = False
    pet._update_hud()
    assert not pet.hud_card.isVisible(), "全关时 HUD 应隐藏"
    assert pet.height() == pet.size_px + 4, ("窗口应收缩", pet.height(), pet.size_px)
    print("7. 全关时 HUD 隐藏且窗口收缩 OK")

    # 8) Token 系统关闭时不显示"Token 系统关闭"占位（时间照常显示）
    for flag in ("hud_show_token", "hud_show_time", "hud_show_date"):
        setattr(pet, flag, True)
    pet.token_enabled = False
    pet._update_hud()
    text = hud_text(pet)
    assert "Token" not in text and re.search(r"\d{2}:\d{2}:\d{2}", text), text
    print(f"8. Token 关闭时只显示时间 OK → {text}")

    # 9) 点击 HUD 区域不消耗 Token、不触发点击
    pet.token_enabled = True
    pet.token = 100000
    before = pet.token
    from PyQt5.QtCore import QPointF, QEvent, Qt
    from PyQt5.QtGui import QMouseEvent
    card = pet.hud_card
    pos = QPointF(card.x() + card.width() / 2, card.y() + card.height() / 2)
    w.QCursor.setPos(pet.x() + int(pos.x()), pet.y() + int(pos.y()))
    QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseButtonPress, pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
    QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseButtonRelease, pos, Qt.LeftButton, Qt.NoButton, Qt.NoModifier))
    app.processEvents()
    assert pet.token == before, ("点击 HUD 不应消耗 Token", before, pet.token)
    print("9. 点击 HUD 不误触发 OK")

    app.quit()
    print()
    print("HUD 自测结果: 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
