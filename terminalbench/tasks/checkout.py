"""Upstream checkouts for spec tasks.

Each repository is cloned once into a cache and then cloned locally into a
fresh workspace per episode, so an agent can edit and `git diff` freely without
touching the cache.
"""

import os
import shutil
import subprocess
from pathlib import Path

from terminalbench.tasks.schema import Task


def cache_dir() -> Path:
    default = Path.home() / ".cache" / "terminalbench"
    return Path(os.environ.get("TERMINALBENCH_CACHE", default)) / "repos"


def upstream_url(task: Task) -> str:
    return f"https://github.com/{task.repo}.git"


def _git(*args: str, cwd: Path | None = None) -> str:
    if shutil.which("git") is None:
        raise RuntimeError("git is not on PATH")
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def mirror(task: Task, url: str | None = None) -> Path:
    """Clone or refresh the cached bare mirror of the task's repository."""
    path = cache_dir() / (task.repo.replace("/", "__") + ".git")
    if (path / "HEAD").is_file():
        _git("remote", "update", "--prune", cwd=path)
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    _git("clone", "--quiet", "--mirror", url or upstream_url(task), str(path))
    return path


def _resolve(ref: str, cwd: Path) -> str:
    for candidate in (ref, f"origin/{ref}"):
        try:
            return _git("rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}", cwd=cwd)
        except RuntimeError:
            continue
    raise RuntimeError(f"ref {ref!r} not found")


def checkout(task: Task, dest: Path, url: str | None = None) -> Path:
    """Materialize the task's repository at `task.ref` (default branch if unset) in `dest`."""
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError(f"{dest} is not empty")
    source = mirror(task, url=url)
    _git("clone", "--quiet", "--no-hardlinks", str(source), str(dest))
    if task.ref:
        _git("checkout", "--quiet", "--detach", _resolve(task.ref, dest), cwd=dest)
    return dest


def head(path: Path) -> str:
    return _git("rev-parse", "HEAD", cwd=path)
