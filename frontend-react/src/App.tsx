import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  BatteryCharging,
  AlertTriangle,
  TrendingDown,
  Bolt,
  LineChart,
  Brain,
  Clock,
  Zap,
} from "lucide-react";
import { DepotLoadChart } from "./components/DepotLoadChart";
import { KPIComparisonChart } from "./components/KPIComparisonChart";
import { ScheduleHeatmap } from "./components/ScheduleHeatmap";
import { InsightCard } from "./components/InsightCard";
import { WhatIfPanel } from "./components/WhatIfPanel";
import { ScenarioForm } from "./components/ScenarioForm";
import { StatusPanel } from "./components/StatusPanel";
import { SchedulePreview } from "./components/SchedulePreview";

export type OptimizePayload = {
  horizon?: number;
  objective?: "cost" | "peak";
  backend?: "greedy" | "milp";
};

export type OptimizerResponse = {
  horizon: number;
  objective: string;
  backend: string;
  kpis: {
    total_cost: number;
    peak_kw: number;
    on_time_pct: number;
  };
  preview: string[];
  explanations: string[];
  per_depot: Record<string, Record<string, number>>;
  per_vehicle: Record<string, Record<string, number>>;
  price_curve: number[];
  remaining_kwh: Record<string, number>;
  message?: string | null;
};

export type StatusResponse = {
  horizon_default: number;
  objective_default: string;
  backend: string;
  metta: string;
  private_mode: boolean;
  has_last_run: boolean;
};

export type CompareResponse = {
  text: string;
};

export type WhatIfMessage = {
  message: string;
};

const formatCurrency = (value: number) => `$${value.toFixed(2)}`;

const heroVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

export function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [optimizerState, setOptimizerState] = useState<OptimizerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [compareText, setCompareText] = useState<string>("");
  const [whatIfMessage, setWhatIfMessage] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const loadStatus = async () => {
    try {
      const res = await axios.get<StatusResponse>("/api/status");
      setStatus(res.data);
    } catch (e: any) {
      setError(e?.message ?? "Failed to load status");
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const onOptimize = async (payload: OptimizePayload) => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post<OptimizerResponse>("/api/optimize", payload);
      if (res.data.message) {
        setError(res.data.message);
      }
      setOptimizerState(res.data);
      await loadStatus();
    } catch (e: any) {
      setError(e?.message ?? "Optimization failed");
    } finally {
      setLoading(false);
    }
  };

  const onCompare = async (horizon?: number) => {
    try {
      const res = await axios.post<CompareResponse>("/api/compare", { horizon });
      setCompareText(res.data.text);
    } catch (e: any) {
      setError(e?.message ?? "Compare failed");
    }
  };

  const onSetSitePeak = async (depot: string, kw: number) => {
    try {
      const res = await axios.post<WhatIfMessage>("/api/whatif/site_peak", { depot, kw });
      setWhatIfMessage(res.data.message);
      await loadStatus();
    } catch (e: any) {
      setError(e?.message ?? "Set site peak failed");
    }
  };

  const onAddBlackout = async (depot: string, start: number, end: number) => {
    try {
      const res = await axios.post<WhatIfMessage>("/api/whatif/blackout", { depot, start, end });
      setWhatIfMessage(res.data.message);
    } catch (e: any) {
      setError(e?.message ?? "Add blackout failed");
    }
  };

  const heroKPIs = useMemo(() => {
    const base = optimizerState?.kpis;
    if (!base) return [];
    return [
      {
        label: "Total Cost",
        value: formatCurrency(base.total_cost),
        icon: <TrendingDown className="w-5 h-5" />,
        description: "Energy cost over horizon",
      },
      {
        label: "Peak Load",
        value: `${base.peak_kw.toFixed(1)} kW`,
        icon: <Bolt className="w-5 h-5" />,
        description: "Max aggregate depot load",
      },
      {
        label: "On-Time",
        value: `${base.on_time_pct.toFixed(1)}%`,
        icon: <Clock className="w-5 h-5" />,
        description: "Vehicles ready before departure",
      },
    ];
  }, [optimizerState]);

  return (
    <div className="min-h-screen bg-background text-white">
      <div className="max-w-7xl mx-auto px-6 py-10">
        <motion.header
          initial="hidden"
          animate="visible"
          variants={heroVariants}
          className="rounded-3xl bg-gradient-to-br from-card via-card/70 to-card/40 border border-white/5 shadow-glow px-10 py-12 flex flex-col gap-6"
        >
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div className="flex-1 min-w-[260px]">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1 text-sm text-muted">
                <Brain className="w-4 h-4 text-accentSecondary" /> ASI Alliance · Fleet Optimization Agent
              </div>
              <h1 className="text-3xl md:text-4xl font-semibold leading-tight mt-4">
                Autonomous EV Fleet Charge Optimizer
              </h1>
              <p className="text-muted text-sm md:text-base mt-3 max-w-2xl">
                Plan charge sessions that hit cost and peak targets, even when depot limits change. Simulate what-ifs, compare strategies, and share explainable KPIs with operations.
              </p>
              <div className="mt-5 flex flex-wrap gap-3 text-sm">
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                  <Zap className="w-4 h-4 text-accentSecondary" /> uAgents + ASI:One Chat
                </div>
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                  <BatteryCharging className="w-4 h-4 text-accent" /> OR-Tools MILP core
                </div>
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                  <LineChart className="w-4 h-4 text-accent" /> What-if simulator
                </div>
              </div>
            </div>
            <StatusPanel status={status} loading={loading} error={error} />
          </div>
          {heroKPIs.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8">
              {heroKPIs.map((item) => (
                <motion.div
                  key={item.label}
                  whileHover={{ y: -4 }}
                  className="rounded-2xl border border-white/5 bg-white/[0.03] px-5 py-4 backdrop-blur-sm"
                >
                  <div className="flex items-center gap-3 text-sm text-muted">
                    <span className="p-2 rounded-xl bg-white/5 border border-white/10 text-accent">
                      {item.icon}
                    </span>
                    <span>{item.description}</span>
                  </div>
                  <h3 className="text-xl font-semibold mt-4">{item.value}</h3>
                  <p className="text-xs text-muted mt-1">{item.label}</p>
                </motion.div>
              ))}
            </div>
          )}
        </motion.header>

        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mt-10 grid grid-cols-1 lg:grid-cols-3 gap-6"
        >
          <div className="lg:col-span-2 space-y-6">
            <ScenarioForm
              status={status}
              loading={loading}
              onOptimize={onOptimize}
              onCompare={onCompare}
            />

            <div className="grid grid-cols-1 gap-6">
              <SchedulePreview
                optimizerState={optimizerState}
                compareText={compareText}
              />
              <DepotLoadChart optimizerState={optimizerState} />
              <KPIComparisonChart compareText={compareText} />
              <ScheduleHeatmap optimizerState={optimizerState} />
            </div>
          </div>
          <div className="space-y-6">
            <WhatIfPanel onSetSitePeak={onSetSitePeak} onAddBlackout={onAddBlackout} whatIfMessage={whatIfMessage} />
            <InsightCard optimizerState={optimizerState} />
          </div>
        </motion.section>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8 rounded-xl border border-red-500/40 bg-red-500/10 px-6 py-4 flex items-start gap-3 text-sm"
          >
            <AlertTriangle className="w-5 h-5 mt-0.5 text-red-300" />
            <p>{error}</p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
