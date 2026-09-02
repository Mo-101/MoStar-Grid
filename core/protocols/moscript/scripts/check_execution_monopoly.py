"""Static check that the moscript binary is only invoked through RuntimeManager.

Scans Python source for subprocess/os.system calls that launch the moscript
native binary outside of the authorized wrappers:
  - core/protocols/moscript/runtime/process_supervisor.py
  - core/protocols/moscript/runtime/runtime_manager.py
"""
from __future__ import annotations

import ast
import os
import pathlib
import sys
from typing import Any


ALLOWED_FILES = {
    "core/protocols/moscript/runtime/process_supervisor.py",
    "core/protocols/moscript/runtime/runtime_manager.py",
}

MOSCRIPT_MARKERS = ("moscript", "moscript-")


def _is_moscript_command(value: ast.AST) -> bool:
    """Return True if an AST node looks like a moscript binary invocation."""
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        lowered = value.value.lower()
        return any(marker in lowered for marker in MOSCRIPT_MARKERS)
    if isinstance(value, ast.List | ast.Tuple) and value.elts:
        first = value.elts[0]
        return _is_moscript_command(first)
    return False


def _get_first_arg(args: list[ast.AST], keywords: list[ast.keyword]) -> ast.AST | None:
    if args:
        return args[0]
    for kw in keywords:
        if kw.arg in ("args", "cmd"):
            return kw.value
    return None


def _check_node(
    node: ast.AST, path: pathlib.Path, violations: list[dict[str, Any]]
) -> None:
    call = None
    if isinstance(node, ast.Call):
        call = node
    elif isinstance(node, ast.With):
        # e.g. with subprocess.Popen(...) as p:
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                call = item.context_expr

    if not isinstance(call, ast.Call):
        return

    func = call.func
    name = ""
    if isinstance(func, ast.Attribute):
        name = f"{ast.unparse(func.value)}.{func.attr}" if hasattr(ast, "unparse") else func.attr
    elif isinstance(func, ast.Name):
        name = func.id

    launchers = {
        "subprocess.Popen",
        "subprocess.run",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "os.system",
        "Popen",
        "run",
        "call",
        "system",
    }
    if name not in launchers:
        return

    first_arg = _get_first_arg(call.args, call.keywords)
    if first_arg is None:
        return
    if _is_moscript_command(first_arg):
        rel = path.relative_to(pathlib.Path(__file__).resolve().parents[5])
        violations.append(
            {
                "file": str(rel),
                "line": getattr(node, "lineno", 0),
                "call": name,
            }
        )


def _scan_file(path: pathlib.Path, violations: list[dict[str, Any]]) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return
    for node in ast.walk(tree):
        _check_node(node, path, violations)


def _is_in_allowed(path: pathlib.Path, repo: pathlib.Path) -> bool:
    rel = path.relative_to(repo)
    return str(rel) in ALLOWED_FILES


def main() -> int:
    repo = pathlib.Path(__file__).resolve().parents[5]
    root = repo / "core"
    violations: list[dict[str, Any]] = []

    for py_file in root.rglob("*.py"):
        if _is_in_allowed(py_file, repo):
            continue
        _scan_file(py_file, violations)

    if violations:
        for v in violations:
            rel = pathlib.Path(v["file"]).as_posix()
            print(f"EXECUTION_MONOPOLY_VIOLATION: {rel}:{v['line']} {v['call']}")
        return 1

    print("EXECUTION_MONOPOLY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
