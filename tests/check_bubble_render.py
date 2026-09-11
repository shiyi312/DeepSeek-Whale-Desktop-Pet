# -*- coding: utf-8 -*-
"""气泡渲染级自测（像素验证，不只看坐标）：
1) 圆点方向：气泡在角色下方时圆点必须在图像上半部，否则在下半部
2) 绘制警告：不允许出现 UpdateLayeredWindowIndirect 失败（阴影曾导致）
3) 贴四角场景下气泡位置与圆点方向一致

用法：python tests/check_bubble_render.py
"""
import contextlib
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication

import whale_pet as w

w.save_config = lambda cfg: None


def border_center(img):
    """返回气泡描边像素的垂直重心比例（0=顶部，1=底部），用于判断圆点在哪一侧。"""
    total = 0.0
    weight = 0.0
    h, wd = img.height(), img.width()
    for y in range(h):
        for x in range(0, wd, 2):
            c = img.pixelColor(x, y)
            if c.alpha() < 40:
                continue
            if c.blue() > 90 and (c.blue() - c.red()) > 40 and c.green() < 140:
                total += 1
                weight += y
    if total == 0:
        return None
    return (weight / total) / h


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.show()
    app.processEvents()
    geo = app.primaryScreen().availableGeometry()
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "_shots")
    os.makedirs(out, exist_ok=True)
    err = io.StringIO()

    cases = [
        ("右下角", geo.right() - pet.width(), geo.bottom() - pet.height(), False),
        ("左下角", geo.left(), geo.bottom() - pet.height(), False),
        ("右上角", geo.right() - pet.width(), geo.top(), True),
        ("左上角", geo.left(), geo.top(), True),
    ]
    problems = []
    for name, x, y, expect_up in cases:
        pet.move(int(x), int(y))
        app.processEvents()
        with contextlib.redirect_stderr(err):
            pet.bubble.show_lines(["当前时间 16:53", "下午好，今日心情：开心"], 3000, pet=pet)
            end = time.time() + 0.45
            while time.time() < end:
                app.processEvents()
        b = pet.bubble
        img = b.grab().toImage()
        img.save(os.path.join(out, f"render_{name}.png"))
        center = border_center(img)
        # 圆点在下方时，椭圆整体偏上（重心 < 0.5）；
        # 圆点被镜像到上方时，椭圆整体下移（重心 > 0.5）
        actual_up = center is not None and center > 0.5
        ok = (b.tail_up == expect_up) and (actual_up == expect_up)
        print(f"  {name}: tail_up={b.tail_up}(期望{expect_up}) | 描边重心={center:.2f} "
              f"| 画面圆点朝{'上' if actual_up else '下'} | {'OK' if ok else '错误'}")
        if not ok:
            problems.append(name)
        b.hide()
        app.processEvents()

    warn = err.getvalue()
    if "UpdateLayeredWindowIndirect" in warn:
        problems.append("绘制警告")
        print("  错误: 出现 UpdateLayeredWindowIndirect 失败（气泡会显示残缺/残留）")
    else:
        print("  绘制无警告 OK（不再有分层窗口更新失败）")

    print()
    if problems:
        print("失败场景:", problems)
        return 1
    print("气泡渲染自测结果: 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
