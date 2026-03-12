import { ApiDown, Shell } from "@/components/shell";
import { tryApi } from "@/lib/api";

export const dynamic = "force-dynamic";

type TrainResponse = {
  config: {
    base_model: string;
    method: string;
    lora: { r: number; alpha: number; dropout: number; target_modules: string[] };
    grpo: {
      learning_rate: number;
      beta: number;
      num_generations: number;
      max_steps: number;
      max_completion_length: number;
    };
    reward: { success: number; regression_penalty: number; format_bonus: number };
  };
  reward_curve: { step: number; mean_reward: number }[];
};

export default async function TrainingPage() {
  const data = await tryApi<TrainResponse>("/training");
  if (!data) return <ApiDown />;
  const max = Math.max(...data.reward_curve.map((point) => point.mean_reward), 0.01);
  return (
    <Shell>
      <h1 className="text-2xl font-medium tracking-tight">QLoRA / GRPO</h1>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
        The adapter is trained on the 25-task train split. Each GRPO group samples{" "}
        {data.config.grpo.num_generations} completions. The reward is 1 for a clean pass, minus{" "}
        {data.config.reward.regression_penalty} when a regression check fails, plus{" "}
        {data.config.reward.format_bonus} when the executor emits a JSON command.
      </p>
      <dl className="mt-6 grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Base model" value={data.config.base_model} />
        <Field label="Method" value={data.config.method} />
        <Field label="LoRA" value={`r=${data.config.lora.r}, alpha=${data.config.lora.alpha}`} />
        <Field label="Learning rate" value={String(data.config.grpo.learning_rate)} />
        <Field label="KL beta" value={String(data.config.grpo.beta)} />
        <Field label="Max steps" value={String(data.config.grpo.max_steps)} />
      </dl>
      <h2 className="mt-8 text-base font-medium">Train reward</h2>
      <div className="mt-4 flex h-40 items-end gap-1">
        {data.reward_curve.map((point) => (
          <div key={point.step} className="flex flex-1 flex-col items-center gap-1">
            <div
              className="w-full rounded-sm bg-primary"
              style={{ height: `${(point.mean_reward / max) * 100}%` }}
              title={`step ${point.step}: ${point.mean_reward}`}
            />
            <span className="font-mono text-[10px] text-muted-foreground">{point.step}</span>
          </div>
        ))}
      </div>
      <p className="mt-3 text-xs text-muted-foreground">
        Mean reward on the train groups. Held-out tasks are not in this curve. Target modules:{" "}
        {data.config.lora.target_modules.join(", ")}.
      </p>
      <pre className="mt-6 overflow-x-auto rounded-lg border border-border bg-card p-3 font-mono text-xs">
        terminalbench train --config configs/train.yaml --dry-run
      </pre>
    </Shell>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border p-3">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-mono text-sm">{value}</dd>
    </div>
  );
}
