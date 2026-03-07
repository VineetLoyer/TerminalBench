import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from terminalbench.sandbox.base import ExecResult, GradeResult, Sandbox


def remove_tree(path: Path) -> None:
    # Git pack files are read-only, which makes a plain rmtree fail on Windows.
    def _retry(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    if not path.exists():
        return
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_retry)
    else:
        shutil.rmtree(path, onerror=_retry)


def shell_argv(command: str) -> list[str] | str:
    # On Windows, `bash` on PATH is often the WSL launcher, which runs in a different
    # filesystem and Python. cmd.exe keeps the command next to this interpreter.
    if os.name == "nt":
        return command
    return ["bash", "-lc", command]


class LocalSandbox(Sandbox):
    """Developer fallback. Copies a fixture into a temp dir. Not a security boundary."""

    def __init__(self, workspace: Path, hidden: Path | None = None):
        self._root = Path(tempfile.mkdtemp(prefix="tb-"))
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
            argv = shell_argv(command)
            proc = subprocess.run(
                argv,
                shell=isinstance(argv, str),
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
        remove_tree(self._root)
