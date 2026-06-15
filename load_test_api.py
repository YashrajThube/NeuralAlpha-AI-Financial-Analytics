"""Root entrypoint for API load test.

Usage:
    python load_test_api.py
"""

from pathlib import Path
import runpy


if __name__ == '__main__':
    script_path = Path(__file__).resolve().parent / 'backend' / 'scripts' / 'load_test_api.py'
    runpy.run_path(str(script_path), run_name='__main__')
