"""Module entry. Version guard runs before CLI/settings imports."""

from __future__ import annotations

import sys

from botmoduleproject1.app.exceptions import PythonVersionError
from botmoduleproject1.app.python_version import assert_python_version

if __name__ == "__main__":
    try:
        assert_python_version()
    except PythonVersionError as exc:
        print(f"STARTUP FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    from botmoduleproject1.cli.entrypoint import main

    raise SystemExit(main())
