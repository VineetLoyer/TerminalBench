import argparse
import json
from pathlib import Path

from terminalbench.harness.report import load_run_csv, summarize_split
from terminalbench.harness.runner import grade_workspace
from terminalbench.paths import CONFIGS_DIR, RESULTS_DIR
from terminalbench.tasks.loader import load_tasks
from terminalbench.training.grpo import prepare


def main() -> None:
    parser = argparse.ArgumentParser(prog="terminalbench")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("tasks", help="list the task bank")

    grade = sub.add_parser("grade", help="grade a fixture, with or without the reference fix")
    grade.add_argument("task_id")
    grade.add_argument("--solution", action="store_true")

    report = sub.add_parser("report", help="summarize a recorded run CSV")
    report.add_argument("run_id")

    train = sub.add_parser("train", help="prepare or launch QLoRA/GRPO")
    train.add_argument("--config", default=str(CONFIGS_DIR / "train.yaml"))
    train.add_argument("--dry-run", action="store_true")
    train.add_argument("--out", default="runs/prepare")

    serve = sub.add_parser("serve", help="run the API")
    serve.add_argument("--port", type=int, default=8741)
    serve.add_argument("--host", default="0.0.0.0")

    args = parser.parse_args()
    tasks = load_tasks()

    if args.cmd == "tasks":
        for task in tasks:
            mark = "fixture" if task.fixture else "spec"
            print(f"{task.split:8}  {mark:7}  {task.repo:22}  {task.id}")
        print(f"{len(tasks)} tasks")
        return

    if args.cmd == "grade":
        task = next((item for item in tasks if item.id == args.task_id), None)
        if task is None or not task.fixture:
            raise SystemExit(f"no fixture for {args.task_id}")
        print(json.dumps(grade_workspace(task, use_solution=args.solution), indent=2))
        return

    if args.cmd == "report":
        path = RESULTS_DIR / f"{args.run_id}.csv"
        records = load_run_csv(path)
        summary = {
            "overall": summarize_split(records, tasks, None).as_dict(),
            "train": summarize_split(records, tasks, "train").as_dict(),
            "held_out": summarize_split(records, tasks, "held_out").as_dict(),
        }
        print(json.dumps(summary, indent=2))
        return

    if args.cmd == "train":
        summary = prepare(Path(args.config), tasks, Path(args.out))
        print(json.dumps(summary, indent=2))
        if args.dry_run:
            return
        from terminalbench.training.grpo import train as run_train

        run_train(Path(args.config), Path(args.out) / "train.jsonl", Path(args.out))
        return

    if args.cmd == "serve":
        import uvicorn

        uvicorn.run("terminalbench.api.app:app", host=args.host, port=args.port, reload=False)
