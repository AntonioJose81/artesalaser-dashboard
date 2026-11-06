# -*- coding: utf-8 -*-
"""Reescribe la pestaña Gastos del espejo de Sheets desde gastos.csv (tras corregir la API)."""
import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path

DIR = Path(r"C:/Users/Utente/ARTESALASER/contabilidad")
SID = json.load(open(r"C:/Users/Utente/AppData/Local/hermes/cache/sheets_contabilidad.json", encoding="utf-8"))["spreadsheet_id"]
TOK = json.load(open(r"C:/Users/Utente/AppData/Local/hermes/google_token.json", encoding="utf-8"))
data = urllib.parse.urlencode({"client_id": TOK["client_id"], "client_secret": TOK["client_secret"],
                               "refresh_token": TOK["refresh_token"], "grant_type": "refresh_token"}).encode()
AT = json.loads(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=data), timeout=25).read())["access_token"]
H = {"Authorization": "Bearer " + AT, "Content-Type": "application/json"}

filas = list(csv.DictReader(open(DIR / "gastos.csv", encoding="utf-8-sig")))
vals = [["fecha", "proveedor", "concepto", "categoria", "base_imponible", "iva", "total", "justificante"]]
for r in filas:
    vals.append([r["fecha"], r["proveedor"], r["concepto"], r["categoria"],
                 float(r["base_imponible"] or 0), float(r["iva"] or 0), float(r["total"] or 0), r["justificante"]])

total = round(sum(float(r["total"] or 0) for r in filas), 2)
n = len(vals)
# 1) datos RAW (cabecera incluida)
url = "https://sheets.googleapis.com/v4/spreadsheets/%s/values/Gastos!A1:H%d?valueInputOption=RAW" % (SID, n)
req = urllib.request.Request(url, data=json.dumps({"values": vals}).encode(), headers=H, method="PUT")
urllib.request.urlopen(req, timeout=60).read()

# 2) fila TOTAL con fórmula
fila_total = n + 1
url2 = "https://sheets.googleapis.com/v4/spreadsheets/%s/values/Gastos!A%d:H%d?valueInputOption=USER_ENTERED" % (SID, fila_total, fila_total)
body = {"values": [["TOTAL", "", "", "", "", "", "=SUM(G2:G%d)" % n, ""]]}
req2 = urllib.request.Request(url2, data=json.dumps(body).encode(), headers=H, method="PUT")
urllib.request.urlopen(req2, timeout=60).read()

# 3) borrar cualquier resto por debajo
url3 = "https://sheets.googleapis.com/v4/spreadsheets/%s/values/Gastos!A%d:H200:clear" % (SID, fila_total + 1)
req3 = urllib.request.Request(url3, data=b"{}", headers=H, method="POST")
urllib.request.urlopen(req3, timeout=60).read()

# 4) verificar
u = "https://sheets.googleapis.com/v4/spreadsheets/%s/values/Gastos!A1:H%d?valueRenderOption=UNFORMATTED_VALUE" % (SID, fila_total)
chk = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60).read())["values"]
print("filas en hoja:", len(chk), "| TOTAL hoja:", chk[-1][6], "| suma CSV:", total)
print("cuadra:", abs(float(chk[-1][6]) - total) < 0.02)
