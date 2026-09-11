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
import ctypes
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

    # 3) desktop.ini + autorun.inf + icon.ico 三件套（普通权限即可）
    root_attrs_before = ctypes.windll.kernel32.GetFileAttributesW(tmp)
    ok, reason = w.apply_drive_icon(tmp + "\\", ico)
    inf = os.path.join(tmp, "autorun.inf")
    ini = os.path.join(tmp, "desktop.ini")
    dst_ico = os.path.join(tmp, "icon.ico")
    assert ok, ("应用磁盘图标失败", reason)
    assert os.path.exists(ini) and os.path.exists(inf) and os.path.exists(dst_ico), \
        "desktop.ini / autorun.inf / icon.ico 未全部生成"
    raw = open(ini, "rb").read()
    assert raw[:2] in (b"\xff\xfe", b"\xfe\xff"), "desktop.ini 应为 UTF-16 编码"
    text = open(ini, encoding="utf-16").read()
    assert "[.ShellClassInfo]" in text and "IconResource=" in text, text
    attrs_ini = ctypes.windll.kernel32.GetFileAttributesW(ini)
    assert attrs_ini != -1 and (attrs_ini & 0x02) and (attrs_ini & 0x04), \
        "desktop.ini 应带隐藏+系统属性（Windows 才认）"
    root_attrs_after = ctypes.windll.kernel32.GetFileAttributesW(tmp)
    assert root_attrs_before == root_attrs_after, \
        "不应改动磁盘根目录属性（这正是旧版需要管理员权限的原因）"
    print("3. desktop.ini(UTF-16) + autorun.inf + icon.ico OK，且未改动盘根属性")

    # 3b) 恢复默认图标：能删除放置的文件
    ok3, msg3 = w.remove_drive_icon(tmp + "\\")
    assert ok3 and not os.path.exists(ini) and not os.path.exists(inf), ("恢复失败", msg3)
    print(f"3b. 恢复默认图标 OK（{msg3[:30]}）")

    # 3c) 重复应用：文件已带隐藏/系统属性时，第二次仍须成功（回归用例）
    ok4, r4 = w.apply_drive_icon(tmp + "\\", ico)
    assert ok4, ("第 1 次应用失败", r4)
    ok5, r5 = w.apply_drive_icon(tmp + "\\", ico)
    assert ok5, ("重复应用失败（隐藏属性挡住了覆盖）", r5)
    print("3c. 重复应用 OK（会自动清除属性后覆盖，不再报无权限）")

    # 3d) 刷新通知：SHChangeNotify 可用（不重启 explorer，不黑屏）
    assert w.refresh_icon_cache() is True, "图标缓存刷新失败"
    print("3d. 图标缓存刷新 OK（ie4uinit + SHChangeNotify，不黑屏）")
    w.remove_drive_icon(tmp + "\\")

    # 3e) 属性清除：设置过的隐藏/系统属性必须能真的清掉（旧版只 |= 不 &=，清不掉）
    tmp2 = tempfile.mkdtemp()
    probe = os.path.join(tmp2, "desktop.ini")
    with open(probe, "w", encoding="utf-8") as f:
        f.write("x")
    assert w.set_file_attrs(probe, hidden=True, system=True), "设置属性失败"
    a1 = ctypes.windll.kernel32.GetFileAttributesW(probe)
    assert (a1 & 0x02) and (a1 & 0x04), "隐藏/系统属性未设上"
    assert w.set_file_attrs(probe, hidden=False, system=False, readonly=False), "清除属性失败"
    a2 = ctypes.windll.kernel32.GetFileAttributesW(probe)
    assert not (a2 & 0x02) and not (a2 & 0x04), ("隐藏/系统属性没清掉（会导致删除时拒绝访问）", a2)
    print("3e. 文件属性可设可清 OK（隐藏/系统真能被清掉）")

    # 3f) 删除被拒绝（模拟 C 盘那种「管理员身份写入的高权限文件」）：
    #     必须如实报告 + 给出解决路径，绝不能假成功
    if w.is_admin():
        print("3f. 跳过（当前是管理员，普通权限分支不适用）")
    else:
        real_remove = os.remove
        real_admin = w.is_admin
        real_elev = w.delete_files_elevated
        try:
            def deny_target(path):
                if os.path.abspath(path).lower() == os.path.abspath(probe).lower():
                    raise PermissionError(13, "拒绝访问")
                return real_remove(path)

            os.remove = deny_target
            w.delete_files_elevated = lambda paths: (False, "提权请求被取消或失败（代码 5）")
            w.is_admin = lambda: False
            ok6, msg6 = w.remove_drive_icon(tmp2 + "\\")
            assert ok6 is False, ("删除被拒绝时不该报成功", ok6, msg6)
            assert "管理员" in msg6, ("应告诉用户需要管理员权限", msg6)
            assert os.path.exists(probe), "文件不该凭空消失"
            print(f"3f. 删除被拒绝时如实报告 OK → {msg6[:44]}")

            # 3g) 提权删除：UAC 发起但文件没删掉时要说明，不能假装成功
            w.delete_files_elevated = lambda paths: (True, "")
            ok7, msg7 = w.remove_drive_icon(tmp2 + "\\")
            assert ok7 is False and ("UAC" in msg7 or "仍在" in msg7), ("提权后仍失败应说明", msg7)
            print(f"3g. UAC 删除未完成时如实报告 OK → {msg7[:44]}")

            # 3g2) 提权删除成功（模拟 UAC 通过、文件被删掉）→ 必须报成功，不能因为
            #      "曾经拒绝过" 就一直报失败
            def fake_elevate(paths):
                for p in paths:
                    real_remove(p)
                return True, ""

            with open(probe, "w", encoding="utf-8") as f:
                f.write("y")
            w.delete_files_elevated = fake_elevate
            ok9, msg9 = w.remove_drive_icon(tmp2 + "\\")
            assert ok9 is True and not os.path.exists(probe), \
                ("提权删除成功后应报成功", ok9, msg9)
            print(f"3g2. 提权删除成功后报成功 OK → {msg9[:44]}")
        finally:
            os.remove = real_remove
            w.is_admin = real_admin
            w.delete_files_elevated = real_elev
        if os.path.exists(probe):          # 3g2 里已被"提权"删掉，这里不能再删一次
            real_remove(probe)
        os.rmdir(tmp2)

    # 3h) 完整性标签降级接口：不该抛异常（非管理员时可能返回 False，属正常）
    ok8 = w.lower_integrity_to_medium(ico)
    assert isinstance(ok8, bool)
    print(f"3h. 完整性标签降级接口 OK（当前返回 {ok8}，非管理员返回 False 属正常）")
    assert w.delete_files_elevated([]) == (False, ""), "空列表应直接返回，不去弹 UAC"
    print("3i. 提权删除空列表不弹窗 OK")

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
