# -*- coding: utf-8 -*-
"""压力自测：遍历面板全部控件 + 模拟日常操作，捕获任何被 _guard 记录的异常。"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (QApplication, QCheckBox, QSlider, QPushButton, QComboBox,
                             QLineEdit, QListWidget, QMessageBox, QFileDialog, QInputDialog)
from PyQt5.QtCore import Qt, QPointF, QEvent, QMimeData, QUrl
from PyQt5.QtGui import QMouseEvent, QDragEnterEvent, QDropEvent

import whale_pet as w

w.save_config = lambda cfg: None
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)
QMessageBox.information = staticmethod(lambda *a, **k: QMessageBox.Ok)
QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: ("", ""))
QInputDialog.getItem = staticmethod(lambda *a, **k: ("", False))
w.subprocess.Popen = lambda *a, **k: None
w.webbrowser.open = lambda *a, **k: True

SKIP_BTNS = {"✕", "退出"}


def pump(app, sec=0.02):
    import time
    end = time.time() + sec
    while time.time() < end:
        app.processEvents()


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.move(300, 300)
    pet.show()
    pump(app)

    # 捕获所有被 _guard 记录的异常
    errors = []
    orig_log = pet._log

    def spy_log(msg):
        if "[异常]" in str(msg) or "[未捕获异常]" in str(msg):
            errors.append(str(msg))
        return orig_log(msg)

    pet._log = spy_log

    panel = w.SettingsPanel(pet)
    pet.settings_panel = panel
    panel.move(500, 50)
    panel.show()
    pump(app, 0.3)

    # ---------- 1. 全部按钮 ----------
    clicks = 0
    for btn in panel.findChildren(QPushButton):
        if btn.text() in SKIP_BTNS or btn.objectName() == "closeBtn":
            continue
        btn.click()
        pump(app)
        clicks += 1
    print(f"1. 按钮点击 {clicks} 个 → 异常 {len(errors)}")

    # ---------- 2. 全部复选框（开→关→开） ----------
    toggles = 0
    for chk in panel.findChildren(QCheckBox):
        for _ in range(2):
            chk.toggle()
            pump(app)
            toggles += 1
    print(f"2. 复选框切换 {toggles} 次 → 异常 {len(errors)}")

    # ---------- 3. 全部滑块（最小/最大/中间） ----------
    moves = 0
    for sld in panel.findChildren(QSlider):
        for v in (sld.minimum(), sld.maximum(), (sld.minimum() + sld.maximum()) // 2):
            sld.setValue(v)
            pump(app)
            moves += 1
    print(f"3. 滑块取值 {moves} 次 → 异常 {len(errors)}")

    # ---------- 4. 全部下拉框逐项切换 ----------
    combos = 0
    for cb in panel.findChildren(QComboBox):
        for i in range(cb.count()):
            cb.setCurrentIndex(i)
            pump(app)
            combos += 1
    print(f"4. 下拉切换 {combos} 次 → 异常 {len(errors)}")

    # ---------- 5. 输入框输入/清空 ----------
    edits = 0
    for le in panel.findChildren(QLineEdit):
        if le is panel.search_edit:
            for kw in ("音量", "泡泡", "自启", "规则", "zzz"):
                le.setText(kw)
                pump(app)
                edits += 1
            le.clear()
            continue
        le.setText("测试台词")
        pump(app)
        le.clear()
        pump(app)
        edits += 2
    print(f"5. 输入框操作 {edits} 次 → 异常 {len(errors)}")

    # ---------- 6. 列表：选中 + 双击 ----------
    lists = 0
    for lw in panel.findChildren(QListWidget):
        for i in range(lw.count()):
            lw.setCurrentRow(i)
            lw.itemDoubleClicked.emit(lw.item(i))
            pump(app)
            lists += 2
    print(f"6. 列表操作 {lists} 次 → 异常 {len(errors)}")

    # ---------- 7. 桌宠日常操作 ----------
    def click(pos):
        QCursorPos = pet.pos()
        w.QCursor.setPos(QCursorPos.x() + int(pos.x()), QCursorPos.y() + int(pos.y()))
        press = QMouseEvent(QEvent.MouseButtonPress, QPointF(pos), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QApplication.sendEvent(pet, press)
        rel = QMouseEvent(QEvent.MouseButtonRelease, QPointF(pos), Qt.LeftButton, Qt.NoButton, Qt.NoModifier)
        QApplication.sendEvent(pet, rel)
        pump(app)

    center = QPointF(pet.width() / 2, pet.height() * 0.3)
    for _ in range(6):                       # 快速连点
        click(center)
    # 长按
    w.QCursor.setPos(pet.x() + int(center.x()), pet.y() + int(center.y()))
    QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseButtonPress, center, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
    pump(app, 0.7)
    QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseButtonRelease, center, Qt.LeftButton, Qt.NoButton, Qt.NoModifier))
    pump(app)
    # 拖拽
    QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseButtonPress, center, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
    to = QPointF(center.x() + 80, center.y() + 40)
    w.QCursor.setPos(pet.x() + int(to.x()), pet.y() + int(to.y()))
    QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseMove, to, Qt.NoButton, Qt.LeftButton, Qt.NoModifier))
    QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseButtonRelease, to, Qt.LeftButton, Qt.NoButton, Qt.NoModifier))
    pump(app)
    print(f"7. 点击/长按/拖拽 → 异常 {len(errors)}")

    # ---------- 8. 右键短按（面板）/ 右键拖拽（弹射） ----------
    pet.show_bubble_quick = lambda *a, **k: None
    for kind in ("right",):
        w.QCursor.setPos(pet.x() + int(center.x()), pet.y() + int(center.y()))
        QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseButtonPress, center, Qt.RightButton, Qt.RightButton, Qt.NoModifier))
        QApplication.sendEvent(pet, QMouseEvent(QEvent.MouseButtonRelease, center, Qt.RightButton, Qt.NoButton, Qt.NoModifier))
        pump(app, 0.2)
    # 弹射：按下 → 移动到远处 → 松手
    pet._char_at_press = pet._center()
    pet._sling_vx, pet._sling_vy = 900, -300
    pet._sling_active = True
    for _ in range(120):                     # 推进弹射（含边缘反弹）
        pet._sling_step(1 / 60.0)
        pump(app, 0.001)
    print(f"8. 右键/弹射 → 异常 {len(errors)}")

    # ---------- 9. 喂食（临时文件 + 目录） ----------
    tmp = tempfile.mkdtemp()
    f = os.path.join(tmp, "喂.txt")
    open(f, "w").close()
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(f)])
    pet.feed_path(f)
    d = os.path.join(tmp, "目录")
    os.makedirs(d)
    open(os.path.join(d, "a.bin"), "wb").write(b"x" * 2048)
    pet.feed_path(d)
    text_only = QMimeData()
    text_only.setText("纯文本")
    ev = QDragEnterEvent(QPointF(10, 10).toPoint(), Qt.CopyAction, text_only, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(pet, ev)
    print(f"9. 喂食文件/目录 → 异常 {len(errors)}（文件已删={not os.path.exists(f)}）")

    # ---------- 10. 各功能模式切换 + 移动 tick ----------
    for attr, on in (("follow_mode", True), ("evade_mode", True), ("wander_mode", True),
                     ("lock_position", True), ("always_on_top", True)):
        setattr(pet, attr, on)
        pet._last_interact = 0
        for _ in range(30):
            pet._move_tick()
            pump(app, 0.001)
        setattr(pet, attr, False)
    print(f"10. 跟随/躲避/漫游/锁定/置顶 tick → 异常 {len(errors)}")

    # ---------- 11. 表情/大小/台词/气泡 全量 ----------
    for e in pet.expressions[:25]:
        pet.apply_expression(e["name"], save=False, play_sound=False)
    for lv in range(w.SIZE_MIN, w.SIZE_MAX + 1):
        pet.set_size_level(lv, save=False)
    for src in ("mood", "random", "custom", "fixed"):
        pet.set_fixed_line_and_clear_custom("固定台词测试")
        pet.line_source = src
        pet._pick_line()
        pet.show_bubble_quick("测试")
    for color in ("blue", "pink", "dark", "green"):
        pet.set_bubble_color(color)
    for mode in list(pet.sounds):
        pet.set_sound_mode(mode)
        pet.play_sound("click")
        pet.play_sound("release")
    print(f"11. 表情/大小/台词/气泡/音效全量 → 异常 {len(errors)}")

    # ---------- 12. 应用监控 / 更新检查 / 日志清理 ----------
    pet._get_foreground_exe = lambda: ("msedge.exe", "Edge")
    pet.app_rules = [{"match": "edge", "text": "测试", "chance": 100, "enabled": True}]
    for _ in range(3):
        pet._last_fore_exe = ""
        pet._monitor_tick()
        pump(app)
    pet.reload_external()
    w.rotate_log_if_needed()
    print(f"12. 监控/重载/日志清理 → 异常 {len(errors)}")

    # ---------- 结果 ----------
    pet._log = orig_log
    print()
    if errors:
        print("发现异常（应修复）：")
        for e in errors[:10]:
            print("  -", e.splitlines()[0])
        print(f"共 {len(errors)} 条")
    else:
        print("[OK] 全流程无异常")
    print("进程存活:", pet.isVisible())
    app.quit()


if __name__ == "__main__":
    main()
