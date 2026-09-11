@echo off
chcp 65001 > nul
cd /d "%~dp0"
set REPORT=tests\自测报告.txt

echo ============================================================> "%REPORT%"
echo   小鲸鱼桌宠 自测报告   %date% %time%>> "%REPORT%"
echo ============================================================>> "%REPORT%"
echo.>> "%REPORT%"

echo [1/12] 静态分析（编译 + pyflakes + AST 扫描）...
echo ---------- 1. 静态分析 ---------->> "%REPORT%"
python tests\check_static.py >> "%REPORT%" 2>&1

echo [2/12] 动态遍历（面板全控件 + 日常操作压测）...
echo.>> "%REPORT%"
echo ---------- 2. 动态遍历压测 ---------->> "%REPORT%"
python tests\check_dynamic.py >> "%REPORT%" 2>&1

echo [3/12] 启动性能与启动瞬间朝向...
echo.>> "%REPORT%"
echo ---------- 3. 启动性能 / 朝向 ---------->> "%REPORT%"
python tests\check_startup.py >> "%REPORT%" 2>&1

echo [4/12] UI 完整性（越界/截断/交互有效性/边缘像素）...
echo.>> "%REPORT%"
echo ---------- 4. UI 完整性 ---------->> "%REPORT%"
python tests\check_ui.py >> "%REPORT%" 2>&1

echo [5/12] 音效系统...
echo.>> "%REPORT%"
echo ---------- 4. 音效系统 ---------->> "%REPORT%"
python tests\check_sound.py >> "%REPORT%" 2>&1

echo [6/12] 应用监控行为（冷却/标题兜底/自动重载）...
echo.>> "%REPORT%"
echo ---------- 5. 应用监控行为 ---------->> "%REPORT%"
python tests\check_app_monitor.py >> "%REPORT%" 2>&1

echo [7/12] HUD 显示（Token 与时间独立/日期星期/字号）...
echo.>> "%REPORT%"
echo ---------- 6. HUD 显示 ---------->> "%REPORT%"
python tests\check_hud.py >> "%REPORT%" 2>&1

echo [8/12] 气泡边界（贴四边不被截断）...
echo.>> "%REPORT%"
echo ---------- 8. 气泡边界 ---------->> "%REPORT%"
python tests\check_bubble.py >> "%REPORT%" 2>&1

echo [9/12] 滚轮误操作（滑块/下拉/标签栏）...
echo.>> "%REPORT%"
echo ---------- 9. 滚轮误操作 ---------->> "%REPORT%"
python tests\check_wheel.py >> "%REPORT%" 2>&1

echo [10/12] 气泡渲染（像素级方向验证）...
echo.>> "%REPORT%"
echo ---------- 10. 气泡渲染 ---------->> "%REPORT%"
python tests\check_bubble_render.py >> "%REPORT%" 2>&1

echo [11/12] 崩溃回归与日志清理...
echo.>> "%REPORT%"
echo ---------- 7. 崩溃回归 / 日志清理 ---------->> "%REPORT%"
python tests\check_monitor.py >> "%REPORT%" 2>&1

echo [12/12] 新功能（全屏隐藏/面板/全局搜索/自动更新）...
echo.>> "%REPORT%"
echo ---------- 12. 新功能 ---------->> "%REPORT%"
python tests\check_features.py >> "%REPORT%" 2>&1

echo.>> "%REPORT%"
echo ============================================================>> "%REPORT%"
echo   自测结束，请查看 tests\自测报告.txt>> "%REPORT%"

echo.
echo 自测完成！报告已保存到： tests\自测报告.txt
echo.
type "%REPORT%"
pause
