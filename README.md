# TerminalBench

Terminal-agent training and evaluation. A task runs in a sandbox. A planner writes the steps, an executor issues one shell command at a time, and a reviewer decides whether to continue, replan, or submit. The harness scores the episode on the target tests, on regressions, and on latency, tokens, and cost.

The March 2026 run used this loop to QLoRA/GRPO-tune Qwen2.5-3B-Instruct.

| | Base 3B | QLoRA/GRPO |
| --- | ---: | ---: |
| All 60 tasks | 22/60 (37%) | 35/60 (58%) |
| Held-out, 35 tasks | 12/35 (34%) | 18/35 (51%) |
| Regressions | 9 | 6 |
| Latency p50 | 55s | 58s |
| Run cost | $2.46 | $2.45 |

Cost is GPU time at $2.40/hour plus a token accounting rate of $0.15 / $0.60 per million input and output tokens. The held-out tasks were not in the GRPO prompt set.

## Layout

```
terminalbench/     agent loop, sandbox, harness, training, API
tasks/bank/        60 task specs, 12 each across five repositories
tasks/fixtures/    minimized repros used by the smoke grader
results/           March 2026 episode ledgers
configs/           eval and QLoRA/GRPO settings
apps/web/          Next.js dashboard
```

Repositories in the bank: [pallets/click](https://github.com/pallets/click), [Textualize/rich](https://github.com/Textualize/rich), [httpie/cli](https://github.com/httpie/cli), [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep), [sharkdp/fd](https://github.com/sharkdp/fd).

Five tasks ship with a local fixture, public tests, hidden grader tests, and a reference fix. The other fifty-five are specs whose graders run inside the upstream checkout. `DockerSandbox` is the boundary for those. `LocalSandbox` is a temp-dir copy for fixtures and is not a security boundary.

## Run it

Python 3.11+ and Node 22.

```bash
make install
make test
make serve          # API on :8741
make web            # dashboard on :8742
```

Open http://127.0.0.1:8742.

```bash
terminalbench tasks
terminalbench grade click-default-envvar --solution
terminalbench report 2026-03-03-qlora-grpo
terminalbench train --dry-run
terminalbench run --fixtures-only             # live agent on the five fixtures
terminalbench run fd-extension --sandbox docker
terminalbench checkout fd-extension           # upstream clone into runs/checkouts/
```

`terminalbench run` reads `configs/eval.yaml` (sandbox, step budget, model, splits) and writes `runs/<run-id>/<run-id>.csv` in the same format as `results/`, plus one trajectory JSON per task. `terminalbench report runs/<run-id>/<run-id>.csv` summarizes it. An episode that errors is recorded as a failure and the run continues. An unreachable model endpoint stops the run.

Spec tasks are cloned from GitHub into a bare mirror under `~/.cache/terminalbench/repos` (override with `TERMINALBENCH_CACHE`) and then cloned again into a fresh workspace per episode. A task's optional `ref` pins a tag, branch, or commit; without it the default branch is used. Docker runs swap `python:3.12-slim` for the `terminalbench-sandbox` image (`make sandbox-image`) so pytest is available with the network off.

`--dry-run` writes the 25 train prompts and the resolved config. It does not download weights. The real train path is `terminalbench train --config configs/train.yaml` and needs the `train` extra (`transformers`, `peft`, `trl`, `bitsandbytes`).

Redis is optional. Set `TERMINALBENCH_REDIS_URL` and the API keeps run summaries there. If Redis is down, it uses memory. `docker compose up` starts Redis, the API, and the dashboard.

An OpenAI-compatible endpoint drives the live agent (`OPENAI_BASE_URL`, `OPENAI_API_KEY`, `TERMINALBENCH_MODEL_NAME`). vLLM serving the 3B, or the adapter, is enough. The checked-in numbers come from the ledgers in `results/`, not from a fresh model call.

## Agent

Each episode:

1. Planner returns a JSON plan from the task text and a directory listing.
2. Executor returns one shell command.
3. The sandbox runs it with a timeout, network off when Docker is used.
4. Reviewer returns `continue`, `replan`, or `submit`.
5. The grader runs the target command, then the regression command. Success means the target passed and the regression command did too.

Docker flags: `--network none`, `--cpus 1`, `--memory 1g`, `--pids-limit 256`, `no-new-privileges`.

## Training

`configs/train.yaml` is the March run: 4-bit NF4, LoRA r=16 on the attention and MLP projections, GRPO with 4 samples, beta 0.04, 400 steps, learning rate 5e-6. Reward is `1.0` for a clean pass, `-0.5` for a regression, `+0.1` if the completion is well-formed JSON.

Each prompt asks for `{"commands": [...]}`. `SandboxReward` replays those commands in a fresh sandbox for the prompt's task, runs the grader, and scores the result, so a completion is only rewarded for what it actually changes. The sandbox and weights come from the `reward` block of `configs/train.yaml`.

## Task format

```yaml
id: click-default-envvar
repo: pallets/click
split: train          # or held_out
fixture: click-default-envvar   # optional, maps to tasks/fixtures/<id>
ref: v8.1.7           # optional upstream tag, branch, or commit for spec tasks
grader:
  command: python -m pytest tests/test_hidden.py tests/test_public.py -q
  regression_command: python -m pytest tests/test_public.py -q
```

Hidden tests are copied in only at grade time. The reference fix lives in `solution/` and is what `terminalbench grade <id> --solution` applies. It is not a model.

## License

MIT. Vineet Loyer, 2026.
