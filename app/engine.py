"""O motor do rodízio (a 'roleta' por baixo dos panos).

Conceito-chave pra entrevista: isto NÃO é aleatório, é um *round-robin* —
um rodízio justo. Cada closer tem a sua vez numa fila. Quando chega a vez
de alguém:

  - se ele está livre  -> recebe o lead e vai pro fim da fila;
  - se está ocupado    -> é pulado (guardamos o motivo) e vai pro fim da fila,
                          e a roleta gira de novo pro próximo.

Distribuição de lead precisa ser JUSTA, não sorte — por isso round-robin e
não random. (Isso é uma ótima frase pra dizer na entrevista.)
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime

from .calendar_provider import CalendarProvider
from .models import Availability, Closer


@dataclass
class SkippedCloser:
    """Um closer que foi pulado, com o motivo (pra mostrar na tela)."""

    closer: Closer
    availability: Availability


@dataclass
class AssignmentResult:
    """Resultado de uma rodada: quem pegou o lead e quem foi pulado."""

    chosen: Closer | None
    skipped: list[SkippedCloser]

    @property
    def assigned(self) -> bool:
        return self.chosen is not None


class RoundRobinEngine:
    def __init__(self, closers: list[Closer], provider: CalendarProvider) -> None:
        self.provider = provider
        # guardamos TODOS os closers (pra ligar/desligar)...
        self._all: dict[int, Closer] = {c.id: c for c in closers}
        # ...mas a fila só tem os ativos, preservando a ordem.
        self._queue: deque[Closer] = deque(c for c in closers if c.active)

    # -- liga/desliga (o pop-up) -------------------------------------------

    def set_active(self, closer_id: int, active: bool) -> None:
        """Ativa/desativa um closer no fluxo sem apagá-lo."""
        closer = self._all[closer_id]
        if active and not closer.active:
            closer.active = True
            self._queue.append(closer)  # volta pro fim da fila
        elif not active and closer.active:
            closer.active = False
            # remove da fila (deque não tem .remove por valor eficiente,
            # mas pra 12 closers isso é irrelevante)
            self._queue = deque(c for c in self._queue if c.id != closer_id)

    # -- o coração do rodízio ----------------------------------------------

    def assign(self, start: datetime, duration_minutes: int) -> AssignmentResult:
        """Gira a roleta até achar um closer livre.

        Percorre no máximo uma volta completa da fila. Quem é tocado (livre
        ou ocupado) vai pro fim da fila — então a vez sempre roda.
        """
        skipped: list[SkippedCloser] = []

        # range(len) garante no máximo UMA volta — se ninguém estiver livre,
        # a gente para em vez de girar pra sempre.
        for _ in range(len(self._queue)):
            closer = self._queue[0]
            avail = self.provider.check_availability(closer, start, duration_minutes)

            # quem foi a vez vai pro fim da fila (livre OU ocupado)
            self._queue.rotate(-1)

            if avail.available:
                return AssignmentResult(chosen=closer, skipped=skipped)

            skipped.append(SkippedCloser(closer=closer, availability=avail))

        # deu uma volta inteira e ninguém estava livre
        return AssignmentResult(chosen=None, skipped=skipped)

    # -- utilidades pra inspecionar o estado -------------------------------

    @property
    def queue_order(self) -> list[str]:
        """Ordem atual da fila (útil pra debug e pros testes)."""
        return [c.name for c in self._queue]
