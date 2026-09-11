# -*- coding: utf-8 -*-
"""磁盘图标与气泡方向自测：
1) 磁盘图标：无权限时给出明确原因（不再假成功/静默失败）
2) desktop.ini 用 UTF-16 编码（中文路径才有效）
3) 文件属性用 ctypes 设置成功
4) 气泡尖头方向：在角色上方朝下、在下方朝上
5) 气泡跟随：吸附/瞬移后气泡跟着走

用法：python tests/check_drive_icon.py
"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication

import whale_pet as w

w.save_config = lambda cfg: None


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.show()
    app.processEvents()

    # 1) 管理员检测可用
    assert isinstance(w.is_admin(), bool)
    print(f"1. 管理员检测 OK（当前：{'管理员' if w.is_admin() else '普通用户'}）")

    # 2) ICO 生成 + 文件属性（用临时目录，不碰系统盘）
    png = os.path.join(w.EXPR_DIR, "v1_fatfish.png")
    tmp = tempfile.mkdtemp()
    ico = os.path.join(tmp, "fish.ico")
    ok, reason = w.build_fish_ico(png, ico)
    assert ok, ("ICO 生成失败", reason)
    assert open(ico, "rb").read()[:4] == b"\x00\x00\x01\x00"
    assert w.set_file_attrs(ico, hidden=True, system=True), "设置文件属性失败"
    print(f"2. ICO 生成 + 文件属性 OK（{os.path.getsize(ico)} 字节，已设隐藏+系统）")

    # 3) 用 autorun.inf + icon.ico 方案（普通权限即可，对标参考项目）
    ok, reason = w.apply_drive_icon(tmp + "\\", ico)
    inf = os.path.join(tmp, "autorun.inf")
    dst_ico = os.path.join(tmp, "icon.ico")
    assert ok, ("应用磁盘图标失败", reason)
    assert os.path.exists(inf) and os.path.exists(dst_ico), "autorun.inf / icon.ico 未生成"
    text = open(inf, encoding="ascii", errors="replace").read()
    assert "[autorun]" in text and "ICON" in text and "icon.ico" in text, text
    assert open(dst_ico, "rb").read()[:4] == b"\x00\x00\x01\x00", "icon.ico 不是合法 ICO"
    import ctypes as _ct
    attrs = _ct.windll.kernel32.GetFileAttributesW(inf)
    assert attrs != -1 and (attrs & 0x02), "autorun.inf 应设为隐藏属性"
    print("3. autorun.inf + icon.ico 方案 OK（普通权限即可，文件已设隐藏）")

    # 3b) 恢复默认图标：能删除放置的文件
    ok3, msg3 = w.remove_drive_icon(tmp + "\\")
    assert ok3 and not os.path.exists(inf) and not os.path.exists(dst_ico), ("恢复失败", msg3)
    print(f"3b. 恢复默认图标 OK（{msg3[:30]}）")

    # 4) 无权限路径：必须返回明确原因，而不是假成功
    bad_dir = r"C:\Windows\System32\__dshw_no_perm__"
    ok2, reason2 = w.build_fish_ico(png, os.path.join(bad_dir, "x.ico"))
    assert ok2 is False and reason2, ("无权限时应返回失败与原因", ok2, reason2)
    print(f"4. 无权限时返回明确原因 OK → {reason2[:40]}")

    # 5) 气泡尖头方向：在角色上方 → 朝下；在角色下方 → 朝上
    geo = app.primaryScreen().availableGeometry()
    pet.move(geo.center().x(), geo.center().y())
    pet.bubble.show_lines(["测试"], 3000, pet=pet)
    app.processEvents()
    assert pet.bubble.y() < pet.y() and pet.bubble.tail_up is False, "上方气泡尖头应朝下"
    pet.bubble.hide()
    pet.move(geo.center().x(), geo.top())          # 贴顶 → 气泡落到下方
    pet.bubble.show_lines(["测试贴顶"], 3000, pet=pet)
    app.processEvents()
    assert pet.bubble.y() > pet.y() and pet.bubble.tail_up is True, \
        ("下方气泡尖头应朝上（指向角色）", pet.bubble.tail_up)
    print("5. 气泡尖头方向 OK（上方朝下 / 下方朝上）")
    pet.bubble.hide()

    # 6) 气泡跟随：吸附/瞬移后气泡必须跟着走（不再定在原地）
    pet.move(geo.right() - 400, geo.center().y())
    pet.bubble.show_lines(["跟随测试"], 3000, pet=pet)
    app.processEvents()
    before = (pet.bubble.x(), pet.bubble.y())
    pet.move(geo.left() + 50, geo.center().y())    # 模拟吸附/瞬移
    app.processEvents()
    pet._snap_to_edge()
    app.processEvents()
    after = (pet.bubble.x(), pet.bubble.y())
    assert after != before, ("气泡没有跟着桌宠移动", before, after)
    dx = abs(pet.bubble.x() + pet.bubble.width() // 2 - (pet.x() + pet.width() // 2))
    assert dx <= 6, ("气泡未与角色对齐", dx)
    print(f"6. 气泡跟随桌宠 OK（移动后对齐偏差 {dx}px）")
    pet.bubble.hide()

    app.quit()
    print()
    print("磁盘图标与气泡方向自测结果: 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
