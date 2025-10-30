import { motion } from "framer-motion";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { OptimizerResponse } from "../App";

interface Props {
  optimizerState: OptimizerResponse | null;
}

export function DepotLoadChart({ optimizerState }: Props) {
  if (!optimizerState || !optimizerState.per_depot || !optimizerState.price_curve) {
    return null;
  }

  const hours = optimizerState.price_curve.map((_, idx) => idx);
  const depots = Object.keys(optimizerState.per_depot ?? {});

  const data = hours.map((hour) => {
    const point: Record<string, number | string> = { hour: `h${hour}` };
    depots.forEach((depot) => {
      const depotHour = optimizerState.per_depot?.[depot]?.[String(hour)] ?? 0;
      point[depot] = depotHour;
    });
    return point;
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-white/10 bg-white/[0.03] p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">Depot Load Curve</h3>
          <p className="text-sm text-muted">Per-depot aggregate power by hour</p>
        </div>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.18)" />
            <XAxis dataKey="hour" stroke="rgba(148,163,184,0.7)" tickLine={false} axisLine={false} />
            <YAxis stroke="rgba(148,163,184,0.7)" tickLine={false} axisLine={false} tickFormatter={(v) => `${v} kW`} />
            <Tooltip
              cursor={{ stroke: "rgba(95,67,241,0.4)", strokeWidth: 2 }}
              contentStyle={{ background: "#0f172a", borderRadius: 12, border: "1px solid rgba(148,163,184,0.2)", color: "white" }}
            />
            {depots.map((depot, idx) => (
              <Line
                key={depot}
                type="monotone"
                dataKey={depot}
                stroke={idx % 2 === 0 ? "#5f43f1" : "#3d8bd3"}
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
