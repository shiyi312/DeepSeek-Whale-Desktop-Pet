# -*- coding: utf-8 -*-
"""静态分析：语法编译 + pyflakes（未定义变量/重复定义/未使用）+ 自定义 AST 检查。

用法：python tests/check_static.py
本脚本不需要 Qt，仅分析源码文本。
"""
import ast
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "whale_pet.py")


def check_compile():
    import py_compile
    try:
        py_compile.compile(SRC, doraise=True)
        print("[OK] 语法编译通过")
        return True
    except Exception as e:
        print("[FAIL] 语法错误:", e)
        return False


def check_pyflakes():
    try:
        import pyflakes  # noqa: F401
    except ImportError:
        print("[跳过] 未安装 pyflakes（可运行: pip install pyflakes）")
        return True
    r = subprocess.run([sys.executable, "-m", "pyflakes", SRC],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    lines = [l for l in out.splitlines() if l.strip()]
    if not lines:
        print("[OK] pyflakes 无问题（未定义变量 / 重复定义 / 未使用变量）")
        return True
    print(f"[WARN] pyflakes 报告 {len(lines)} 条：")
    for l in lines[:20]:
        print("   ", l)
    return False


def check_ast_patterns():
    """自定义检查：注释里被吞掉的代码、可疑的连续赋值、除零、过长函数等。"""
    src = open(SRC, encoding="utf-8").read()
    problems = []

    # 1) 真注释里出现 `= ` 赋值（历史上出现过赋值被并入注释导致 NameError 的事故）
    #    用 tokenize 只扫注释 token，避免把字符串模板里的说明文字当成注释
    import io
    import tokenize
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT and re.search(r"\b\w+\s*=\s*[^=]", tok.string):
                if not re.search(r"[\u4e00-\u9fff]", tok.string):   # 中文说明行不算
                    problems.append(f"{tok.start[0]}: 注释行里疑似包含赋值语句 → {tok.string[:60]}")
    except Exception:
        pass

    # 2) 函数内使用但未定义的局部变量（简易数据流检查）
    import builtins
    tree = ast.parse(src)
    module_names = set(dir(builtins)) | {"self", "cls", "__file__", "__name__", "__doc__", "__spec__"}

    def collect_names(node, target):
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                target.add(sub.id)
            elif isinstance(sub, (ast.Import, ast.ImportFrom)):
                for a in sub.names:
                    target.add((a.asname or a.name).split(".")[0])
            elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                target.add(sub.name)

    for node in tree.body:                      # 模块级定义/导入都算已知名字
        collect_names(node, module_names)

    def collect_assigned(fn):
        """收集一个函数内绑定的所有名字（参数/赋值/import/嵌套定义）。"""
        names = set()
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, (ast.Store, ast.Del)):
                names.add(sub.id)
            elif isinstance(sub, ast.arg):
                names.add(sub.arg)
            elif isinstance(sub, (ast.Import, ast.ImportFrom)):
                for a in sub.names:
                    names.add((a.asname or a.name).split(".")[0])
            elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                    and sub is not fn:
                names.add(sub.name)
        return names

    def check_func(fn, inherited):
        """检查函数体引用的名字是否可见（含闭包外层作用域）。"""
        visible = set(inherited) | collect_assigned(fn)
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                if sub.id not in visible:
                    problems.append(f"{sub.lineno}: 函数 {fn.name} 中疑似未定义变量 {sub.id}")
                    break
        for child in ast.iter_child_nodes(fn):      # 嵌套函数继承当前作用域
            walk(child, visible)

    def walk(node, inherited):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                check_func(child, inherited)
            else:
                walk(child, inherited)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            check_func(node, module_names)      # 顶层函数：带上模块级名字
        else:
            walk(node, module_names)

    # 3) 过长的函数（可维护性提示，不算错误）
    long_funcs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            span = (node.end_lineno or node.lineno) - node.lineno
            if span > 120:
                long_funcs.append((node.name, node.lineno, span))

    if problems:
        print(f"[WARN] AST 检查发现 {len(problems)} 条可疑项：")
        for p in problems[:20]:
            print("   ", p)
    else:
        print("[OK] AST 检查通过（无注释吞代码、无未定义变量）")
    if long_funcs:
        print("   （提示）较长函数：", ", ".join(f"{n}({s}行)" for n, _, s in long_funcs[:5]))
    return not problems


def main():
    print("=" * 56)
    print("静态分析（pyflakes + AST）")
    print("=" * 56)
    ok = True
    ok &= check_compile()
    ok &= check_pyflakes()
    ok &= check_ast_patterns()
    print()
    print("静态分析结果:", "通过" if ok else "有需要修复的问题")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
