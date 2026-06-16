"""Fonte de agenda dos closers.

Esta é a parte mais importante de arquitetura do projeto. Em vez de o motor
do rodízio falar DIRETO com o Google Calendar, ele fala com um "contrato"
(a classe CalendarProvider). Quem implementa esse contrato pode ser:

  - FakeCalendarProvider  -> agenda na memória, pra rodar/demonstrar offline
  - GoogleCalendarProvider -> a agenda real (a gente pluga depois)

Isso se chama "inversão de dependência". Vantagem prática: o app sempre roda,
mesmo sem internet/OAuth, e trocar a fonte não exige mexer no motor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Protocol

from .models import Availability, Closer


class CalendarProvider(Protocol):
    """O contrato. Qualquer fonte de agenda precisa saber responder isto."""

    def check_availability(
        self, closer: Closer, start: datetime, duration_minutes: int
    ) -> Availability:
        ...


# --------------------------------------------------------------------------
# Implementação FALSA (mock) — usada em testes e na demo offline.
# --------------------------------------------------------------------------


@dataclass
class FakeEvent:
    """Um compromisso na agenda de um closer."""

    closer_id: int
    title: str
    start: datetime
    end: datetime


@dataclass
class FakeVacation:
    """Período de férias de um closer (inclusivo nas duas pontas)."""

    closer_id: int
    start: date
    end: date


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Dois intervalos se sobrepõem? Regra clássica: cada um começa antes
    de o outro terminar."""
    return a_start < b_end and b_start < a_end


class FakeCalendarProvider:
    """Agenda guardada na memória. Perfeita pra testar a lógica do rodízio
    sem depender de nenhuma API externa."""

    def __init__(
        self,
        events: list[FakeEvent] | None = None,
        vacations: list[FakeVacation] | None = None,
    ) -> None:
        self.events = events or []
        self.vacations = vacations or []

    def check_availability(
        self, closer: Closer, start: datetime, duration_minutes: int
    ) -> Availability:
        # 1) Está de férias na data da call?
        for v in self.vacations:
            if v.closer_id == closer.id and v.start <= start.date() <= v.end:
                return Availability(
                    available=False,
                    reason=(
                        f"De férias ({v.start.strftime('%d/%m')} a "
                        f"{v.end.strftime('%d/%m/%Y')})"
                    ),
                    on_vacation=True,
                    vacation_until=v.end,
                )

        # 2) Tem algum evento batendo com o horário da call?
        end = start + timedelta(minutes=duration_minutes)
        for e in self.events:
            if e.closer_id == closer.id and _overlaps(start, end, e.start, e.end):
                return Availability(
                    available=False,
                    reason=(
                        f"Ocupado: {e.title} "
                        f"({e.start.strftime('%H:%M')}–{e.end.strftime('%H:%M')})"
                    ),
                    conflicting_event=e.title,
                )

        # 3) Livre!
        return Availability(available=True)
