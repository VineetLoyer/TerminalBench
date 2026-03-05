from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExecResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_sec: float
    timed_out: bool = False


@dataclass
class GradeResult:
    success: bool
    regression: bool
    target: ExecResult
    regression_result: ExecResult | None = None
    notes: list[str] = field(default_factory=list)


class Sandbox:
    """Isolated workspace. DockerSandbox is the supported path for untrusted code."""

    def exec(self, command: str, timeout: int = 60) -> ExecResult:
        raise NotImplementedError

    def grade(self, command: str, regression_command: str | None, timeout: int) -> GradeResult:
        raise NotImplementedError

    def close(self) -> None:
        return None

    @property
    def workdir(self) -> Path:
        raise NotImplementedError
