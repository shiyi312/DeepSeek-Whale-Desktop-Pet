# -*- coding: utf-8 -*-
"""音效系统自测：音效扫描 / 播放器池每声完整 / 自定义覆盖 / 零加载延迟 / 音量同步。

用法：python tests/check_sound.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtMultimedia import QMediaPlayer

import whale_pet as w

w.save_config = lambda cfg: None


class FakePlayer:
    def __init__(self, name):
        self.name = name
        self.playing = False
        self.volume = 0
        self.calls = []

    def state(self):
        return QMediaPlayer.PlayingState if self.playing else QMediaPlayer.StoppedState

    def play(self):
        self.playing = True
        self.calls.append("play")

    def stop(self):
        self.playing = False
        self.calls.append("stop")

    def setMedia(self, m):
        self.calls.append("setMedia")

    def setPosition(self, p):
        self.calls.append("setPosition")

    def setVolume(self, v):
        self.volume = v


def main():
    app = QApplication(sys.argv)
    pet = w.PetWindow()
    pet.show()
    app.processEvents()

    sounds = w.scan_sounds()
    assert sounds, "sounds 目录扫描为空"
    print(f"1. 音效扫描 OK（{len(sounds)} 个: {'、'.join(list(sounds)[:8])}）")

    pool = [FakePlayer(f"p{i}") for i in range(w.SFX_POOL_SIZE)]
    pet._sfx_pool = pool
    pet._sfx_seq = 0
    pet.custom_sound_path = ""
    pet.set_sound_mode(list(sounds)[0])

    for p in pool:
        p.calls.clear()
        p.playing = False
        p._dsh_path = ""
    pet._preload_sound()
    assert all(p.calls == ["setMedia"] for p in pool), [p.calls for p in pool]
    pet._preload_sound()
    assert all(p.calls == ["setMedia"] for p in pool), "重复预加载（应跳过）"
    print(f"2. 预加载 OK（{w.SFX_POOL_SIZE} 个播放器各加载一次，重复调用不重载）")

    for p in pool:
        p.calls.clear()
        p.playing = False
    for _ in range(w.SFX_POOL_SIZE):
        pet.play_sound("click")
    assert all(p.calls == ["setPosition", "play"] for p in pool), [p.calls for p in pool]
    assert sum(p.playing for p in pool) == w.SFX_POOL_SIZE, "应同时在播（每声完整）"
    print(f"3. 连点 {w.SFX_POOL_SIZE} 声各自完整 OK（无打断、无重叠糊音）")

    pool[0].calls.clear()
    pet.play_sound("click")
    assert pool[0].calls == ["stop", "play"], pool[0].calls
    assert len(pet._sfx_pool) == w.SFX_POOL_SIZE, "播放器数量不应增长"
    print("4. 池满接管最早一声 OK（播放器数量不增长）")

    name = list(sounds)[0]
    pet.custom_sound_path = sounds[name]["click"]
    assert pet._sound_path_for("click").endswith(os.path.basename(sounds[name]["click"]))
    assert pet._sound_path_for("release").endswith(os.path.basename(sounds[name]["click"]))
    pet._preload_sound()
    assert all(getattr(p, "_dsh_path", "").endswith(os.path.basename(sounds[name]["click"])) for p in pool)
    print("5. 自定义音效覆盖点击/松手并预加载 OK")

    pet.set_volume(55)
    assert all(p.volume == 55 for p in pool), [p.volume for p in pool]
    print("6. 音量同步池内全部播放器 OK")

    app.quit()
    print()
    print("音效自测结果: 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
