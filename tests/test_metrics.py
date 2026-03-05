from terminalbench.harness.report import load_run_csv, summarize_split
from terminalbench.paths import RESULTS_DIR
from terminalbench.tasks.loader import load_tasks
from terminalbench.training.reward import score_grade


def test_recorded_headline_numbers():
    tasks = load_tasks()
    tuned = load_run_csv(RESULTS_DIR / "2026-03-03-qlora-grpo.csv")
    base = load_run_csv(RESULTS_DIR / "2026-02-24-baseline.csv")

    tuned_all = summarize_split(tuned, tasks, None)
    tuned_held = summarize_split(tuned, tasks, "held_out")
    base_held = summarize_split(base, tasks, "held_out")

    assert tuned_all.n == 60
    assert tuned_all.n_success == 35
    assert round(tuned_all.success_rate, 2) == 0.58
    assert base_held.n_success == 12
    assert round(base_held.success_rate, 2) == 0.34
    assert tuned_held.n_success == 18
    assert round(tuned_held.success_rate, 2) == 0.51
    assert tuned_all.n_regression == 6
    assert tuned_all.total_cost_usd > 0
    assert tuned_all.latency_p50 > 0


def test_reward_penalizes_regressions():
    assert score_grade(True, False, True) == 1.1
    assert score_grade(False, True, True) == -0.4
    assert score_grade(False, False, False) == 0.0
