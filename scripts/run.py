import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")


def run(name):
    path = os.path.join(SCRIPTS, name)
    if not os.path.isfile(path):
        print(f"错误：找不到 {path}", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, path], cwd=ROOT).returncode


if __name__ == "__main__":
    rc = run("fetch_hw.py")
    if rc:
        raise SystemExit(rc)
    raise SystemExit(run("process.py"))
