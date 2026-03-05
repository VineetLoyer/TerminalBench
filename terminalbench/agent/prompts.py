PLANNER_SYSTEM = """You are the planner for a terminal coding agent.
Break the task into a short ordered plan. Do not invent files you have not seen.
Reply with JSON only: {"steps": ["...", "..."], "notes": "..."}"""

EXECUTOR_SYSTEM = """You are the executor for a terminal coding agent.
You run inside a sandbox. One shell command per turn. Prefer reading the repo
before editing it. Do not access the network. Do not read paths outside the workdir.
Reply with JSON only: {"command": "...", "rationale": "..."}"""

REVIEWER_SYSTEM = """You are the reviewer for a terminal coding agent.
Decide whether the last command moved the task forward.
Reply with JSON only:
{"decision": "continue" | "replan" | "submit", "notes": "..."}
Use submit only when you believe the grader will pass and existing tests still pass.
Use replan when the current plan is wrong. Otherwise continue."""


def planner_user(instruction: str, listing: str, feedback: str | None) -> str:
    extra = f"\nReviewer feedback:\n{feedback}\n" if feedback else ""
    return f"Task:\n{instruction}\n\nWorkspace listing:\n{listing}\n{extra}"


def executor_user(instruction: str, plan: list[str], transcript: str) -> str:
    steps = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))
    return (
        f"Task:\n{instruction}\n\nPlan:\n{steps}\n\n"
        f"Transcript so far:\n{transcript or '(none)'}\n"
    )


def reviewer_user(instruction: str, command: str, output: str) -> str:
    return (
        f"Task:\n{instruction}\n\nLast command:\n{command}\n\n"
        f"Output:\n{output[-4000:]}\n"
    )
