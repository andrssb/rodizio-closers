"""Autoriza no Google e LISTA suas agendas (com os IDs pra usar no CALENDAR_IDS).

Rode UMA vez, depois de salvar o credentials.json na raiz do projeto:

    python setup_google.py

Na primeira vez abre o navegador pra você autorizar. Depois ele imprime todas
as suas agendas e os respectivos IDs (que você cola no CALENDAR_IDS de
app/main.py para cada closer).
"""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")  # terminal do Windows e acentos

from app.google_calendar import get_google_service

if not os.path.exists("credentials.json"):
    print("ERRO: nao encontrei 'credentials.json' na raiz do projeto.")
    print("Baixe ele no Google Cloud Console (passo a passo no README) e")
    print("salve aqui em C:\\Users\\andre\\rodizio-closers\\credentials.json")
    raise SystemExit(1)

print("Abrindo o navegador para autorizar... (faca login e clique em permitir)")
service = get_google_service()

print("\nAutorizado com sucesso. Suas agendas:\n")
items = service.calendarList().list().execute().get("items", [])
for cal in items:
    marca = "  (principal)" if cal.get("primary") else ""
    print(f"  nome: {cal.get('summary')}{marca}")
    print(f"  ID  : {cal['id']}")
    print("  " + "-" * 50)

print("\nPronto. Copie o ID da agenda de cada closer e preencha o")
print("dicionario CALENDAR_IDS em app/main.py (ou me mande os IDs).")
