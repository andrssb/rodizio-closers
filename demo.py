"""Demonstração do motor do rodízio no terminal.

Não faz parte do app final — é só pra você VER a lógica funcionando antes
de existir tela/API. Rode com:  python demo.py
"""

import sys
from datetime import date, datetime

# o terminal do Windows usa cp1252 e não exibe emoji; forçamos UTF-8
sys.stdout.reconfigure(encoding="utf-8")

from app.calendar_provider import FakeCalendarProvider, FakeEvent, FakeVacation
from app.engine import RoundRobinEngine
from app.models import Closer

# ---------------------------------------------------------------------------
# 12 closers fictícios
# ---------------------------------------------------------------------------
NOMES = [
    "Ana", "Bruno", "Carla", "Diego", "Elaine", "Felipe",
    "Gabriela", "Heitor", "Isabela", "João", "Karla", "Lucas",
]
closers = [Closer(i + 1, nome) for i, nome in enumerate(NOMES)]

# Agendas de exemplo (data da demo: 17/06/2026)
eventos = [
    FakeEvent(1, "Reunião de Pipeline", datetime(2026, 6, 17, 13, 30), datetime(2026, 6, 17, 15, 0)),
    FakeEvent(2, "Almoço com cliente", datetime(2026, 6, 17, 12, 0), datetime(2026, 6, 17, 14, 30)),
    FakeEvent(4, "Demo produto", datetime(2026, 6, 17, 14, 0), datetime(2026, 6, 17, 14, 45)),
]
ferias = [
    FakeVacation(3, date(2026, 6, 15), date(2026, 6, 20)),  # Carla de férias
]

engine = RoundRobinEngine(closers, FakeCalendarProvider(events=eventos, vacations=ferias))


def girar(titulo, quando, duracao):
    print(f"\n{'=' * 60}")
    print(f"{titulo}  (call de {duracao} min às {quando.strftime('%H:%M')})")
    print("=" * 60)
    r = engine.assign(quando, duracao)

    for s in r.skipped:
        print(f"   - Pulou {s.closer.name:<10} -> {s.availability.reason}")

    if r.assigned:
        print(f"   >> LEAD VAI PARA: {r.chosen.name}")
    else:
        print("   >> Ninguém disponível nesse horário.")

    print(f"   Fila agora: {' -> '.join(engine.queue_order)}")


# ---------------------------------------------------------------------------
# Sequência de calls chegando
# ---------------------------------------------------------------------------
print("\n>>> 12 closers no rodízio. Vamos distribuir leads que vão chegando...")

girar("Lead 1", datetime(2026, 6, 17, 14, 0), 30)   # Ana ocupada -> pula
girar("Lead 2", datetime(2026, 6, 17, 14, 0), 45)
girar("Lead 3", datetime(2026, 6, 17, 14, 0), 60)

print("\n>>> Gerente desliga o Felipe no pop-up...")
engine.set_active(6, False)
girar("Lead 4", datetime(2026, 6, 17, 16, 0), 30)   # horário livre pra todos

print()
