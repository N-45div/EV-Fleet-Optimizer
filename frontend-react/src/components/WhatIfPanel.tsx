import { useState } from "react";
import { motion } from "framer-motion";
import { Castle, Lightbulb, PlusCircle } from "lucide-react";

interface Props {
  onSetSitePeak: (depot: string, kw: number) => Promise<void>;
  onAddBlackout: (depot: string, start: number, end: number) => Promise<void>;
  whatIfMessage: string;
}

export function WhatIfPanel({ onSetSitePeak, onAddBlackout, whatIfMessage }: Props) {
  const [peakDepot, setPeakDepot] = useState("D1");
  const [peakKw, setPeakKw] = useState("40");
  const [blackoutDepot, setBlackoutDepot] = useState("D2");
  const [blackoutStart, setBlackoutStart] = useState("18");
  const [blackoutEnd, setBlackoutEnd] = useState("22");
  const [submitting, setSubmitting] = useState(false);

  const submitPeak = async () => {
    const depot = peakDepot.trim() || "D1";
    const kw = Number(peakKw);
    if (Number.isNaN(kw) || kw <= 0) return;
    setSubmitting(true);
    await onSetSitePeak(depot, kw);
    setSubmitting(false);
  };

  const submitBlackout = async () => {
    const depot = blackoutDepot.trim() || "D2";
    const start = Number(blackoutStart);
    const end = Number(blackoutEnd);
    if (Number.isNaN(start) || Number.isNaN(end)) return;
    setSubmitting(true);
    await onAddBlackout(depot, start, end);
    setSubmitting(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 space-y-6"
    >
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-2xl bg-white/5 border border-white/10 text-accent">
          <Lightbulb className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">What-if overrides</h3>
          <p className="text-sm text-muted">Tune site limits or inject outage windows before re-running optimization.</p>
        </div>
      </div>

      <div className="space-y-3 text-sm">
        <div className="text-xs uppercase tracking-wide text-muted">Site Peak Override</div>
        <div className="flex flex-wrap gap-3">
          <input
            className="flex-1 min-w-[100px] rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white"
            value={peakDepot}
            onChange={(e) => setPeakDepot(e.target.value)}
            placeholder="Depot ID"
          />
          <input
            className="flex-1 min-w-[120px] rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white"
            value={peakKw}
            onChange={(e) => setPeakKw(e.target.value)}
            placeholder="kW"
            type="number"
          />
          <button
            onClick={submitPeak}
            disabled={submitting}
            className="inline-flex items-center gap-2 rounded-full bg-accent px-4 py-2 text-sm font-semibold hover:bg-accent/80 disabled:opacity-60"
          >
            <Castle className="w-4 h-4" />
            Apply
          </button>
        </div>
      </div>

      <div className="space-y-3 text-sm">
        <div className="text-xs uppercase tracking-wide text-muted">Blackout Window</div>
        <div className="flex flex-wrap gap-3">
          <input
            className="flex-1 min-w-[100px] rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white"
            value={blackoutDepot}
            onChange={(e) => setBlackoutDepot(e.target.value)}
            placeholder="Depot ID"
          />
          <input
            className="flex-1 min-w-[100px] rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white"
            value={blackoutStart}
            onChange={(e) => setBlackoutStart(e.target.value)}
            placeholder="Start hour"
            type="number"
          />
          <input
            className="flex-1 min-w-[100px] rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white"
            value={blackoutEnd}
            onChange={(e) => setBlackoutEnd(e.target.value)}
            placeholder="End hour"
            type="number"
          />
          <button
            onClick={submitBlackout}
            disabled={submitting}
            className="inline-flex items-center gap-2 rounded-full border border-white/15 px-4 py-2 text-sm font-semibold hover:border-accent/60"
          >
            <PlusCircle className="w-4 h-4" />
            Add
          </button>
        </div>
      </div>

      {whatIfMessage && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.05] px-4 py-3 text-xs text-white/80">
          {whatIfMessage}
        </div>
      )}
    </motion.div>
  );
}
