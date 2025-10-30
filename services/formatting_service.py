from typing import Dict, List


class FormattingService:
    def format_schedule_preview(self, schedule: Dict, max_vehicles: int = 5, max_hours: int = 12) -> List[str]:
        per_vehicle: Dict[str, Dict[int, float]] = schedule.get("per_vehicle", {})
        if not per_vehicle:
            return []
        lines: List[str] = []
        for i, (v_id, alloc) in enumerate(per_vehicle.items()):
            if i >= max_vehicles:
                break
            # Build compact hour:kw entries for first max_hours hours where kw>0
            entries: List[str] = []
            for h in range(max_hours):
                kw = alloc.get(h, 0.0)
                if kw > 0:
                    entries.append(f"h{h}:{kw:.0f}kW")
            if entries:
                lines.append(f"- {v_id}: " + ", ".join(entries))
        return lines

    def format_help(self) -> str:
        lines = [
            "EV Fleet Charge Optimizer",
            "Commands:",
            "- optimize 24h",
            "- optimize 12h peak",
            "- optimize 48h cost",
            "- set backend milp | greedy",
            "- status",
            "- preview (or 'preview 10 vehicles 24h')",
            "- explain (or 'explain v5')",
            "- compare cost vs peak",
            "- set default objective peak | cost",
            "- set default horizon 24h",
            "- set site peak D1 40kW",
            "- blackout D2 18-22h",
            "- clear blackouts [D1]",
            "- clear peak [D1]",
            "You can also say: 'optimize for 24h with peak flattening'",
        ]
        return "\n".join(lines)

    def format_summary(
        self,
        kpis: Dict[str, float],
        horizon: int,
        objective: str,
        top_explanations: List[str],
        preview_lines: List[str],
    ) -> str:
        lines: List[str] = []
        lines.append("EV Fleet Charge Optimization")
        lines.append(f"Horizon: {horizon}h")
        lines.append(f"Objective: {objective}")
        lines.append(f"Total cost: ${kpis['total_cost']:.2f}")
        lines.append(f"Peak power: {kpis['peak_kw']:.1f} kW")
        lines.append(f"On-time compliance: {kpis['on_time_pct']:.1f}%")
        if top_explanations:
            lines.append("Top decisions:")
            for e in top_explanations[:5]:
                lines.append(f"- {e}")
        if preview_lines:
            lines.append("Schedule preview:")
            lines.extend(preview_lines)
        return "\n".join(lines)

    def format_vehicle_detail(self, schedule: Dict, vehicle_id: str, max_hours: int = 24) -> str:
        per_vehicle: Dict[str, Dict[int, float]] = schedule.get("per_vehicle", {})
        alloc = per_vehicle.get(vehicle_id)
        if not alloc:
            return f"No entries for {vehicle_id}"
        entries: List[str] = []
        for h in range(max_hours):
            kw = alloc.get(h, 0.0)
            if kw > 0:
                entries.append(f"h{h}:{kw:.0f}kW")
        body = ", ".join(entries) if entries else "(no power assigned)"
        return f"{vehicle_id}: {body}"

    def format_compare(self, cost_kpis: Dict[str, float], peak_kpis: Dict[str, float]) -> str:
        lines = [
            "Comparison: cost vs peak",
            f"- Cost objective: ${cost_kpis['total_cost']:.2f}, peak {cost_kpis['peak_kw']:.1f}kW, on-time {cost_kpis['on_time_pct']:.1f}%",
            f"- Peak objective: ${peak_kpis['total_cost']:.2f}, peak {peak_kpis['peak_kw']:.1f}kW, on-time {peak_kpis['on_time_pct']:.1f}%",
            f"Δ Cost: ${(peak_kpis['total_cost']-cost_kpis['total_cost']):+.2f}",
            f"Δ Peak: {(peak_kpis['peak_kw']-cost_kpis['peak_kw']):+.1f}kW",
        ]
        return "\n".join(lines)
