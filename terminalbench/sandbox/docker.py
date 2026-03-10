import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from terminalbench.sandbox.base import ExecResult, GradeResult, Sandbox


class DockerSandbox(Sandbox):
    """One container per episode. Network off, no extra capabilities, memory capped."""

    def __init__(
        self,
        workspace: Path,
        image: str = "python:3.12-slim",
        memory: str = "1g",
        cpus: str = "1.0",
        hidden: Path | None = None,
    ):
        if shutil.which("docker") is None:
            raise RuntimeError("docker is not on PATH")
        self._image = image
        self._name = f"tb-{uuid.uuid4().hex[:10]}"
        self._host_work = Path(workspace).resolve()
        self._hidden = hidden
        # Match the host user so files the agent writes into the bind mount stay removable.
        user = ["--user", f"{os.getuid()}:{os.getgid()}"] if hasattr(os, "getuid") else []
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                self._name,
                *user,
                "--network",
                "none",
                "--cpus",
                cpus,
                "--memory",
                memory,
                "--pids-limit",
                "256",
                "--security-opt",
                "no-new-privileges",
                "-v",
                f"{self._host_work}:/work",
                "-w",
                "/work",
                image,
                "sleep",
                "infinity",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    @property
    def workdir(self) -> Path:
        return self._host_work

    def exec(self, command: str, timeout: int = 60) -> ExecResult:
        started = time.monotonic()
        try:
            proc = subprocess.run(
                ["docker", "exec", "-w", "/work", self._name, "bash", "-lc", command],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return ExecResult(
                command=command,
                exit_code=proc.returncode,
                stdout=proc.stdout[-8000:],
                stderr=proc.stderr[-8000:],
                duration_sec=time.monotonic() - started,
            )
        except subprocess.TimeoutExpired:
            return ExecResult(
                command=command,
                exit_code=124,
                stdout="",
                stderr="timeout",
                duration_sec=time.monotonic() - started,
                timed_out=True,
            )

    def grade(self, command: str, regression_command: str | None, timeout: int) -> GradeResult:
        if self._hidden and self._hidden.exists():
            dest = self._host_work / "tests"
            dest.mkdir(exist_ok=True)
            for path in self._hidden.glob("*.py"):
                shutil.copy(path, dest / path.name)
        target = self.exec(command, timeout=timeout)
        regression_result = None
        regression = False
        if regression_command:
            regression_result = self.exec(regression_command, timeout=timeout)
            regression = regression_result.exit_code != 0
        return GradeResult(
            success=target.exit_code == 0 and not regression,
            regression=regression,
            target=target,
            regression_result=regression_result,
        )

    def close(self) -> None:
        subprocess.run(
            ["docker", "rm", "-f", self._name],
            capture_output=True,
            text=True,
            check=False,
        )
