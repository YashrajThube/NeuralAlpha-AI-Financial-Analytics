"""Fail if production code introduces legacy /api endpoints.

Policy:
- /api/v1 is the only contract allowed in application and frontend source code.
- /api compatibility is temporarily allowed only in app/main.py where routing and usage logging live.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]

# Production code only. Tests/docs are intentionally excluded.
SCAN_TARGETS = [
    ROOT / 'backend' / 'app',
    ROOT / 'frontend' / 'src',
    ROOT / 'frontend' / 'vite.config.js',
]

# Temporary compatibility ownership is centralized in app/main.py.
ALLOW_LEGACY = {
    (ROOT / 'backend' / 'app' / 'main.py').resolve(),
}

TEXT_EXTENSIONS = {'.py', '.js', '.jsx', '.ts', '.tsx'}
LEGACY_PATTERN = re.compile(r"['\"`]/api(?!/v1)")


def _iter_files() -> list[Path]:
    files: list[Path] = []
    for target in SCAN_TARGETS:
        if target.is_file():
            files.append(target)
            continue
        if target.is_dir():
            for path in target.rglob('*'):
                if path.suffix.lower() in TEXT_EXTENSIONS and path.is_file():
                    files.append(path)
    return files


def main() -> int:
    violations: list[str] = []

    for path in _iter_files():
        resolved = path.resolve()
        if resolved in ALLOW_LEGACY:
            continue

        content = path.read_text(encoding='utf-8', errors='ignore').splitlines()
        for idx, line in enumerate(content, start=1):
            if '/api' not in line:
                continue
            if LEGACY_PATTERN.search(line):
                rel = path.relative_to(ROOT).as_posix()
                violations.append(f'{rel}:{idx}: {line.strip()}')

    if violations:
        print('Legacy /api usage found in production code. Use /api/v1 instead:')
        for item in violations:
            print(f'- {item}')
        return 1

    print('API contract check passed: no legacy /api usage outside compatibility gateway.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
