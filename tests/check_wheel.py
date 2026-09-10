# -*- coding: utf-8 -*-
"""滚轮误操作自测：在面板上滚动时，滑块与下拉框的值不得被改变。

用法：python tests/check_wheel.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QSlider, QComboBox
from PyQt5.QtCore import QPointF, QPoint, Qt
from PyQt5.QtGui import QWheelEvent

import whale_pet as w

w.save_config = lambda cfg: None


def wheel(widget, delta=-120):
    """向控件发送一个滚轮事件（delta<0 表示向下滚）。"""
    ev = QWheelEvent(QPointF(widget.width() / 2, widget.height() / 2),
                     QPointF(widget.width() / 2, widget.height() / 2),
                     QPoint(0, delta), QPoint(0, delta),
                     Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
    QApplication.sendEvent(widget, ev)
    QApplication.processEvents()


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    panel = w.SettingsPanel(pet)
    pet.settings_panel = panel
    panel.show()
    end = time.time() + 0.4
    while time.time() < end:
        app.processEvents()

    sliders = panel.findChildren(QSlider)
    combos = panel.findChildren(QComboBox)
    assert sliders and combos, "未找到滑块/下拉框"

    # 1) 所有滑块：上下滚动各 3 次，值都不得变化
    for sld in sliders:
        before = sld.value()
        for _ in range(3):
            wheel(sld, -120)
            wheel(sld, 120)
        assert sld.value() == before, ("滑块被滚轮改动了", sld.value(), before)
    print(f"1. 滑块不响应滚轮 OK（{len(sliders)} 个滑块，上下各滚 3 次值不变）")

    # 2) 所有下拉框：滚动不得切换选项
    for cb in combos:
        before = cb.currentIndex()
        for _ in range(3):
            wheel(cb, -120)
            wheel(cb, 120)
        assert cb.currentIndex() == before, ("下拉框被滚轮切换了", cb.currentIndex(), before)
    print(f"2. 下拉框不响应滚轮 OK（{len(combos)} 个下拉框，滚动不切换选项）")

    # 3) 表情与音效这类关键下拉，顺便确认配置未被误改
    expr_before = pet.expression
    sound_before = pet.sound_mode
    for _ in range(5):
        wheel(panel.expr_combo)
        wheel(panel.sound_combo)
    assert pet.expression == expr_before, ("表情被滚轮改了", pet.expression, expr_before)
    assert pet.sound_mode == sound_before, ("音效被滚轮改了", pet.sound_mode, sound_before)
    print("3. 表情 / 音效不被滚轮误改 OK")

    # 4) 滑块用键盘/点击仍可正常调节（功能没被禁用）
    sld = panel.size_slider
    old = sld.value()
    target = sld.minimum() if old != sld.minimum() else sld.maximum()
    sld.setValue(target)
    app.processEvents()
    assert pet.size_px == w.size_level_to_px(target), "滑块仍应可正常调节"
    sld.setValue(old)
    app.processEvents()
    print("4. 滑块仍可正常调节 OK（只是不响应滚轮）")

    # 5) 标签栏也不吃滚轮（否则滚动会误切换标签页）
    tabbar = panel.tabs.tabBar()
    before_tab = panel.tabs.currentIndex()
    for _ in range(3):
        wheel(tabbar, -120)
        wheel(tabbar, 120)
    assert panel.tabs.currentIndex() == before_tab, \
        ("滚轮误切换了标签页", panel.tabs.currentIndex(), before_tab)
    print("5. 标签栏不响应滚轮 OK（滚动不会误切标签页）")

    app.quit()
    print()
    print("滚轮误操作自测结果: 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
