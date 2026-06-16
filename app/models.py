"""Modelos de domínio do Rodízio de Closers.

Aqui ficam só as "coisas" do nosso mundo: o closer e o resultado de uma
checagem de agenda. Repare que nada aqui sabe o que é Google Calendar,
HubSpot ou banco de dados. Isso é de propósito: o domínio fica limpo e
fácil de testar. As integrações ficam de fora (ver calendar_provider.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


# Durações de call permitidas, em minutos.
# (a "call rápida", a "padrão" e a "longa" que você descreveu)
DURACOES_PERMITIDAS = (30, 45, 60)


@dataclass
class Closer:
    """Um vendedor que pode receber leads no rodízio."""

    id: int
    name: str
    active: bool = True  # o liga/desliga do pop-up mexe aqui


@dataclass
class Availability:
    """Resposta da pergunta: 'esse closer está livre nesse horário?'

    Quando NÃO está livre, a gente guarda o porquê pra mostrar na tela
    (era isso que você pediu: dizer qual evento ocupa a agenda, se está
    de férias, etc.).
    """

    available: bool
    reason: str | None = None              # texto pronto pra exibir no front
    conflicting_event: str | None = None   # nome do evento que bloqueou
    on_vacation: bool = False
    vacation_until: date | None = None
