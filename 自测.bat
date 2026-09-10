@echo off
chcp 65001 > nul
cd /d "%~dp0"
set REPORT=tests\自测报告.txt

echo ============================================================> "%REPORT%"
echo   小鲸鱼桌宠 自测报告   %date% %time%>> "%REPORT%"
echo ============================================================>> "%REPORT%"
echo.>> "%REPORT%"

echo [1/4] 静态分析（编译 + pyflakes + AST 扫描）...
echo ---------- 1. 静态分析 ---------->> "%REPORT%"
python tests\check_static.py >> "%REPORT%" 2>&1

echo [2/4] 动态遍历（面板全控件 + 日常操作压测）...
echo.>> "%REPORT%"
echo ---------- 2. 动态遍历压测 ---------->> "%REPORT%"
python tests\check_dynamic.py >> "%REPORT%" 2>&1

echo [3/4] 启动性能与启动瞬间朝向...
echo.>> "%REPORT%"
echo ---------- 3. 启动性能 / 朝向 ---------->> "%REPORT%"
python tests\check_startup.py >> "%REPORT%" 2>&1

echo [4/4] 音效系统...
echo.>> "%REPORT%"
echo ---------- 4. 音效系统 ---------->> "%REPORT%"
python tests\check_sound.py >> "%REPORT%" 2>&1

echo.>> "%REPORT%"
echo ============================================================>> "%REPORT%"
echo   自测结束，请查看 tests\自测报告.txt>> "%REPORT%"

echo.
echo 自测完成！报告已保存到： tests\自测报告.txt
echo.
type "%REPORT%"
pause
