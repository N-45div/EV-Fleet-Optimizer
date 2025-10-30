import { motion } from "framer-motion";
import { Loader2, Wifi, Shield, BrainCircuit } from "lucide-react";
import type { StatusResponse } from "../App";

interface Props {
  status: StatusResponse | null;
  loading: boolean;
  error: string | null;
}

export function StatusPanel({ status, loading, error }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-sm rounded-3xl border border-white/10 bg-white/[0.04] p-5 backdrop-blur-md"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-muted">
          <Wifi className={`w-4 h-4 ${status ? "text-accentSecondary" : "text-muted"}`} />
          <span>Agent Status</span>
        </div>
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin text-white/70" />
        ) : (
          <span className="text-xs text-white/60">{status ? "Live" : "Pending"}</span>
        )}
      </div>

      <div className="mt-4 space-y-3 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-muted">Default Horizon</span>
          <span className="font-medium">
            {status ? `${status.horizon_default}h` : "—"}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted">Default Objective</span>
          <span className="font-medium capitalize">
            {status ? status.objective_default : "—"}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted">Backend</span>
          <span className="font-medium uppercase">
            {status ? status.backend : "—"}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted">MeTTa Adapter</span>
          <span className="flex items-center gap-1 font-medium">
            <BrainCircuit className="w-4 h-4 text-accentSecondary" />
            {status ? status.metta : "—"}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted">Mailbox Privacy</span>
          <span className="flex items-center gap-1 font-medium">
            <Shield className="w-4 h-4 text-accent" />
            {status ? (status.private_mode ? "Private" : "Verbose") : "—"}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted">Last Run</span>
          <span className="font-medium">
            {status?.has_last_run ? "Available" : "Not yet"}
          </span>
        </div>
      </div>

      {error && (
        <p className="mt-4 text-xs text-red-300/80">
          {error}
        </p>
      )}
    </motion.div>
  );
}
