"""Implementação REAL da agenda via Google Calendar.

Fica num módulo separado de propósito: ele depende das libs do Google, que
são opcionais. Assim os testes e o motor continuam rodando sem instalar nada
do Google. A gente só importa isto quando a integração real está ligada.

Ele implementa o mesmo contrato do FakeCalendarProvider (método
check_availability), então o motor do rodízio nem percebe a diferença.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .models import Availability, Closer

# Pedimos só leitura — o sistema nunca altera a agenda de ninguém.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TZ = ZoneInfo("America/Sao_Paulo")


def get_google_service(credentials_path: str = "credentials.json", token_path: str = "token.json"):
    """Faz login no Google (OAuth) e devolve um cliente da API do Calendar.

    Na primeira vez abre o navegador pra você autorizar e salva um token.json
    pra não precisar logar de novo nas próximas.
    """
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def _localize(dt: datetime) -> datetime:
    """Garante que o horário tenha fuso (a API do Google exige)."""
    return dt.replace(tzinfo=TZ) if dt.tzinfo is None else dt


class GoogleCalendarProvider:
    def __init__(self, service, calendar_ids: dict[int, str]) -> None:
        self.service = service
        # closer.id -> ID do calendário no Google (normalmente o e-mail dele)
        self.calendar_ids = calendar_ids

    def check_availability(
        self, closer: Closer, start: datetime, duration_minutes: int
    ) -> Availability:
        cal_id = self.calendar_ids.get(closer.id)
        if not cal_id:
            # closer sem calendário mapeado -> consideramos sempre livre
            return Availability(available=True)

        start = _localize(start)
        end = start + timedelta(minutes=duration_minutes)

        # Pega os eventos que cruzam a janela da call.
        items = (
            self.service.events()
            .list(
                calendarId=cal_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
            .get("items", [])
        )

        for ev in items:
            summary = ev.get("summary", "Compromisso")
            inicio = ev["start"]

            # Evento de dia inteiro (sem hora) -> tratamos como férias/bloqueio do dia.
            if "date" in inicio:
                return Availability(
                    available=False,
                    reason=f"Dia bloqueado: {summary}",
                    on_vacation=True,
                )

            # Evento com hora -> conflito de horário.
            s = datetime.fromisoformat(inicio["dateTime"])
            e = datetime.fromisoformat(ev["end"]["dateTime"])
            return Availability(
                available=False,
                reason=f"Ocupado: {summary} ({s.strftime('%H:%M')}–{e.strftime('%H:%M')})",
                conflicting_event=summary,
            )

        return Availability(available=True)
