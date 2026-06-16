# 🎯 Rodízio de Closers

Distribuição **justa** de leads entre vendedores (closers), com checagem de
agenda em tempo real. Em vez de mandar o lead pro primeiro que aparece (ou
pior, sempre pro mesmo), o sistema usa um rodízio (**round-robin**) que
respeita a vez de cada um — e pula automaticamente quem está ocupado ou de
férias, explicando o porquê.

> Projeto nascido de uma dor real de operação de vendas: como repartir leads
> entre closers sem injustiça e sem mandar reunião pra quem não tem horário.

## ✨ O que ele faz

- **Rodízio justo (round-robin)** entre os closers — cada um tem a sua vez.
- **Checa a agenda** antes de atribuir: se o closer da vez não tem horário
  pra uma call de **30, 45 ou 60 min**, ele é pulado e vai pro fim da fila.
- **Explica o motivo** de quem foi pulado: qual evento ocupa a agenda
  (ex: *"Ocupado: Reunião de Pipeline (13:30–15:00)"*) ou se está de
  férias (e até quando).
- **Liga/desliga** de closer no fluxo (sem apagar o cadastro).
- **Integração com HubSpot** para registrar a atribuição (atualmente
  mockada; ver Roadmap).

## 🧠 Decisões de arquitetura (o "porquê")

- **É round-robin, não aleatório.** Distribuição de lead precisa ser justa
  e previsível, não sorte. A "roleta girando" é só a interface; por baixo é
  uma fila.
- **Inversão de dependência na agenda.** O motor não conhece o Google
  Calendar — ele conversa com um contrato (`CalendarProvider`). Existem duas
  implementações: uma falsa (`FakeCalendarProvider`, pra rodar/demonstrar
  offline) e a real do Google (em construção). Trocar a fonte não exige
  mexer no motor.
- **Domínio sem dependências externas.** As regras (`engine.py`,
  `models.py`) não importam nada de web/API/banco — por isso dá pra testar
  tudo em milissegundos.

## 🗂️ Estrutura

```
app/
  models.py             # Closer, Availability (o "mundo" do problema)
  calendar_provider.py  # contrato de agenda + implementação falsa (mock)
  engine.py             # o motor do rodízio (round-robin)
tests/
  test_engine.py        # testes que provam a lógica
```

## ▶️ Como rodar

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt

# rodar os testes
pytest

# ver a lógica no terminal
python demo.py

# subir a interface web (a roleta)
uvicorn app.main:app --reload
# depois abra http://127.0.0.1:8000
```

## 🛣️ Roadmap

- [x] Motor do rodízio (round-robin) + testes
- [x] API REST com FastAPI (atribuir / ligar-desligar)
- [x] Front com a roleta animada
- [ ] Agenda real via Google Calendar (`GoogleCalendarProvider`)
- [ ] Integração real com HubSpot
- [ ] Persistência em banco (SQLAlchemy)

## 🧪 Stack

Python · FastAPI · SQLAlchemy · pytest · (Google Calendar API · HubSpot)
