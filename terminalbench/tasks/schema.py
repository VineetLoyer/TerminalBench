from typing import Literal

from pydantic import BaseModel, Field

Split = Literal["train", "held_out"]
Difficulty = Literal["easy", "medium", "hard"]
Category = Literal["bugfix", "feature", "refactor", "debug", "config"]


class GraderSpec(BaseModel):
    command: str
    timeout_sec: int = 90
    regression_command: str | None = None


class Task(BaseModel):
    id: str
    repo: str
    title: str
    category: Category
    difficulty: Difficulty
    split: Split
    instruction: str
    timeout_sec: int = 600
    image: str = "python:3.12-slim"
    fixture: str | None = None
    ref: str | None = None
    grader: GraderSpec
    tags: list[str] = Field(default_factory=list)

    @property
    def repo_slug(self) -> str:
        return self.repo.split("/")[-1]
