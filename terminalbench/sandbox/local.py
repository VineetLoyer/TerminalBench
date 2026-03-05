import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from terminalbench.sandbox.base import ExecResult, GradeResult, Sandbox


class LocalSandbox(Sandbox):
    """Developer fallback. Copies a fixture into a temp dir. Not a security boundary."""

    def __init__(self, workspace: Path, hidden: Path | None = None):
        self._root = Path(subprocess.check_output(["mktemp", "-d"], text=True).strip())
        self._work = self._root / "work"
        shutil.copytree(workspace, self._work)
        self._hidden = hidden

    @property
    def workdir(self) -> Path:
        return self._work

    def exec(self, command: str, timeout: int = 60) -> ExecResult:
        started = time.monotonic()
        try:
            env = os.environ.copy()
            bindir = str(Path(sys.executable).parent)
            env["PATH"] = bindir + os.pathsep + env.get("PATH", "")
            proc = subprocess.run(
                ["bash", "-lc", command],
                cwd=self._work,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                check=False,
            )
            return ExecResult(
                command=command,
                exit_code=proc.returncode,
                stdout=proc.stdout[-8000:],
                stderr=proc.stderr[-8000:],
                duration_sec=time.monotonic() - started,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", "replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", "replace")
            return ExecResult(
                command=command,
                exit_code=124,
                stdout=stdout[-8000:],
                stderr=(stderr + "\ntimeout")[-8000:],
                duration_sec=time.monotonic() - started,
                timed_out=True,
            )

    def grade(self, command: str, regression_command: str | None, timeout: int) -> GradeResult:
        if self._hidden and self._hidden.exists():
            dest = self._work / "tests"
            dest.mkdir(exist_ok=True)
            for path in self._hidden.glob("*.py"):
                shutil.copy(path, dest / path.name)
        target = self.exec(command, timeout=timeout)
        regression_result = None
        regression = False
        if regression_command:
            regression_result = self.exec(regression_command, timeout=timeout)
            regression = regression_result.exit_code != 0
        success = target.exit_code == 0 and not regression
        return GradeResult(
            success=success,
            regression=regression,
            target=target,
            regression_result=regression_result,
        )

    def close(self) -> None:
        shutil.rmtree(self._root, ignore_errors=True)
