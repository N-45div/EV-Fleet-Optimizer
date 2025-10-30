import { motion } from "framer-motion";
import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface Props {
  compareText: string;
}

const parseCompareText = (text: string) => {
  if (!text) return null;
  const lines = text.split("\n");
  if (lines.length < 3) return null;

  const costLine = lines.find((l) => l.includes("Cost objective"));
  const peakLine = lines.find((l) => l.includes("Peak objective"));
  if (!costLine || !peakLine) return null;

  const extract = (line: string) => {
    const costMatch = line.match(/\$(\d+\.\d+)/);
    const peakMatch = line.match(/peak (\d+\.\d+)kW/);
    const onTimeMatch = line.match(/on-time (\d+\.\d+)%/);
    return {
      cost: costMatch ? Number(costMatch[1]) : 0,
      peak: peakMatch ? Number(peakMatch[1]) : 0,
      onTime: onTimeMatch ? Number(onTimeMatch[1]) : 0,
    };
  };

  return {
    cost: extract(costLine),
    peak: extract(peakLine),
  };
};

export function KPIComparisonChart({ compareText }: Props) {
  const dataset = useMemo(() => {
    const parsed = parseCompareText(compareText);
    if (!parsed) return null;
    return [
      {
        strategy: "Cost",
        cost: parsed.cost.cost,
        peak: parsed.cost.peak,
        onTime: parsed.cost.onTime,
      },
      {
        strategy: "Peak",
        cost: parsed.peak.cost,
        peak: parsed.peak.peak,
        onTime: parsed.peak.onTime,
      },
    ];
  }, [compareText]);

  if (!dataset) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-white/10 bg-white/[0.03] p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">Cost vs Peak Strategy</h3>
          <p className="text-sm text-muted">Compare KPI trade-offs</p>
        </div>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={dataset} barSize={28}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.18)" />
            <XAxis dataKey="strategy" stroke="rgba(148,163,184,0.7)" tickLine={false} axisLine={false} />
            <YAxis stroke="rgba(148,163,184,0.7)" tickLine={false} axisLine={false} />
            <Tooltip
              cursor={{ fill: "rgba(95,67,241,0.08)" }}
              contentStyle={{ background: "#0f172a", borderRadius: 12, border: "1px solid rgba(148,163,184,0.2)", color: "white" }}
            />
            <Bar dataKey="cost" stackId="a" fill="#5f43f1" name="Total Cost" />
            <Bar dataKey="peak" stackId="a" fill="#3d8bd3" name="Peak kW" />
            <Bar dataKey="onTime" stackId="a" fill="#fbbf24" name="On-Time %" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
