import os
import sys
import re
from datetime import datetime
from typing import Dict, List
from uuid import uuid4
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol, Model
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

# Ensure project root is importable when running this file directly (before local imports)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.telemetry_service import TelemetryService
from services.price_service import PriceService
from services.kg_service import KGService
from services.optimizer_service import OptimizerService
from services.evaluation_service import EvaluationService
from services.formatting_service import FormattingService
from services.optimizer_milp import OptimizerMILP
from services.metta_adapter import MeTTaAdapter

load_dotenv()

AGENT_NAME = os.getenv("ORCHESTRATOR_AGENT_NAME", "EV-Optimizer-Orchestrator")
SEED_PHRASE = os.getenv("ORCHESTRATOR_SEED_PHRASE", "ev-optimizer-seed")
HORIZON_HOURS = int(os.getenv("HORIZON_HOURS", "24"))
README_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
AVATAR_URL = os.getenv("AVATAR_URL", None)
AGENT_PORT = int(os.getenv("AGENT_PORT", "8000"))
PUBLIC_ENDPOINT = os.getenv("PUBLIC_ENDPOINT", None)
OBJECTIVE_DEFAULT = os.getenv("OBJECTIVE_DEFAULT", "cost").lower()
USE_MAILBOX = os.getenv("USE_MAILBOX", "false").lower() in ("1", "true", "yes")
USE_METTA = os.getenv("USE_METTA", "false").lower() in ("1", "true", "yes")
BACKEND_DEFAULT = os.getenv("BACKEND", "greedy").lower()
PRIVATE_MODE = os.getenv("PRIVATE_MODE", "false").lower() in ("1", "true", "yes")

# Metadata to help Agentverse discovery/classification (non-sensitive)
AGENT_METADATA = {
    "category": "innovationlab",
    "project": "ev-fleet-optimizer",
    "tech": ["uagents", "asi-one", "metta-kg"],
}
agent = Agent(
    name=AGENT_NAME,
    seed=SEED_PHRASE,
    port=AGENT_PORT,
    endpoint=PUBLIC_ENDPOINT if PUBLIC_ENDPOINT else None,
    mailbox=USE_MAILBOX,
    publish_agent_details=True,
    readme_path=README_PATH if os.path.exists(README_PATH) else None,
    avatar_url=AVATAR_URL,
    metadata=AGENT_METADATA,
)
chat_proto = Protocol(spec=chat_protocol_spec)


def create_text_chat(text: str) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=content)


telemetry = TelemetryService()
prices = PriceService()
metta = MeTTaAdapter(metta_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), "kg", "metta_rules.metta"))
kg = KGService(metta=metta)
optimizer = OptimizerService(kg=kg, telemetry=telemetry, prices=prices)
eval_service = EvaluationService()
formatter = FormattingService()
milp_optimizer = OptimizerMILP(kg=kg, telemetry=telemetry, prices=prices)


# simple conversational state
last_schedule = None
last_kpis = None
last_horizon = None
last_objective = None

# runtime defaults (mutable without restarting)
current_default_horizon = HORIZON_HOURS
current_default_objective = OBJECTIVE_DEFAULT if OBJECTIVE_DEFAULT in ("cost", "peak") else "cost"
current_backend = BACKEND_DEFAULT if BACKEND_DEFAULT in ("greedy", "milp") else "greedy"


def parse_intent(text: str) -> dict:
    t = (text or "").lower().strip()
    if not t or t in {"hi", "hello", "hey"}:
        return {"type": "greet"}
    if "help" in t or "commands" in t:
        return {"type": "help"}
    if "status" in t:
        return {"type": "status"}
    if "preview" in t:
        mv = 5
        mh = 12
        m = re.search(r"(\d+)\s*vehicles", t)
        if m:
            mv = int(m.group(1))
        m = re.search(r"(\d+)\s*h", t)
        if m:
            mh = int(m.group(1))
        return {"type": "preview", "max_vehicles": mv, "max_hours": mh}
    if "explain" in t or "why" in t:
        m = re.search(r"explain\s+(v\w+)", t)
        return {"type": "explain", "vehicle": m.group(1) if m else None}
    if "compare" in t and "cost" in t and "peak" in t:
        # e.g. "compare cost vs peak"
        m = re.search(r"(\d+)\s*h", t)
        hz = int(m.group(1)) if m else None
        return {"type": "compare", "horizon": hz}
    if t.startswith("set default objective"):
        obj = "peak" if "peak" in t else ("cost" if "cost" in t else None)
        return {"type": "set_default_objective", "objective": obj}
    if t.startswith("set default horizon"):
        m = re.search(r"(\d+)\s*h", t)
        hz = int(m.group(1)) if m else None
        return {"type": "set_default_horizon", "horizon": hz}
    if t.startswith("set backend"):
        m = re.search(r"set backend\s+(greedy|milp)", t)
        return {"type": "set_backend", "backend": m.group(1) if m else None}
    m = re.search(r"set\s+(?:site\s*)?peak\s+(?:for\s*)?(d\d+)\s*(\d+)\s*k?w", t)
    if m:
        return {"type": "set_site_peak", "depot": m.group(1).upper(), "kw": int(m.group(2))}
    m = re.search(r"blackout\s+(d\d+)\s*(\d+)\s*[-to]+\s*(\d+)\s*h?", t)
    if m:
        return {"type": "add_blackout", "depot": m.group(1).upper(), "start": int(m.group(2)), "end": int(m.group(3))}
    m = re.search(r"clear\s+blackouts(?:\s+(d\d+))?", t)
    if m:
        return {"type": "clear_blackouts", "depot": (m.group(1).upper() if m.group(1) else None)}
    m = re.search(r"clear\s+peak(?:\s+(d\d+))?", t)
    if m:
        return {"type": "clear_peak", "depot": (m.group(1).upper() if m.group(1) else None)}

    if "optimize" in t or "optimise" in t:
        horizon = None
        m = re.search(r"(\d+)\s*h", t)
        if m:
            horizon = int(m.group(1))
        else:
            if "48" in t:
                horizon = 48
            elif "12" in t:
                horizon = 12
            elif "day" in t:
                horizon = 24
        objective = None
        if "peak" in t or "flatten" in t:
            objective = "peak"
        elif "cost" in t:
            objective = "cost"
        return {"type": "optimize", "horizon": horizon, "objective": objective}

    return {"type": "help"}


@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))

    horizon = current_default_horizon
    request_texts = []
    objective = current_default_objective
    saw_start = False

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            saw_start = True
            continue
        elif isinstance(item, TextContent):
            request_texts.append(item.text.lower())
        elif isinstance(item, EndSessionContent):
            continue

    request = " ".join(request_texts)

    if saw_start and not request.strip():
        await ctx.send(sender, create_text_chat("Hi! I'm the EV Fleet Charge Optimizer.\n" + formatter.format_help()))
        return
    intent = parse_intent(request)

    if intent["type"] in {"greet", "help"}:
        text = formatter.format_help()
        await ctx.send(sender, create_text_chat(text))
        return

    if intent["type"] == "compare":
        hz = intent.get("horizon") or current_default_horizon
        try:
            price_curve = prices.get_prices(hz)
            if current_backend == "milp":
                sched_cost = milp_optimizer.optimize(horizon_hours=hz, objective="cost")
                sched_peak = milp_optimizer.optimize(horizon_hours=hz, objective="peak")
            else:
                sched_cost = optimizer.optimize(horizon_hours=hz, request_text=request, objective="cost")
                sched_peak = optimizer.optimize(horizon_hours=hz, request_text=request, objective="peak")
            kpis_cost = eval_service.compute_kpis(schedule=sched_cost, price_curve=price_curve)
            kpis_peak = eval_service.compute_kpis(schedule=sched_peak, price_curve=price_curve)
        except Exception as e:
            await ctx.send(sender, create_text_chat(f"Error while comparing: {e}"))
            return
        text = formatter.format_compare(kpis_cost, kpis_peak)
        await ctx.send(sender, create_text_chat(text))
        return

    if intent["type"] == "status":
        status_lines = [
            "EV Fleet Charge Optimizer",
            f"Default horizon: {current_default_horizon}h",
            f"Default objective: {current_default_objective}",
            f"Backend: {current_backend}",
            (metta.info()),
            ("Private mode: on" if PRIVATE_MODE else "Private mode: off"),
        ]
        if last_schedule and last_kpis:
            status_lines.append("Last run available. Try 'preview' or 'explain'.")
        await ctx.send(sender, create_text_chat("\n".join(status_lines)))
        return

    if intent["type"] == "preview":
        if not last_schedule:
            await ctx.send(sender, create_text_chat("No schedule yet. Say 'optimize 24h' to create one."))
            return
        preview = formatter.format_schedule_preview(
            last_schedule,
            max_vehicles=int(intent.get("max_vehicles", 5)),
            max_hours=int(intent.get("max_hours", 12)),
        )
        text = "Schedule preview:\n" + ("\n".join(preview) if preview else "(empty)")
        await ctx.send(sender, create_text_chat(text))
        return

    if intent["type"] == "explain":
        if not last_schedule:
            await ctx.send(sender, create_text_chat("No schedule yet. Say 'optimize 24h' first."))
            return
        if intent.get("vehicle"):
            text = formatter.format_vehicle_detail(last_schedule, intent["vehicle"], max_hours=24)
        else:
            exps = last_schedule.get("explanations", [])
            text = "Top decisions:\n" + "\n".join(f"- {e}" for e in exps[:10])
        await ctx.send(sender, create_text_chat(text))
        return

    if intent["type"] == "set_default_objective":
        obj = intent.get("objective")
        if obj in ("cost", "peak"):
            globals()["current_default_objective"] = obj
            await ctx.send(sender, create_text_chat(f"Default objective set to {obj}"))
        else:
            await ctx.send(sender, create_text_chat("Please specify 'peak' or 'cost'."))
        return

    if intent["type"] == "set_default_horizon":
        hz = intent.get("horizon")
        if isinstance(hz, int) and hz > 0:
            globals()["current_default_horizon"] = hz
            await ctx.send(sender, create_text_chat(f"Default horizon set to {hz}h"))
        else:
            await ctx.send(sender, create_text_chat("Please provide horizon like 'set default horizon 24h'."))
        return

    if intent["type"] == "set_backend":
        be = intent.get("backend")
        if be in ("greedy", "milp"):
            globals()["current_backend"] = be
            await ctx.send(sender, create_text_chat(f"Backend set to {be}"))
        else:
            await ctx.send(sender, create_text_chat("Please choose backend 'greedy' or 'milp'."))
        return

    if intent["type"] == "set_site_peak":
        depot = intent.get("depot")
        kw = intent.get("kw")
        try:
            kg.set_site_peak_limit_kw(depot, kw)
        except Exception as e:
            await ctx.send(sender, create_text_chat(f"Failed to set peak: {e}"))
            return
        await ctx.send(sender, create_text_chat(f"Set site peak for {depot} to {kw}kW"))
        return

    if intent["type"] == "add_blackout":
        depot = intent.get("depot")
        start = intent.get("start")
        end = intent.get("end")
        try:
            kg.add_blackout(depot, int(start), int(end))
        except Exception as e:
            await ctx.send(sender, create_text_chat(f"Failed to add blackout: {e}"))
            return
        await ctx.send(sender, create_text_chat(f"Added blackout for {depot} {start}-{end}h"))
        return

    if intent["type"] == "clear_blackouts":
        kg.clear_blackouts(intent.get("depot"))
        await ctx.send(sender, create_text_chat("Cleared blackouts" + (f" for {intent.get('depot')}" if intent.get('depot') else "")))
        return

    if intent["type"] == "clear_peak":
        kg.clear_site_peak_override(intent.get("depot"))
        await ctx.send(sender, create_text_chat("Cleared site peak override" + (f" for {intent.get('depot')}" if intent.get('depot') else "")))
        return

    if intent["type"] == "optimize":
        if intent.get("horizon"):
            horizon = int(intent["horizon"])
        if intent.get("objective") in ("cost", "peak"):
            objective = intent["objective"]

        try:
            price_curve = prices.get_prices(horizon)
            if current_backend == "milp":
                schedule = milp_optimizer.optimize(horizon_hours=horizon, objective=objective)
            else:
                schedule = optimizer.optimize(horizon_hours=horizon, request_text=request, objective=objective)
            kpis = eval_service.compute_kpis(schedule=schedule, price_curve=price_curve)
        except Exception as e:
            await ctx.send(sender, create_text_chat(f"Error while optimizing: {e}"))
            return

        preview_lines = formatter.format_schedule_preview(schedule, max_vehicles=5, max_hours=12)
        text = formatter.format_summary(kpis, horizon, objective, schedule.get("explanations", []), preview_lines)

        last_run = {
            "schedule": schedule,
            "kpis": kpis,
            "horizon": horizon,
            "objective": objective,
        }
        globals()["last_schedule"] = last_run["schedule"]
        globals()["last_kpis"] = last_run["kpis"]
        globals()["last_horizon"] = last_run["horizon"]
        globals()["last_objective"] = last_run["objective"]

        await ctx.send(sender, create_text_chat(text))
        return

    await ctx.send(sender, create_text_chat(formatter.format_help()))


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(chat_proto, publish_manifest=True)

# ===== REST API for Frontend Integration =====

class KPI(Model):
    total_cost: float
    peak_kw: float
    on_time_pct: float


class OptimizeRequest(Model):
    horizon: int | None = None
    objective: str | None = None
    backend: str | None = None


class OptimizeResponse(Model):
    horizon: int
    objective: str
    backend: str
    kpis: KPI
    preview: list[str]
    explanations: list[str]
    per_depot: Dict[str, Dict[str, float]]
    per_vehicle: Dict[str, Dict[str, float]]
    price_curve: List[float]
    remaining_kwh: Dict[str, float]
    message: str | None = None


class CompareRequest(Model):
    horizon: int | None = None


class CompareResponse(Model):
    text: str


class StatusResponse(Model):
    horizon_default: int
    objective_default: str
    backend: str
    metta: str
    private_mode: bool
    has_last_run: bool


class SitePeakRequest(Model):
    depot: str
    kw: int


class BlackoutRequest(Model):
    depot: str
    start: int
    end: int


class MessageResponse(Model):
    message: str


@agent.on_rest_post("/optimize", OptimizeRequest, OptimizeResponse)
async def api_optimize(ctx: Context, req: OptimizeRequest) -> OptimizeResponse:
    hz = req.horizon or current_default_horizon
    obj = req.objective or current_default_objective
    be = req.backend or current_backend
    try:
        price_curve = prices.get_prices(hz)
        if be == "milp":
            schedule = milp_optimizer.optimize(horizon_hours=hz, objective=obj)
        else:
            schedule = optimizer.optimize(horizon_hours=hz, request_text=f"api optimize {hz}h {obj}", objective=obj)
        kpis = eval_service.compute_kpis(schedule=schedule, price_curve=price_curve)
    except Exception as e:
        return OptimizeResponse(horizon=hz, objective=obj, backend=be, kpis=KPI(total_cost=0.0, peak_kw=0.0, on_time_pct=0.0), preview=[], explanations=[], message=f"error: {e}", per_depot={}, per_vehicle={}, price_curve=[], remaining_kwh={})

    preview_lines = formatter.format_schedule_preview(schedule, max_vehicles=5, max_hours=12)
    # store last run
    globals()["last_schedule"] = schedule
    globals()["last_kpis"] = kpis
    globals()["last_horizon"] = hz
    globals()["last_objective"] = obj

    def normalize_keys(input_dict: Dict[str, Dict[int, float]]) -> Dict[str, Dict[str, float]]:
        normalized: Dict[str, Dict[str, float]] = {}
        for outer_key, inner in input_dict.items():
            normalized[outer_key] = {str(hour): float(val) for hour, val in inner.items()}
        return normalized

    return OptimizeResponse(
        horizon=hz,
        objective=obj,
        backend=be,
        kpis=KPI(total_cost=kpis["total_cost"], peak_kw=kpis["peak_kw"], on_time_pct=kpis["on_time_pct"]),
        preview=preview_lines,
        explanations=schedule.get("explanations", [])[:10],
        per_depot=normalize_keys(schedule.get("per_depot", {})),
        per_vehicle=normalize_keys(schedule.get("per_vehicle", {})),
        price_curve=[float(x) for x in price_curve],
        remaining_kwh={str(k): float(v) for k, v in schedule.get("remaining_kwh", {}).items()},
        message=None,
    )


@agent.on_rest_post("/compare", CompareRequest, CompareResponse)
async def api_compare(ctx: Context, req: CompareRequest) -> CompareResponse:
    hz = req.horizon or current_default_horizon
    try:
        price_curve = prices.get_prices(hz)
        if current_backend == "milp":
            sched_cost = milp_optimizer.optimize(horizon_hours=hz, objective="cost")
            sched_peak = milp_optimizer.optimize(horizon_hours=hz, objective="peak")
        else:
            sched_cost = optimizer.optimize(horizon_hours=hz, request_text="api compare", objective="cost")
            sched_peak = optimizer.optimize(horizon_hours=hz, request_text="api compare", objective="peak")
        kpis_cost = eval_service.compute_kpis(schedule=sched_cost, price_curve=price_curve)
        kpis_peak = eval_service.compute_kpis(schedule=sched_peak, price_curve=price_curve)
    except Exception as e:
        return CompareResponse(text=f"error: {e}")
    text = formatter.format_compare(kpis_cost, kpis_peak)
    return CompareResponse(text=text)


@agent.on_rest_get("/status", StatusResponse)
async def api_status(ctx: Context) -> StatusResponse:
    return StatusResponse(
        horizon_default=current_default_horizon,
        objective_default=current_default_objective,
        backend=current_backend,
        metta=metta.info(),
        private_mode=PRIVATE_MODE,
        has_last_run=bool(last_schedule and last_kpis),
    )


@agent.on_rest_post("/whatif/site_peak", SitePeakRequest, MessageResponse)
async def api_site_peak(ctx: Context, req: SitePeakRequest) -> MessageResponse:
    try:
        kg.set_site_peak_limit_kw(req.depot, int(req.kw))
        return MessageResponse(message=f"Set site peak for {req.depot} to {req.kw}kW")
    except Exception as e:
        return MessageResponse(message=f"error: {e}")


@agent.on_rest_post("/whatif/blackout", BlackoutRequest, MessageResponse)
async def api_blackout(ctx: Context, req: BlackoutRequest) -> MessageResponse:
    try:
        kg.add_blackout(req.depot, int(req.start), int(req.end))
        return MessageResponse(message=f"Added blackout for {req.depot} {req.start}-{req.end}h")
    except Exception as e:
        return MessageResponse(message=f"error: {e}")

if __name__ == "__main__":
    agent.run()
