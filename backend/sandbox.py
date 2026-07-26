"""Execute English Python source in an isolated subprocess with a timeout.

Never imports executor.py — subprocess isolation means the child process
has no knowledge of Hindi, and runs pure Python only.
"""

import subprocess
import sys


def run_in_sandbox(english_source: str, timeout_seconds: int = 5) -> tuple[str, str]:
    try:
        result = subprocess.run(
            [sys.executable, "-c", english_source],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return "", f"TimeoutError: execution exceeded {timeout_seconds}s"
    except Exception as exc:
        return "", f"SandboxError: {exc}"

    return result.stdout, result.stderr
