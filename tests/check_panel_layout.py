# -*- coding: utf-8 -*-
"""面板布局与拖拽自测：各页高度自适应（不留大片空白）、高 DPI 修复、
拖动时取消压扁（避免变形/重影）。

用法：python tests/check_panel_layout.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPointF, QEvent
from PyQt5.QtGui import QMouseEvent

import whale_pet as w

w.save_config = lambda cfg: None


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.move(300, 200)
    pet.show()
    app.processEvents()

    # 1) 高 DPI 修复函数存在（修复缩放屏拖拽漂移的前提）
    assert hasattr(w, "enable_high_dpi"), "缺少 enable_high_dpi（高 DPI 修复）"
    print("1. 高 DPI 修复函数存在 OK（缩放屏拖拽不再漂移）")

    panel = w.SettingsPanel(pet)
    pet.settings_panel = panel
    panel.move(500, 60)
    panel.show()
    app.processEvents()

    # 2) 每个标签页高度跟随自身内容（内容少的页不再留大片空白）
    heights = {}
    tabs = {}
    for i in range(panel.tabs.count()):
        panel.tabs.setCurrentIndex(i)
        app.processEvents()
        time.sleep(0.05)
        app.processEvents()
        heights[i] = panel.height()
        page = panel.tabs.currentWidget()
        tabs[i] = panel.tabs.height() - page.sizeHint().height()
    name = [panel.tabs.tabText(i) for i in range(panel.tabs.count())]
    print("   各页面板高度:", {name[i]: heights[i] for i in heights})
    assert len(set(heights.values())) > 1, ("各页高度应有差异（自适应）", heights)
    for i, pad in tabs.items():
        assert 0 <= pad <= 60, (f"{name[i]} 页 tabs 高度与内容不匹配", pad)
    print("2. 各页高度自适应 OK（内容少的页不留大片空白）")

    # 3) 拖动时取消按压压扁：拖动后 label 几何应恢复方形
    center = QPointF(pet.width() / 2, pet.size_px * 0.4)
    w.QCursor.setPos(pet.x() + int(center.x()), pet.y() + int(center.y()))
    QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseButtonPress, center,
                                            Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
    app.processEvents()
    pressing = (pet.label.width(), pet.label.height())
    to = QPointF(center.x() + 60, center.y() + 30)
    w.QCursor.setPos(pet.x() + int(to.x()), pet.y() + int(to.y()))
    QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseMove, to, Qt.NoButton, Qt.LeftButton, Qt.NoModifier))
    end = time.time() + 0.35
    while time.time() < end:
        app.processEvents()
    assert pet._moved, "未进入拖动状态"
    assert pet.label.width() == pet.size_px and pet.label.height() == pet.size_px, \
        ("拖动中应恢复方形（避免变形/重影）", (pet.label.width(), pet.label.height()))
    QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseButtonRelease, to,
                                            Qt.LeftButton, Qt.NoButton, Qt.NoModifier))
    app.processEvents()
    print(f"3. 拖动取消压扁 OK（按压时 {pressing} → 拖动中恢复方形）")

    # 4) 拖动跟手：窗口位移应与鼠标位移一致（同一坐标系）
    pet.move(400, 300)
    app.processEvents()
    start_win = (pet.x(), pet.y())
    c2 = QPointF(pet.width() / 2, pet.size_px * 0.4)
    w.QCursor.setPos(pet.x() + int(c2.x()), pet.y() + int(c2.y()))
    QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseButtonPress, c2,
                                            Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
    for step in range(1, 5):
        p = QPointF(c2.x() + step * 20, c2.y() + step * 10)
        w.QCursor.setPos(pet.x() + int(p.x()), pet.y() + int(p.y()))
        QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseMove, p, Qt.NoButton, Qt.LeftButton, Qt.NoModifier))
        app.processEvents()
    moved = (pet.x() - start_win[0], pet.y() - start_win[1])
    QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseButtonRelease, p,
                                            Qt.LeftButton, Qt.NoButton, Qt.NoModifier))
    app.processEvents()
    assert moved[0] > 0 and moved[1] > 0, ("拖动方向异常（应为正向跟随）", moved)
    print(f"4. 拖动方向正确 OK（鼠标右下移动 → 窗口位移 {moved}）")

    app.quit()
    print()
    print("面板布局与拖拽自测结果: 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
