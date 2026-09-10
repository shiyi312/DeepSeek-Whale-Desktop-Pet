# 🐳 DeepSeek 小鲸鱼桌宠（Whale Desktop Pet）

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![GUI](https://img.shields.io/badge/GUI-PyQt5-41b883) ![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078d6) ![Version](https://img.shields.io/badge/Version-v4.1.0-orange)

**作者：shiyi312**　|　版本：`v4.1.0`　|　[开发者信息](#-开发者信息)

![DSH 小鲸鱼桌宠](assets/DSH2.png)

一个独立运行的 Windows 桌面宠物：**DeepSeek 小鲸鱼娘**。基于 PyQt5 单文件实现，
不依赖浏览器、不依赖 DSH，开箱即用。她住在你的桌面角落：会呼吸眨眼、Q 弹软乎乎，
帮你盯着 Token 余额，还能陪你摸鱼。

> 💡 本项目是从 [DeepSeek-WindowsTable-game.io（鲸鱼娘）](#-来源与致谢) 的玩法、
> [DeepSeek-Balance-Whale-Widget（DSH 余额挂件）](#-来源与致谢) 的交互风格、
> [DeepSeek-Whale-widget-desktop（独立桌面版）](#-来源与致谢) 的桌面形态
> 改造整合而来，并在其基础上重写了窗口、交互、Token 系统、气泡系统与设置面板。
> 详见文末「来源与致谢」。

---

## ✨ 特性

- 🧸 **Q 弹玩偶**：按压压扁回弹（底部坐标固定），自带弹簧手感
- 🖱️ **拖拽 + 四边四分之一吸附**：松手时中心落在屏幕某侧 25% 区域即贴边，角落可组合
- 🔄 **左吸附翻转**：贴左边缘自动水平镜像（面朝屏内），文字保持可读
- 🎯 **右键橡皮筋弹射**：拉得越远越「重」，松手弹射 + 屏幕边缘反弹角反射 + 音效
- 💰 **趣味 Token 系统**：点击消耗、拖文件/文件夹喂食（弹窗警告真实删除）、
  一键 +520W、清空、总开关
- 🔢 **数字滚动动画**：Token 变化时 700ms 缓动滚动，增加亮蓝 / 消耗红色反馈
- 🧾 **鲸鱼娘风格 HUD**：白色圆角框 + 深藏蓝 Token 数字 + 秒级时间，
  主题色随气泡联动，支持大数缩写（388.4W）
- 🫧 **气泡台词系统**：今日心情 / 随机 / 自定义 / 固定台词，
  自动关泡、4 种配色、字号 / 框大小 / 触发频率全可调
- 🐟 **互动玩法**：鼠标跟随、躲避鼠标（被逼到角落会瞬移到对角）、
  待机漫游（走走停停 + 边缘弱回正 + 交互即停）
- 🎨 **表情系统**：内置 v1~v4 表情包 + 默认表情 + Gif 摸头，
  连点 N 次换表情（1~100 可调）、自动轮换（5~100 秒可调）、空闲眨眼动画
- 🔊 **音效系统**：播放器池（连点每一声都完整、不重叠不延迟）、
  点击 / 松手 / 弹射 / 反弹音效、`sounds/` 目录放入 mp3 即可新增音效选项、
  支持自定义音效（覆盖全部音效）
- 📝 **台词与规则可外部编辑**：`.dshw-pet-lines.txt`（每行一句台词）与
  `.dshw-pet-rules.txt`（`匹配词 | 台词 | 触发概率 | 启用`，带完整注释说明），
  记事本改完点「重新加载」即生效
- ⚙️ **系统能力**：单实例锁、开机自启（自动修正失效路径）、
  独立运行日志（每次启动归档、保留 100 份）、应用打开监控 + 自定义规则与概率、
  自定义点击音效、GitHub 更新检查、磁盘图标美化（大肥鱼）、托盘右键菜单
- 🎚️ **多分区标签式设置面板**：深色玻璃风格，标题栏可拖动，离开面板自动关闭，
  低分辨率屏幕自动启用滚动
- 📏 **大小 0.6~2.5 倍**任意调节（档位 1~20）

---

## 🚀 快速开始

### 方式 A：直接下载运行（推荐）

1. 打开右侧 **[Releases](../../releases)** 页面
2. 下载最新版 `WhaleDesktopPet.zip`（包含独立 exe）
3. 解压后双击 `WhaleDesktopPet.exe`，小鲸鱼就出现了 🐳

> 无需安装 Python、无需联网、无需 DSH。

### 方式 B：源码运行

```powershell
# 1. 安装 Python 3.9+（勾选 Add to PATH）
# 2. 安装依赖
pip install PyQt5

# 3. 运行
python whale_pet.py
```

Windows 下也可直接双击 `run.bat`。

### 方式 C：自己打包 exe

双击 `build.bat`（或手动执行）：

```bat
python -m PyInstaller --noconfirm --onefile --windowed --name WhaleDesktopPet ^
  --icon expressions\DSniang1.png --add-data "expressions;expressions" whale_pet.py
```

---

## 🕹️ 玩法说明

| 操作 | 效果 |
| --- | --- |
| **左键单击** | 消耗 Token（200~50000），弹出一句台词气泡 |
| **左键连点** | 连续点击 N 次后轮换到下一个表情（默认 30 次，可在设置调整 1~100） |
| **左键拖拽** | 移动小鲸鱼；靠近屏幕边缘松手自动贴边吸附 |
| **贴到左边缘** | 自动水平翻转（面朝屏内） |
| **右键短按** | 打开设置面板（鼠标移出面板自动关闭；顶部标题栏可拖动，✕ 为备用关闭） |
| **右键拖拽** | 橡皮筋弹射：把鲸鱼娘往后拉（拉得越远越重），松手向反方向弹出，撞到屏幕边缘反弹并播音符 |
| **拖文件到角色** | 喂食！弹窗明确警告「文件会被真实删除」，按 1KB = 1 Token 结算 |
| **鼠标靠近** | 开启「躲避鼠标」后她会逃跑（被逼到角落会挣扎贴边） |
| **离开一阵** | 开启「待机漫游」后她会在桌面走走停停散步 |
| **托盘菜单** | 显示/隐藏、Token +520W、清空、切换置顶、重新加载表情、检查更新、打开日志等 |

---

## ⚙️ 设置面板一览

### 互动
表情切换 · **连点换表情（1~100 下）** · 大小（档位） · 音量 · 音效（小黄鸭/音效1）
鼠标跟随 · 躲避鼠标 · 待机漫游 · 贴边自动镜像（翻转） · 固定位置 ·
**拖拽吸附屏幕边缘** · 始终置顶

### Token
开启 Token 系统 · **显示 Token HUD** · **HUD 数字缩写（388.4W）** ·
当前 Token 余额 · +520W · 清空

### 气泡
台词模式（今日心情/随机/自定义/固定） · 自定义台词库增删 · 显示气泡 ·
自动关闭时间（1~10s） · 气泡颜色（蓝/粉/深/绿，HUD 同步换主题） ·
显示当前时间 · 时间问候（早/中/晚） · 气泡字号（10~24px） ·
气泡框大小（70%~140%） · 对话频率（1%~100%）

### 系统
自动轮换表情 + **间隔 5~100 秒** · 空闲自动表情动画 · 空闲自动眨眼 + 间隔 ·
开机自启（自动修正失效路径） · **应用打开监控**（匹配进程名/窗口标题 → 自定义台词与概率，
可增删/启停规则，也可直接编辑 `.dshw-pet-rules.txt`） ·
**编辑台词文件 / 编辑规则文件 / 重新加载台词与规则** · 检查更新 ·
自定义音效（设置/清除） · 美化磁盘图标（大肥鱼） · 打开运行日志

---

## 📁 目录结构

```text
DeepSeek-Whale-Desktop-Pet/
├── whale_pet.py            # 主程序（全部逻辑，单文件）
├── run.bat                 # 源码一键运行
├── build.bat               # 一键打包 exe
├── WhaleDesktopPet.spec    # PyInstaller 配置
├── README.md               # 本说明
├── assets/
│   └── DSH2.png            # README 封面图
├── expressions/            # 表情素材（v1~v4 + 默认表情 + Gif + 内置音效）
└── sounds/                 # 音效目录：放入 mp3/wav 即成为可选音效
    ├── 吐小泡泡.mp3  ├── 呀呼.mp3  ├── 啵.mp3   ├── 喵.mp3
    └── 曼波.mp3      ├── 玛卡巴卡.mp3       └── 酱酱.MP3
```

## 📄 配置与日志

- 配置文件：`C:\Users\<用户名>\.dshw-desktop-pet.json`（自动保存）
- **台词文件**：`C:\Users\<用户名>\.dshw-pet-lines.txt`（每行一句，`#` 为注释）
- **监测规则文件**：`C:\Users\<用户名>\.dshw-pet-rules.txt`
  格式：`匹配词 | 触发台词 | 触发概率(0-100) | 是否启用(1/0)`
  例：`steam | 又在打游戏啦 | 30 | 1`（30 = 30% 概率触发）；文件开头有完整注释说明
- 运行日志：`%TEMP%\dshw-pet.log`（每次启动归档，保留最近 100 份）
- 开机自启：写入注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
  （每次启动自动校验路径，失效会自动修正为当前程序）

## 🧩 自定义表情

把 `png / jpg / jpeg / webp / gif` 放进 `expressions\` 后，托盘菜单
「重新加载表情」即可（或重启）。文件名会自动出现在设置面板的表情列表，
支持 `v1_xxx / v2_xxx / v3_xxx / v4_xxx` 前缀分组显示。

## 🔊 自定义音效

把 `mp3 / wav / ogg / m4a` 放进 `sounds\` 目录，重启后在
**设置 → 互动 → 音效** 下拉框即可选到（文件名就是选项名）。
想让点击和松手用不同音效，命名 `名字_click.mp3` + `名字_release.mp3` 配对即可。
另外还支持 **自定义音效**（设置面板选择任意音频文件），它会覆盖点击 / 松手 /
弹射 / 反弹全部音效；不想用时点「清除自定义音效」。

---

## 🙏 来源与致谢

本项目由以下开源项目改造整合而来，在此向他们表示衷心感谢：

| 项目 | 借鉴内容 |
| --- | --- |
| [comreade-123/DeepSeek-Whale-widget-desktop](https://github.com/comreade-123/DeepSeek-Whale-widget-desktop) | 独立桌面版形态、HUD 窗口卡片样式、更新检查对齐、托盘交互思路 |
| [MeteorNOX/DeepSeek-Balance-Whale-Widget](https://github.com/MeteorNOX/DeepSeek-Balance-Whale-Widget) | 原版交互规范：四边四分之一吸附、左吸附翻转、数字滚动动画（700ms easeOutCubic）、Q 弹参数（底部锚点、scaleY 0.88/scaleX 1.05、OutBack 回弹）、HUD 主题联动 |
| [JiafishNB/DeepSeek-WindowsTable-game.io](https://github.com/JiafishNB/DeepSeek-WindowsTable-game.io) | 鲸鱼娘本体（表情/音效素材）、右键弹射物理（橡皮筋阻尼、角度反射反弹、B→A 方向发射）、躲避/跟随/待机漫游 tick 逻辑、鲸鱼娘风格 HUD（白框 + 深藏蓝数字）、喂食/连点互动玩法 |

> 如果你喜欢本项目，也请去给上面三个仓库点个 Star ⭐，感谢原作者的付出！

---

## 👨‍💻 开发者信息

| 项 | 内容 |
|---|---|
| 作者 | DeepSeek-Whale-Desktop-Pet 团队 |
| 版本 | v4.1.0 |
| QQ 交流群 | `254668799`（[点击搜索加群](https://qun.qq.com/qq/254668799)） |

> 🐛 使用中遇到问题？欢迎加入 QQ 交流群 `254668799` 反馈 bug 或提出建议；
> 也可以找我们讨论互动玩法、表情素材或一起开发桌宠功能。

---

## 📄 License

MIT License，详见 [LICENSE](LICENSE)。
<br>© 2026 DeepSeek-Whale-Desktop-Pet contributors
