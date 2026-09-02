import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(script):
    path = os.path.join(ROOT, "scripts", script)
    if not os.path.isfile(path):
        print(f"错误：缺少 {path}")
        return 2
    p = subprocess.run([sys.executable, path], cwd=ROOT)
    return p.returncode


def main():
    code = run("fetch_hw.py")
    if code:
        return code
    return run("process.py")


if __name__ == "__main__":
    raise SystemExit(main())
