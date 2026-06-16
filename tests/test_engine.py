"""Testes do motor do rodízio.

Estes testes são o seu seguro: provam que a lógica funciona sem precisar
abrir o navegador. Numa entrevista, mostrar testes te coloca num outro nível
de candidato a estágio.

Rode com:  pytest
"""

from datetime import date, datetime

from app.calendar_provider import FakeCalendarProvider, FakeEvent, FakeVacation
from app.engine import RoundRobinEngine
from app.models import Closer


# horário-base pras calls dos testes: 17/06/2026 às 14h
BASE = datetime(2026, 6, 17, 14, 0)


def make_closers():
    return [Closer(1, "Ana"), Closer(2, "Bruno"), Closer(3, "Carla")]


def test_todos_livres_escolhe_o_primeiro_e_gira():
    engine = RoundRobinEngine(make_closers(), FakeCalendarProvider())

    r1 = engine.assign(BASE, 30)
    assert r1.chosen.name == "Ana"        # primeiro da fila
    assert r1.skipped == []

    r2 = engine.assign(BASE, 30)
    assert r2.chosen.name == "Bruno"      # a vez girou
    assert engine.queue_order == ["Carla", "Ana", "Bruno"]


def test_ocupado_e_pulado_com_motivo():
    eventos = [
        FakeEvent(
            closer_id=1,
            title="Reunião de Pipeline",
            start=datetime(2026, 6, 17, 13, 30),
            end=datetime(2026, 6, 17, 15, 0),
        )
    ]
    engine = RoundRobinEngine(make_closers(), FakeCalendarProvider(events=eventos))

    r = engine.assign(BASE, 30)

    # Ana estava ocupada -> pulada; Bruno pega o lead
    assert r.chosen.name == "Bruno"
    assert len(r.skipped) == 1
    assert r.skipped[0].closer.name == "Ana"
    assert r.skipped[0].availability.conflicting_event == "Reunião de Pipeline"
    assert "Ocupado" in r.skipped[0].availability.reason


def test_ferias_e_pulado_com_motivo():
    ferias = [FakeVacation(closer_id=1, start=date(2026, 6, 15), end=date(2026, 6, 20))]
    engine = RoundRobinEngine(make_closers(), FakeCalendarProvider(vacations=ferias))

    r = engine.assign(BASE, 45)

    assert r.chosen.name == "Bruno"
    assert r.skipped[0].availability.on_vacation is True
    assert r.skipped[0].availability.vacation_until == date(2026, 6, 20)
    assert "férias" in r.skipped[0].availability.reason


def test_ninguem_livre_retorna_sem_escolhido():
    eventos = [
        FakeEvent(c, "Ocupadíssimo",
                  datetime(2026, 6, 17, 13, 0),
                  datetime(2026, 6, 17, 16, 0))
        for c in (1, 2, 3)
    ]
    engine = RoundRobinEngine(make_closers(), FakeCalendarProvider(events=eventos))

    r = engine.assign(BASE, 60)

    assert r.assigned is False
    assert r.chosen is None
    assert len(r.skipped) == 3   # todos foram avaliados


def test_desligar_closer_tira_do_rodizio():
    engine = RoundRobinEngine(make_closers(), FakeCalendarProvider())

    engine.set_active(2, False)   # desliga o Bruno (o pop-up)
    assert engine.queue_order == ["Ana", "Carla"]

    assert engine.assign(BASE, 30).chosen.name == "Ana"
    assert engine.assign(BASE, 30).chosen.name == "Carla"
    assert engine.assign(BASE, 30).chosen.name == "Ana"  # nunca cai no Bruno


def test_religar_closer_volta_pro_fim_da_fila():
    engine = RoundRobinEngine(make_closers(), FakeCalendarProvider())

    engine.set_active(2, False)
    engine.set_active(2, True)
    assert engine.queue_order == ["Ana", "Carla", "Bruno"]
