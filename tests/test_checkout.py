import shutil
import subprocess
from pathlib import Path

import pytest

from terminalbench.tasks.checkout import checkout, head, upstream_url
from terminalbench.tasks.loader import load_tasks

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=tb", "-c", "user.email=tb@example.com", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _upstream(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "upstream"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "README").write_text("v1\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "v1")
    _git(repo, "tag", "v1")
    first = _git(repo, "rev-parse", "HEAD")
    (repo / "README").write_text("v2\n")
    _git(repo, "commit", "-q", "-am", "v2")
    return repo, first, _git(repo, "rev-parse", "HEAD")


def test_upstream_url():
    task = next(t for t in load_tasks() if t.id == "fd-extension")
    assert upstream_url(task) == "https://github.com/sharkdp/fd.git"


def test_checkout_default_branch_and_ref(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TERMINALBENCH_CACHE", str(tmp_path / "cache"))
    upstream, first, latest = _upstream(tmp_path)
    task = next(t for t in load_tasks() if t.id == "fd-extension")

    tip = checkout(task, tmp_path / "tip", url=str(upstream))
    assert head(tip) == latest

    pinned = checkout(task.model_copy(update={"ref": "v1"}), tmp_path / "pinned", url=str(upstream))
    assert head(pinned) == first
    assert (pinned / "README").read_text().strip() == "v1"

    with pytest.raises(FileExistsError):
        checkout(task, tmp_path / "tip", url=str(upstream))
