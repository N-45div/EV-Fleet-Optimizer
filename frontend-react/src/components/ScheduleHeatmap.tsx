import { motion } from "framer-motion";
import { useMemo } from "react";
import type { OptimizerResponse } from "../App";

interface Props {
  optimizerState: OptimizerResponse | null;
}

export function ScheduleHeatmap({ optimizerState }: Props) {
  const heatmap = useMemo(() => {
    if (!optimizerState) return null;
    const vehicles = Object.keys(optimizerState.per_vehicle ?? {});
    if (vehicles.length === 0) return null;
    const hours = optimizerState.price_curve?.map((_, idx) => idx) ?? [];
    return {
      vehicles,
      hours,
      values: vehicles.map((vehicle) =>
        hours.map((hour) => optimizerState.per_vehicle?.[vehicle]?.[String(hour)] ?? 0)
      ),
    };
  }, [optimizerState]);

  if (!heatmap || heatmap.hours.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-white/10 bg-white/[0.03] p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">Vehicle charging density</h3>
          <p className="text-sm text-muted">Heatmap of kW per vehicle per hour</p>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-1 text-xs">
          <thead>
            <tr>
              <th className="text-left text-muted font-medium">Vehicle</th>
              {heatmap.hours.map((hour) => (
                <th key={hour} className="px-2 text-muted font-medium">
                  h{hour}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {heatmap.vehicles.map((vehicle, rowIdx) => (
              <tr key={vehicle}>
                <td className="px-2 py-1 text-white/80 font-medium">{vehicle}</td>
                {heatmap.hours.map((hour, colIdx) => {
                  const kw = heatmap.values[rowIdx][colIdx];
                  const intensity = Math.min(1, kw / 40);
                  const background = `rgba(95,67,241,${intensity * 0.6})`;
                  return (
                    <td
                      key={hour}
                      className="px-1 py-1 text-center text-[10px] text-white/90 rounded"
                      style={{ background }}
                    >
                      {kw > 0 ? `${kw.toFixed(0)}` : ""}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}
