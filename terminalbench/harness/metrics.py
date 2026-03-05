from dataclasses import dataclass

from pydantic import BaseModel

# Accounting rates shared by local and API-served runs.
# GPU time is the dominant term for a self-hosted 3B; token rates keep
# hosted comparisons on the same ledger.
DEFAULT_INPUT_USD_PER_MTOK = 0.15
DEFAULT_OUTPUT_USD_PER_MTOK = 0.60
DEFAULT_GPU_USD_PER_HOUR = 2.40


class EpisodeRecord(BaseModel):
    task_id: str
    success: bool
    regression: bool
    steps: int
    latency_sec: float
    prompt_tokens: int
    completion_tokens: int

    def cost_usd(
        self,
        input_per_mtok: float = DEFAULT_INPUT_USD_PER_MTOK,
        output_per_mtok: float = DEFAULT_OUTPUT_USD_PER_MTOK,
        gpu_hourly: float = DEFAULT_GPU_USD_PER_HOUR,
    ) -> float:
        tokens = (
            self.prompt_tokens * input_per_mtok + self.completion_tokens * output_per_mtok
        ) / 1_000_000
        gpu = (self.latency_sec / 3600) * gpu_hourly
        return tokens + gpu


@dataclass
class Aggregate:
    n: int
    n_success: int
    success_rate: float
    n_regression: int
    regression_rate: float
    latency_p50: float
    latency_p95: float
    mean_prompt_tokens: float
    mean_completion_tokens: float
    total_cost_usd: float
    mean_cost_usd: float

    def as_dict(self) -> dict:
        return {
            "n": self.n,
            "n_success": self.n_success,
            "success_rate": self.success_rate,
            "n_regression": self.n_regression,
            "regression_rate": self.regression_rate,
            "latency_p50": self.latency_p50,
            "latency_p95": self.latency_p95,
            "mean_prompt_tokens": self.mean_prompt_tokens,
            "mean_completion_tokens": self.mean_completion_tokens,
            "total_cost_usd": self.total_cost_usd,
            "mean_cost_usd": self.mean_cost_usd,
        }


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def aggregate(records: list[EpisodeRecord]) -> Aggregate:
    n = len(records)
    if n == 0:
        return Aggregate(0, 0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    successes = sum(1 for row in records if row.success)
    regressions = sum(1 for row in records if row.regression)
    costs = [row.cost_usd() for row in records]
    latencies = [row.latency_sec for row in records]
    return Aggregate(
        n=n,
        n_success=successes,
        success_rate=successes / n,
        n_regression=regressions,
        regression_rate=regressions / n,
        latency_p50=_percentile(latencies, 0.50),
        latency_p95=_percentile(latencies, 0.95),
        mean_prompt_tokens=sum(row.prompt_tokens for row in records) / n,
        mean_completion_tokens=sum(row.completion_tokens for row in records) / n,
        total_cost_usd=sum(costs),
        mean_cost_usd=sum(costs) / n,
    )
