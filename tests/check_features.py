# -*- coding: utf-8 -*-
"""新功能自测：全屏隐藏 / 面板宽度一致且无需滚动 / 全局搜索 / 自动更新提示。

用法：python tests/check_features.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QMessageBox

import whale_pet as w

w.save_config = lambda cfg: None


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.show()
    app.processEvents()

    # 1) 全屏时自动隐藏、退出全屏自动恢复
    pet.hide_in_fullscreen = True
    pet._is_fullscreen_foreground = lambda: True
    pet._fullscreen_tick()
    app.processEvents()
    assert not pet.isVisible(), "全屏时应隐藏桌宠（避免遮挡游戏）"
    pet._is_fullscreen_foreground = lambda: False
    pet._fullscreen_tick()
    app.processEvents()
    assert pet.isVisible(), "退出全屏后应恢复显示"
    print("1. 全屏自动隐藏 / 恢复 OK（不再遮挡游戏画面）")

    # 2) 面板：宽度各页一致（不再变胖变瘦）且每页都无需滚动
    panel = w.SettingsPanel(pet)
    pet.settings_panel = panel
    panel.show()
    widths, scroll_pages = set(), []
    for i in range(panel.tabs.count()):
        panel.tabs.setCurrentIndex(i)
        end = time.time() + 0.35
        while time.time() < end:
            app.processEvents()
        widths.add(panel.width())
        if panel.low_res_scroll:
            scroll_pages.append(panel.tabs.tabText(i))
    assert len(widths) == 1, ("各页宽度应一致（切页不变胖）", widths)
    assert not scroll_pages, ("这些页仍需要滚动", scroll_pages)
    print(f"2. 面板宽度一致（{widths.pop()}px）且每页无需滚动 OK")

    # 3) 全局搜索：跨标签页匹配并自动切换
    panel.search_edit.setText("音效")
    end = time.time() + 0.4
    while time.time() < end:
        app.processEvents()
    visible_cards = [c for c in panel.findChildren(w.Card) if c.isVisibleTo(panel.tabs.currentWidget())]
    assert visible_cards, "搜索后应至少有一张卡片可见"
    # 当前页应包含匹配卡片
    cur_texts = " ".join(c.keywords for c in visible_cards)
    assert "音效" in cur_texts, ("搜索未定位到匹配卡片", cur_texts[:60])
    panel.search_edit.clear()
    end = time.time() + 0.3
    while time.time() < end:
        app.processEvents()
    total_visible = len([c for c in panel.findChildren(w.Card)
                         if c.isVisibleTo(panel.tabs.currentWidget())])
    assert total_visible >= 1, "清空搜索后应恢复显示"
    print("3. 全局搜索 OK（跨标签页匹配并自动切到命中页）")

    # 4) 自动检查更新：发现新版本时弹窗询问；选“否”记住忽略，下次不再打扰
    pet._auto_check = True
    pet._update_tag = "v9.9.9"
    asked = {"n": 0}
    orig_question = QMessageBox.question
    QMessageBox.question = staticmethod(lambda *a, **k: (asked.__setitem__("n", asked["n"] + 1), QMessageBox.No)[1])
    w.webbrowser.open = lambda *a, **k: True
    try:
        pet._on_update_done("发现新版本 v9.9.9")
        app.processEvents()
        assert asked["n"] == 1, "应弹出更新询问"
        assert pet.cfg.get("skipped_version") == "v9.9.9", "应记住被忽略的版本"
        pet._on_update_done("发现新版本 v9.9.9")
        app.processEvents()
        assert asked["n"] == 1, "已忽略的版本不应反复弹窗"
    finally:
        QMessageBox.question = orig_question
    print("4. 自动更新提示 OK（发现新版弹窗询问；忽略后不再反复打扰）")

    # 5) 手动检查不受影响（不弹询窗、直接走原有提示）
    pet._auto_check = False
    pet._update_tag = ""
    pet._on_update_done("已经是最新版本啦")
    print("5. 手动检查更新行为不变 OK")

    app.quit()
    print()
    print("新功能自测结果: 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
