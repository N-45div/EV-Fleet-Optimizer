import { FormEvent, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Rocket, Timer, SlidersHorizontal, Gauge, RefreshCcw } from "lucide-react";
import type { OptimizePayload, StatusResponse } from "../App";

interface Props {
  status: StatusResponse | null;
  loading: boolean;
  onOptimize: (payload: OptimizePayload) => Promise<void>;
  onCompare: (horizon?: number) => Promise<void>;
}

export function ScenarioForm({ status, loading, onOptimize, onCompare }: Props) {
  const [horizon, setHorizon] = useState<string>("");
  const [objective, setObjective] = useState<string>("");
  const [backend, setBackend] = useState<string>("");

  const defaults = useMemo(() => ({
    horizon: status?.horizon_default ?? 24,
    objective: status?.objective_default ?? "cost",
    backend: status?.backend ?? "greedy",
  }), [status]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const payload: OptimizePayload = {};
    const horizonNum = horizon.trim() ? Number(horizon) : undefined;
    if (horizonNum && !Number.isNaN(horizonNum)) payload.horizon = horizonNum;
    if (objective) payload.objective = objective as OptimizePayload["objective"];
    if (backend) payload.backend = backend as OptimizePayload["backend"];
    await onOptimize(payload);
  };

  const handleCompare = async () => {
    const horizonNum = horizon.trim() ? Number(horizon) : undefined;
    await onCompare(horizonNum);
  };

  return (
    <motion.form
      onSubmit={submit}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-md space-y-6"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">Scenario Setup</h2>
          <p className="text-sm text-muted">Adjust horizon, objective, and backend before running optimization.</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setHorizon(String(defaults.horizon));
            setObjective(defaults.objective);
            setBackend(defaults.backend);
          }}
          className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-muted hover:text-white transition"
        >
          <RefreshCcw className="w-3.5 h-3.5" />
          Fill defaults
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <label className="flex flex-col gap-2 text-sm">
          <span className="flex items-center gap-2 text-muted">
            <Timer className="w-4 h-4 text-accentSecondary" /> Horizon (hours)
          </span>
          <input
            value={horizon}
            onChange={(e) => setHorizon(e.target.value)}
            placeholder={String(defaults.horizon)}
            min={1}
            type="number"
            className="rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-accent/40"
          />
        </label>

        <label className="flex flex-col gap-2 text-sm">
          <span className="flex items-center gap-2 text-muted">
            <SlidersHorizontal className="w-4 h-4 text-accent" /> Objective
          </span>
          <select
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            className="rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-accent/40"
          >
            <option value="">default ({defaults.objective})</option>
            <option value="cost">Cost</option>
            <option value="peak">Peak</option>
          </select>
        </label>

        <label className="flex flex-col gap-2 text-sm">
          <span className="flex items-center gap-2 text-muted">
            <Gauge className="w-4 h-4 text-accent" /> Backend
          </span>
          <select
            value={backend}
            onChange={(e) => setBackend(e.target.value)}
            className="rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-accent/40"
          >
            <option value="">default ({defaults.backend})</option>
            <option value="greedy">Greedy</option>
            <option value="milp">MILP</option>
          </select>
        </label>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2 text-sm font-medium hover:bg-accent/80 transition disabled:opacity-60"
        >
          <Rocket className="w-4 h-4" />
          {loading ? "Optimizing..." : "Run Optimization"}
        </button>
        <button
          type="button"
          onClick={handleCompare}
          className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-transparent px-5 py-2 text-sm font-medium text-white/80 hover:text-white transition"
        >
          Compare cost vs peak
        </button>
      </div>
    </motion.form>
  );
}
