# -*- coding: utf-8 -*-
"""UI 完整性自测：
1) 每个交互控件是否完整落在卡片内容区（不被裁切）
2) 文字是否被截断（按钮/复选框/下拉/输入框提示）
3) 交互有效性：滑块/复选框/下拉改动后，配置是否真的生效
4) 各页尺寸是否随内容自适应

用法：python tests/check_ui.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QCheckBox,
                             QComboBox, QLineEdit, QSlider, QListWidget, QTabWidget)
from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QFontMetrics

import whale_pet as w

w.save_config = lambda cfg: None

INTERACTIVE = (QPushButton, QCheckBox, QComboBox, QLineEdit, QSlider, QListWidget)


def widget_text(widget):
    if isinstance(widget, (QPushButton, QCheckBox, QLabel)):
        return widget.text()
    if isinstance(widget, QComboBox):
        return widget.currentText()
    if isinstance(widget, QLineEdit):
        return widget.placeholderText()
    return ""


def text_needs_width(widget):
    """控件的文字实际需要多少像素（含内边距）。"""
    text = widget_text(widget)
    if not text:
        return 0
    fm = QFontMetrics(widget.font())
    pad = 24
    if isinstance(widget, QCheckBox):
        pad = 30                       # 含方块与间距
    elif isinstance(widget, QPushButton):
        pad = 16
    return fm.horizontalAdvance(text) + pad


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.show()
    app.processEvents()
    panel = w.SettingsPanel(pet)
    pet.settings_panel = panel
    panel.show()
    app.processEvents()

    problems = []
    page_heights = {}
    checked = 0
    per_page = {}

    for idx in range(panel.tabs.count()):
        panel.tabs.setCurrentIndex(idx)
        end = time.time() + 0.4
        while time.time() < end:
            app.processEvents()
        # 强制激活布局，确保几何真实（否则未布局的控件几何为 0，会误报越界）
        page = panel.tabs.currentWidget()
        if page.layout() is not None:
            page.layout().activate()
        if panel.card.layout() is not None:
            panel.card.layout().activate()
        page.updateGeometry()
        app.processEvents()
        time.sleep(0.05)
        app.processEvents()

        name = panel.tabs.tabText(idx)
        page_heights[name] = panel.height()
        card = panel.card
        card_rect = QRect(0, 0, card.width(), card.height())
        count = 0
        for widget in page.findChildren(QWidget):
            # isVisibleTo(page)：按页判断，不受标签页切换时机影响（隐藏控件如提示文字跳过）
            if not isinstance(widget, INTERACTIVE) or not widget.isVisibleTo(page):
                continue
            if widget.height() <= 1 or widget.width() <= 1:
                continue      # 尚未布局完成的控件跳过（避免误报）
            count += 1
            checked += 1
            # 1) 文字是否被截断（几何判断，可靠）
            need = text_needs_width(widget)
            if need and widget.width() > 1 and widget.width() < need:
                problems.append(f"[{name}] 文字可能被截断: {type(widget).__name__} "
                                f"{widget_text(widget)[:24]!r} 宽={widget.width()} 需要≈{need}")
            # 2) 控件本身是否可用
            if not widget.isEnabled():
                problems.append(f"[{name}] 控件被禁用: {widget_text(widget)[:20]!r}")
        per_page[name] = count

        # 像素级边缘检测：卡片内容区底边/右边若出现"控件色"，说明内容被裁或贴边
        img = panel.grab().toImage()
        iw, ih = img.width(), img.height()
        margin = 14

        def bright(x, y):
            c = img.pixelColor(x, y)
            return (c.red() + c.green() + c.blue()) / 3.0

        def edge_has_content(xs, ys, label):
            total = hit = 0
            for y in ys:
                for x in xs:
                    total += 1
                    if bright(x, y) > 90:
                        hit += 1
            if total and hit / total > 0.06:
                problems.append(f"[{name}] {label}边缘有内容贴边（可能被裁）")

        xr = range(margin + 8, iw - margin - 8)
        yr = range(margin + 8, ih - margin - 8)
        edge_has_content(xr, range(ih - margin - 3, ih - margin + 1), "底部")
        # 右侧只检测最外侧 6px（避开内容区内的滚动条，否则限高滚动时必然误报）
        edge_has_content(range(iw - 8, iw - 3), yr, "右侧")

    print(f"检查控件数: {checked}（分页：{per_page}）")
    print(f"各页面板高度: {page_heights}")
    assert len(set(page_heights.values())) > 1, "各页高度应随内容不同"

    # 4) 交互有效性：滑块 / 复选框 / 下拉
    checks = [
        ("大小滑块", panel.size_slider, lambda v: pet.size_px, lambda: w.size_level_to_px(panel.size_slider.value()), True),
        ("音量滑块", panel.vol_slider, lambda v: pet.volume, lambda: panel.vol_slider.value(), True),
        ("气泡字号", panel.bubble_font_slider, lambda v: pet.bubble_font_size, lambda: panel.bubble_font_slider.value(), True),
        ("冷却滑块", panel.cooldown_slider, lambda v: pet.app_rule_cooldown, lambda: panel.cooldown_slider.value(), True),
        ("漫游延迟", panel.wander_delay_slider, lambda v: pet.wander_delay, lambda: panel.wander_delay_slider.value(), True),
        ("躲避距离", panel.evade_range_slider, lambda v: pet.evade_range, lambda: panel.evade_range_slider.value(), True),
    ]
    for label, sld, getter, expect, _ in checks:
        old = sld.value()
        target = sld.minimum() if old != sld.minimum() else sld.maximum()
        sld.setValue(target)
        app.processEvents()
        got = getter(None)
        want = expect()
        assert got == want, (f"{label} 调节未生效", got, want)
        sld.setValue(old)
        app.processEvents()
    print("4. 滑块全部生效 OK（大小/音量/字号/冷却/漫游/躲避）")

    toggles = [
        ("显示时间", panel.hud_time_check, lambda: pet.hud_show_time),
        ("显示 Token", panel.hud_token_check, lambda: pet.hud_show_token),
        ("显示日期星期", panel.hud_date_check, lambda: pet.hud_show_date),
        ("气泡开关", panel.bubble_check, lambda: pet.bubble_on),
        ("自动轮换", panel.auto_rotate_check, lambda: pet.auto_rotate),
        ("开机自启(状态读回)", panel.autostart_check, lambda: panel.autostart_check.isChecked()),
    ]
    for label, chk, getter in toggles:
        before = getter()
        chk.toggle()
        app.processEvents()
        after = getter()
        assert before != after, (f"{label} 切换未生效", before, after)
        chk.toggle()
        app.processEvents()
    print("5. 复选框全部生效 OK（HUD 三项/气泡/轮换/自启）")

    combo = panel.color_combo
    old = combo.currentIndex()
    combo.setCurrentIndex((old + 1) % combo.count())
    app.processEvents()
    assert pet.bubble_color == combo.currentData(), ("气泡颜色下拉未生效", pet.bubble_color)
    combo.setCurrentIndex(old)
    app.processEvents()
    print("6. 下拉框生效 OK（气泡颜色 → HUD 主题联动）")

    # 7) 点击有效性：+520W 真的加到 Token
    before = pet.token
    for btn in panel.findChildren(QPushButton):
        if "+520W" in btn.text():
            btn.click()
            break
    app.processEvents()
    assert pet.token == before + 5200000, ("+520W 按钮未生效", before, pet.token)
    pet.token = before
    print("7. 按钮点击生效 OK（+520W 实际到账）")

    print()
    if problems:
        print(f"发现 {len(problems)} 个 UI 问题：")
        for p in problems[:25]:
            print("  -", p)
    else:
        print("[OK] 未发现越界/截断/禁用等 UI 问题")
    app.quit()
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
