# -*- coding: utf-8 -*-
"""Sustituye las estimaciones semanales de API por 20 EUR/mes reales (indicado por Antonio).

- Elimina las filas semanales de DeepSeek/MiniMax.
- Deja UNA fila por mes: 20 EUR (sep, oct, nov). Agosto conserva los 30 EUR reales jul-ago.
- Reescribe gastos.csv conservando formato y finales de línea.
"""
import csv
import io
from collections import defaultdict
from pathlib import Path

DIR = Path(r"C:/Users/Utente/ARTESALASER/contabilidad")
CSV = DIR / "gastos.csv"
raw = CSV.read_bytes()
eol = "\r\n" if b"\r\n" in raw else "\n"
texto = raw.decode("utf-8-sig")
filas = list(csv.DictReader(io.StringIO(texto)))
campos = list(filas[0].keys())

API = 20.00
conservar = []
nuevas = []
meses = {"2026-09-30": "Consumo API Hermes septiembre 2026", "2026-10-31": "Consumo API Hermes octubre 2026",
         "2026-11-30": "Consumo API Hermes noviembre 2026"}

for f in filas:
    es_api = "deepseek" in (f["proveedor"] + f["concepto"]).lower()
    if not es_api:
        conservar.append(f)
        continue
    # agosto: la fila real de 30 EUR se queda; la de 0,25 se va
    if f["fecha"].startswith("2026-08") and abs(float(f["total"]) - 30.0) < 0.01:
        conservar.append(f)

for fecha, concepto in meses.items():
    nuevas.append({"fecha": fecha, "proveedor": "DeepSeek", "concepto": concepto, "categoria": "API",
                   "base_imponible": "%.2f" % API, "iva": "0.00", "total": "%.2f" % API, "justificante": ""})

antes_api = sum(float(f["total"] or 0) for f in filas if "deepseek" in (f["proveedor"] + f["concepto"]).lower())
salida = conservar + nuevas
salida.sort(key=lambda r: r["fecha"])

buf = io.StringIO()
w = csv.DictWriter(buf, fieldnames=campos, lineterminator=eol)
w.writeheader()
for r in salida:
    w.writerow({k: r.get(k, "") for k in campos})
CSV.write_bytes(buf.getvalue().encode("utf-8-sig"))

despues_api = sum(float(r["total"] or 0) for r in salida if "deepseek" in (r["proveedor"] + r["concepto"]).lower())
print("filas antes:", len(filas), "| despues:", len(salida))
print("API antes: %.2f | API despues: %.2f" % (antes_api, despues_api))
print("gastos totales despues: %.2f" % sum(float(r["total"] or 0) for r in salida))
por_mes = defaultdict(float)
for r in salida:
    if r["categoria"].strip().upper() == "API":
        por_mes[r["fecha"][:7]] += float(r["total"] or 0)
print("API por mes:", {k: round(v, 2) for k, v in sorted(por_mes.items())})
