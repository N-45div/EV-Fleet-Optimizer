import { motion } from "framer-motion";
import { ClipboardList, AlignRight, Info } from "lucide-react";
import type { OptimizerResponse } from "../App";

interface Props {
  optimizerState: OptimizerResponse | null;
  compareText: string;
}

export function SchedulePreview({ optimizerState, compareText }: Props) {
  if (!optimizerState) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-3xl border border-white/10 bg-white/[0.02] p-6 text-sm text-muted"
      >
        Run an optimization to preview schedules and explanations.
      </motion.div>
    );
  }

  const { preview, explanations, objective, backend, horizon } = optimizerState;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-white/10 bg-white/[0.03] p-6"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">Schedule Snapshot</h3>
          <p className="text-sm text-muted">
            Objective <span className="uppercase">{objective}</span> · Backend {backend.toUpperCase()} · Horizon {horizon}h
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-white/80">
            <ClipboardList className="w-4 h-4 text-accent" />
            Vehicle allocations (first few hours)
          </div>
          <div className="mt-3 space-y-2 text-sm text-muted">
            {preview.length > 0 ? preview.map((line) => <div key={line}>{line}</div>) : <div>No assignments yet.</div>}
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-white/80">
            <AlignRight className="w-4 h-4 text-accentSecondary" />
            Top decisions
          </div>
          <div className="mt-3 space-y-2 text-sm text-muted">
            {explanations.length > 0 ? explanations.map((line) => <div key={line}>{line}</div>) : <div>No explanations generated.</div>}
          </div>
        </div>
      </div>

      {compareText && (
        <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.02] p-4 text-sm text-muted">
          <div className="flex items-center gap-2 font-medium text-white/80">
            <Info className="w-4 h-4 text-accentSecondary" />
            Cost vs Peak summary
          </div>
          <pre className="mt-3 whitespace-pre-wrap text-xs leading-relaxed text-white/70">
            {compareText}
          </pre>
        </div>
      )}
    </motion.div>
  );
}
