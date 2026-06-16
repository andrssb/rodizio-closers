"""API web do Rodízio de Closers (FastAPI).

Ela é uma casca fininha por cima do motor (engine.py): recebe requisições
HTTP, chama o motor e devolve JSON. Também serve o frontend (a roleta).

Rodar:  uvicorn app.main:app --reload
Depois abra:  http://127.0.0.1:8000
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .calendar_provider import FakeCalendarProvider, FakeEvent, FakeVacation
from .engine import RoundRobinEngine
from .models import DURACOES_PERMITIDAS, Closer

# ---------------------------------------------------------------------------
# Estado em memória: 12 closers fictícios + agendas de exemplo.
# (quando plugarmos banco/Google, isso sai daqui)
# ---------------------------------------------------------------------------
NOMES = [
    "Ana", "Bruno", "Carla", "Diego", "Elaine", "Felipe",
    "Gabriela", "Heitor", "Isabela", "João", "Karla", "Lucas",
]
CLOSERS = [Closer(i + 1, nome) for i, nome in enumerate(NOMES)]

DEMO_TIME = datetime(2026, 6, 17, 14, 0)  # horário padrão da demo

EVENTOS = [
    FakeEvent(1, "Reunião de Pipeline", datetime(2026, 6, 17, 13, 30), datetime(2026, 6, 17, 15, 0)),
    FakeEvent(2, "Almoço com cliente", datetime(2026, 6, 17, 12, 0), datetime(2026, 6, 17, 14, 30)),
    FakeEvent(4, "Demo de produto", datetime(2026, 6, 17, 14, 0), datetime(2026, 6, 17, 14, 45)),
    FakeEvent(5, "1:1 com gestor", datetime(2026, 6, 17, 14, 15), datetime(2026, 6, 17, 15, 0)),
]
FERIAS = [
    FakeVacation(3, date(2026, 6, 15), date(2026, 6, 20)),  # Carla
]

engine = RoundRobinEngine(CLOSERS, FakeCalendarProvider(events=EVENTOS, vacations=FERIAS))

# ---------------------------------------------------------------------------
# App + arquivos estáticos (o frontend)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Rodízio de Closers")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


# ---------------------------------------------------------------------------
# Endpoints da API
# ---------------------------------------------------------------------------
@app.get("/api/closers")
def list_closers():
    """Lista os 12 closers na ordem fixa (pra desenhar a roleta)."""
    return [
        {"id": c.id, "name": c.name, "active": c.active, "index": i}
        for i, c in enumerate(CLOSERS)
    ]


class AssignRequest(BaseModel):
    duration_minutes: int
    when: datetime | None = None


@app.post("/api/assign")
def assign(req: AssignRequest):
    """Gira o rodízio e devolve quem pegou o lead + quem foi pulado e por quê."""
    if req.duration_minutes not in DURACOES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail=f"Duração inválida. Use uma de: {DURACOES_PERMITIDAS}",
        )

    when = req.when or DEMO_TIME
    result = engine.assign(when, req.duration_minutes)

    chosen = None
    if result.chosen:
        idx = next(i for i, c in enumerate(CLOSERS) if c.id == result.chosen.id)
        chosen = {"id": result.chosen.id, "name": result.chosen.name, "index": idx}

    return {
        "chosen": chosen,
        "skipped": [
            {
                "name": s.closer.name,
                "reason": s.availability.reason,
                "on_vacation": s.availability.on_vacation,
                "conflicting_event": s.availability.conflicting_event,
            }
            for s in result.skipped
        ],
        "queue": engine.queue_order,
    }


@app.post("/api/closers/{closer_id}/toggle")
def toggle_closer(closer_id: int):
    """Liga/desliga um closer no fluxo (o pop-up da tela)."""
    closer = next((c for c in CLOSERS if c.id == closer_id), None)
    if closer is None:
        raise HTTPException(status_code=404, detail="Closer não encontrado")

    engine.set_active(closer_id, not closer.active)
    return {"id": closer.id, "name": closer.name, "active": closer.active}
