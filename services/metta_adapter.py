import os
from typing import Optional, Dict, List


class MeTTaAdapter:
    """Optional MeTTa (Hyperon) integration with graceful fallback."""

    def __init__(self, metta_path: Optional[str] = None):
        self.enabled = False
        self.reason = ""
        self.metta_path = metta_path
        self.metta = None
        try:
            import hyperon  # noqa: F401
            from hyperon import MeTTa  # type: ignore
            self.metta = MeTTa()
            self.enabled = True
        except Exception as e:
            self.enabled = False
            self.reason = f"hyperon not available: {e}"

    def info(self) -> str:
        if self.enabled:
            return "MeTTa adapter enabled"
        return f"MeTTa adapter disabled ({self.reason or 'not enabled'})"

    def load_facts(self, site_limits_df, chargers_df) -> None:
        if not self.enabled or self.metta is None:
            return
        prog_lines: List[str] = []
        # Facts: (site-peak D1 60)
        for _, row in site_limits_df.iterrows():
            depot = str(row["depot_id"]) if "depot_id" in row else str(row[0])
            kw = float(row["site_peak_kw"]) if "site_peak_kw" in row else float(row[1])
            prog_lines.append(f"(site-peak {depot} {int(kw)})")
        # Facts: (charger c1 D1 CCS 50)
        for _, row in chargers_df.iterrows():
            cid = str(row["id"]) if "id" in row else str(row[0])
            depot = str(row["depot_id"]) if "depot_id" in row else str(row[1])
            conn = str(row.get("connector", "CCS")).upper()
            kw = float(row.get("max_kw", 22))
            prog_lines.append(f"(charger {cid} {depot} {conn} {int(kw)})")
        # Simple compatibility rule: same connector name
        prog_lines.append("(= (compat $t $t) True)")
        program = "\n".join(prog_lines)
        try:
            self.metta.run(program)
        except Exception as e:
            self.enabled = False
            self.reason = f"load_facts error: {e}"

    def query_site_peak(self, depot_id: str) -> Optional[float]:
        if not self.enabled or self.metta is None:
            return None
        q = f"(site-peak {depot_id} $x)"
        try:
            res = self.metta.run(q)
            # Expect something like list of bindings; parse numbers from string repr
            text = str(res)
            import re
            m = re.search(r"(\d+\.?\d*)", text)
            return float(m.group(1)) if m else None
        except Exception:
            return None

    def query_chargers(self, depot_id: str) -> List[Dict]:
        if not self.enabled or self.metta is None:
            return []
        q = f"(charger $id {depot_id} $type $kw)"
        try:
            res = self.metta.run(q)
            text = str(res)
            # Very naive parse: find tuples like (charger id depot type kw)
            items: List[Dict] = []
            import re
            for m in re.finditer(r"charger ([^\s]+) .*? ([A-Z0-9]+) (\d+)", text):
                items.append({"id": m.group(1), "connector": m.group(2), "max_kw": float(m.group(3))})
            return items
        except Exception:
            return []
