import argparse
import json
from datetime import datetime
from pathlib import Path

import httpx

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
    report.add_argument("run_id", help="a run id in results/, or a path to a ledger CSV")

    run = sub.add_parser("run", help="run the live agent and write an episode ledger")
    run.add_argument("task_ids", nargs="*", help="defaults to every task in the configured splits")
    run.add_argument("--config", default=str(CONFIGS_DIR / "eval.yaml"))
    run.add_argument("--split", action="append", choices=["train", "held_out"])
    run.add_argument("--sandbox", choices=["local", "docker"])
    run.add_argument("--max-steps", type=int)
    run.add_argument("--fixtures-only", action="store_true")
    run.add_argument("--run-id", help="defaults to <date>-<model>")
    run.add_argument("--out", default="runs")

    clone = sub.add_parser("checkout", help="clone a spec task's upstream repository")
    clone.add_argument("task_id")
    clone.add_argument("dest", nargs="?", help="defaults to runs/checkouts/<task_id>")

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
        path = Path(args.run_id)
        if not path.is_file():
            path = RESULTS_DIR / f"{args.run_id}.csv"
        if not path.is_file():
            raise SystemExit(f"no run named {args.run_id}")
        records = load_run_csv(path)
        summary = {
            "overall": summarize_split(records, tasks, None).as_dict(),
            "train": summarize_split(records, tasks, "train").as_dict(),
            "held_out": summarize_split(records, tasks, "held_out").as_dict(),
        }
        print(json.dumps(summary, indent=2))
        return

    if args.cmd == "run":
        from terminalbench.agent.llm import client_from_env
        from terminalbench.harness.evaluate import load_eval_config, run_suite, select_tasks

        cfg = load_eval_config(Path(args.config))
        try:
            chosen = select_tasks(
                tasks, args.task_ids, args.split or cfg["splits"], args.fixtures_only
            )
        except KeyError as exc:
            raise SystemExit(exc.args[0]) from None
        if not chosen:
            raise SystemExit("no tasks selected")
        model = cfg.get("model")
        run_id = args.run_id or (
            f"{datetime.now().astimezone().date().isoformat()}-"
            f"{str(model or 'model').split('/')[-1].lower()}"
        )
        out_dir = Path(args.out) / run_id
        try:
            records = run_suite(
                chosen,
                lambda: client_from_env(model),
                out_dir,
                sandbox=args.sandbox or cfg["sandbox"],
                max_steps=args.max_steps or cfg["max_steps"],
                image_overrides=cfg["image_overrides"],
            )
        except httpx.ConnectError as exc:
            raise SystemExit(
                f"model endpoint unreachable ({exc}). Set OPENAI_BASE_URL to a running server."
            ) from None
        summary = {
            "run_id": run_id,
            "ledger": str(out_dir / f"{run_id}.csv"),
            "overall": summarize_split(records, tasks, None).as_dict(),
        }
        print(json.dumps(summary, indent=2))
        return

    if args.cmd == "checkout":
        from terminalbench.tasks.checkout import checkout, head

        task = next((item for item in tasks if item.id == args.task_id), None)
        if task is None:
            raise SystemExit(f"unknown task {args.task_id}")
        dest = Path(args.dest or Path("runs") / "checkouts" / task.id)
        checkout(task, dest)
        print(json.dumps({"task_id": task.id, "path": str(dest), "head": head(dest)}, indent=2))
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
