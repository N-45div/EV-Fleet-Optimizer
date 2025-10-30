import { motion } from "framer-motion";
import { BadgeCheck, Flame, PiggyBank } from "lucide-react";
import type { OptimizerResponse } from "../App";

interface Props {
  optimizerState: OptimizerResponse | null;
}

const formatDelta = (num: number) => {
  if (!Number.isFinite(num)) return "±0";
  if (Math.abs(num) < 0.01) return "±0";
  return num > 0 ? `+${num.toFixed(1)}` : num.toFixed(1);
};

export function InsightCard({ optimizerState }: Props) {
  if (!optimizerState) return null;

  const { kpis } = optimizerState;
  const peakReserve = Math.max(0, 60 - kpis.peak_kw);
  const onTimeGap = Math.max(0, 100 - kpis.on_time_pct);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 space-y-4"
    >
      <div className="flex items-center gap-3">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-2 text-accent">
          <BadgeCheck className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Operational insights</h3>
          <p className="text-sm text-muted">Quick indicators from the latest schedule.</p>
        </div>
      </div>

      <div className="space-y-3 text-sm text-white/80">
        <div className="flex items-center gap-3">
          <PiggyBank className="w-4 h-4 text-accent" />
          <span>Total cost: ${kpis.total_cost.toFixed(2)}</span>
        </div>
        <div className="flex items-center gap-3">
          <Flame className="w-4 h-4 text-accentSecondary" />
          <span>Peak load: {kpis.peak_kw.toFixed(1)} kW (reserve {formatDelta(peakReserve)} kW vs 60 kW cap)</span>
        </div>
        <div className="flex items-center gap-3">
          <BadgeCheck className="w-4 h-4 text-white/80" />
          <span>On-time compliance: {kpis.on_time_pct.toFixed(1)}% ({formatDelta(onTimeGap)}% slack)</span>
        </div>
      </div>
    </motion.div>
  );
}
