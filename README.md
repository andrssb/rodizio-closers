# Rodízio de Closers

Distribuição **justa** de leads entre vendedores (closers), com checagem de
agenda em tempo real. Em vez de mandar o lead pro primeiro que aparece (ou
pior, sempre pro mesmo), o sistema usa um rodízio (**round-robin**) que
respeita a vez de cada um — e pula automaticamente quem está ocupado ou de
férias, explicando o porquê.

> Projeto nascido de uma dor real de operação de vendas: como repartir leads
> entre closers sem injustiça e sem mandar reunião pra quem não tem horário.

## Qual é a sua função?

- **Rodízio justo (round-robin)** entre os closers — cada um tem a sua vez.
- **Checa a agenda** antes de atribuir: se o closer da vez não tem horário
  pra uma call de **30, 45 ou 60 min**, ele é pulado e vai pro fim da fila.
- **Explica o motivo** de quem foi pulado: qual evento ocupa a agenda
  (ex: *"Ocupado: Reunião de Pipeline (13:30–15:00)"*) ou se está de
  férias (e até quando).
- **Liga/desliga** de closer no fluxo (sem apagar o cadastro).
- **Integração com HubSpot** para registrar a atribuição (atualmente
  mockada; ver Roadmap).

## Decisões de arquitetura

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

## Estrutura

```
app/
  models.py             # Closer, Availability (o "mundo" do problema)
  calendar_provider.py  # contrato de agenda + implementação falsa (mock)
  engine.py             # o motor do rodízio (round-robin)
tests/
  test_engine.py        # testes que provam a lógica
```

## Como rodar

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

## Extensão opcional: agenda real via Google Calendar

**Isto é opcional — o app funciona 100% sem nada disso.** Por padrão ele usa
uma **agenda simulada (mock)**, que já demonstra toda a lógica do rodízio.

O conector real do Google (`app/google_calendar.py`) já está pronto e
encaixado no sistema, com fallback automático: ele só é usado se você
fornecer as credenciais abaixo. É um ponto de extensão, não um requisito.

Para quem quiser ligar a agenda **real** do Google Calendar um dia:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/) e crie
   um projeto (ou use um existente).
2. Em **APIs e Serviços > Biblioteca**, habilite a **Google Calendar API**.
3. Em **APIs e Serviços > Tela de consentimento OAuth**, configure como
   *Externo* e adicione seu e-mail como usuário de teste.
4. Em **APIs e Serviços > Credenciais > Criar credenciais > ID do cliente
   OAuth**, escolha o tipo **App para computador**. Baixe o JSON e salve na
   raiz do projeto como **`credentials.json`**.
5. Pegue o ID de cada calendário (Google Agenda > Configurações do calendário
   > *Integrar agenda* > **ID da agenda**; geralmente é o e-mail) e preencha
   o dicionário `CALENDAR_IDS` em `app/main.py`, mapeando `closer.id -> ID`.
6. Rode `uvicorn app.main:app --reload`. Na primeira vez abre o navegador pra
   você autorizar; depois disso fica salvo em `token.json`.

> Dica pra demo: você não precisa de 12 contas. Crie alguns calendários
> secundários na sua própria Google Agenda (Adicionar > Criar nova agenda),
> coloque eventos de teste e mapeie só esses closers. Os demais ficam livres.
>
> `credentials.json` e `token.json` são segredos e já estão no `.gitignore`.

## Roadmap

- [x] Motor do rodízio (round-robin) + testes
- [x] API REST com FastAPI (atribuir / ligar-desligar)
- [x] Front com a roleta animada
- [x] Estrutura plugável de agenda (mock + conector Google com fallback)
- [ ] Conectar o Google Calendar de verdade (opcional — requer credenciais)
- [ ] Integração real com HubSpot
- [ ] Persistência em banco (SQLAlchemy)

## Stack

Python · FastAPI · SQLAlchemy · pytest · (Google Calendar API · HubSpot)
