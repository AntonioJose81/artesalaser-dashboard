# -*- coding: utf-8 -*-
"""Dashboard financiero moderno: genera index.html desde los tres CSV de contabilidad.

Diseño mobile-first, sin dependencias externas (SVG inline), autónomo.
Uso: python nuevo_dashboard.py [dir_contabilidad]
"""
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DIR = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:/Users/Utente/ARTESALASER/contabilidad")
OUT = DIR / "index.html"

MESES = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
         7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}


def leer(nombre, campo_importe):
    p = DIR / nombre
    if not p.exists():
        return []
    out = []
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        try:
            imp = float(r.get(campo_importe) or 0)
        except ValueError:
            continue
        out.append({**r, "importe": imp, "mes": r["fecha"][:7]})
    return out


fac = leer("ingresos_facturados.csv", "total")
sin = leer("ingresos_sin_factura.csv", "importe")
gas = leer("gastos.csv", "total")

meses = sorted({r["mes"] for r in fac + sin + gas})
datos = []
for m in meses:
    f = sum(r["importe"] for r in fac if r["mes"] == m)
    s = sum(r["importe"] for r in sin if r["mes"] == m)
    g = sum(r["importe"] for r in gas if r["mes"] == m)
    datos.append({"mes": m, "etiqueta": MESES[int(m[5:7])] + " '" + m[2:4],
                  "facturado": round(f, 2), "sinFactura": round(s, 2), "gastos": round(g, 2),
                  "ingresos": round(f + s, 2), "neto": round(f + s - g, 2)})

tot = {
    "facturado": round(sum(d["facturado"] for d in datos), 2),
    "sinFactura": round(sum(d["sinFactura"] for d in datos), 2),
    "gastos": round(sum(d["gastos"] for d in datos), 2),
}
tot["ingresos"] = round(tot["facturado"] + tot["sinFactura"], 2)
tot["neto"] = round(tot["ingresos"] - tot["gastos"], 2)

# por proyecto
proy = defaultdict(float)
for r in fac + sin:
    proy[r.get("proyecto") or "Otros"] += r["importe"]
proyectos = sorted(({"nombre": k, "importe": round(v, 2)} for k, v in proy.items()),
                   key=lambda x: -x["importe"])

# por categoría de gasto
cat = defaultdict(float)
for r in gas:
    cat[(r.get("categoria") or "Otros").strip().capitalize()] += r["importe"]
categorias = sorted(({"nombre": k, "importe": round(v, 2)} for k, v in cat.items()),
                    key=lambda x: -x["importe"])[:8]

# últimos movimientos
mov = []
for r in fac:
    mov.append({"fecha": r["fecha"], "tipo": "ingreso", "titulo": r.get("cliente", ""),
                "detalle": r.get("concepto", ""), "importe": r["importe"], "proyecto": r.get("proyecto", "")})
for r in sin:
    mov.append({"fecha": r["fecha"], "tipo": "ingreso", "titulo": r.get("cliente", ""),
                "detalle": r.get("concepto", ""), "importe": r["importe"], "proyecto": r.get("proyecto", "")})
for r in gas:
    mov.append({"fecha": r["fecha"], "tipo": "gasto", "titulo": r.get("proveedor", ""),
                "detalle": r.get("concepto", ""), "importe": r["importe"], "proyecto": r.get("categoria", "")})
mov.sort(key=lambda x: x["fecha"], reverse=True)
mov = mov[:40]

D = json.dumps({"datos": datos, "tot": tot, "proyectos": proyectos,
                "categorias": categorias, "movimientos": mov}, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0b0f17">
<title>ARTESALASER · Finanzas</title>
<style>
:root{
  --bg:#0b0f17; --card:#141b26; --card2:#1b2432; --line:#243040;
  --txt:#eef2f7; --muted:#8b9bb0; --green:#3ddc97; --red:#ff6b6b;
  --blue:#5aa9ff; --gold:#f5c26b;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:var(--bg);color:var(--txt);
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif;
 padding:16px 14px 40px;max-width:560px;margin:0 auto}
h1{font-size:19px;margin:4px 0 2px;letter-spacing:-.3px}
.sub{color:var(--muted);font-size:12.5px;margin-bottom:18px}
.hero{background:linear-gradient(145deg,#1a2433,#121924);border:1px solid var(--line);
 border-radius:18px;padding:18px;margin-bottom:14px}
.hero .lbl{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.8px}
.hero .big{font-size:34px;font-weight:700;letter-spacing:-1px;margin:6px 0 2px}
.hero .delta{font-size:13px;color:var(--muted)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px}
.card .lbl{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px}
.card .val{font-size:19px;font-weight:650;margin-top:5px;letter-spacing:-.4px}
.pos{color:var(--green)} .neg{color:var(--red)} .gold{color:var(--gold)} .blue{color:var(--blue)}
section{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;margin-bottom:14px}
section h2{font-size:14px;margin:0 0 14px;font-weight:600;letter-spacing:-.2px}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:11.5px;color:var(--muted);margin-bottom:10px}
.legend i{width:9px;height:9px;border-radius:3px;display:inline-block;margin-right:5px}
.row{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid #1d2735;font-size:13.5px}
.row:last-child{border-bottom:0}
.row .l{color:var(--muted);font-size:11.5px}
.mov{display:flex;justify-content:space-between;gap:10px;padding:10px 0;border-bottom:1px solid #1d2735}
.mov:last-child{border-bottom:0}
.mov .t{font-size:13.5px;font-weight:600}
.mov .d{font-size:11.5px;color:var(--muted);margin-top:2px}
.mov .a{font-size:14px;font-weight:650;white-space:nowrap}
.bar{height:8px;border-radius:6px;background:#131a25;overflow:hidden;margin-top:7px}
.bar span{display:block;height:100%;border-radius:6px}
.tabs{display:flex;gap:8px;margin-bottom:14px;overflow-x:auto;padding-bottom:2px}
.tab{flex:0 0 auto;padding:8px 14px;border-radius:999px;background:var(--card);
 border:1px solid var(--line);color:var(--muted);font-size:12.5px}
.tab.on{background:#20304a;color:#fff;border-color:#31456a}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:right;color:var(--muted);font-weight:500;font-size:11px;padding:6px 4px;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
td{padding:8px 4px;border-bottom:1px solid #1a2230;text-align:right;white-space:nowrap}
tfoot td{font-weight:700;border-top:1px solid var(--line)}
.hide{display:none}
</style>
</head>
<body>
<h1>ARTESALASER</h1>
<div class="sub" id="rango">Contabilidad</div>

<div class="hero">
  <div class="lbl">Resultado acumulado</div>
  <div class="big" id="neto">—</div>
  <div class="delta" id="delta">—</div>
</div>

<div class="grid">
  <div class="card"><div class="lbl">Ingresos</div><div class="val pos" id="ing">—</div></div>
  <div class="card"><div class="lbl">Gastos</div><div class="val neg" id="gas">—</div></div>
  <div class="card"><div class="lbl">Facturado</div><div class="val blue" id="fac">—</div></div>
  <div class="card"><div class="lbl">Sin factura</div><div class="val gold" id="sin">—</div></div>
</div>

<section>
  <h2>Evolución por meses</h2>
  <div class="legend">
    <span><i style="background:var(--green)"></i>Ingresos</span>
    <span><i style="background:var(--red)"></i>Gastos</span>
    <span><i style="background:var(--blue)"></i>Resultado</span>
  </div>
  <div id="chart"></div>
</section>

<div class="tabs">
  <div class="tab on" data-t="mes">Por mes</div>
  <div class="tab" data-t="proy">Por proyecto</div>
  <div class="tab" data-t="cat">Gastos por tipo</div>
</div>

<section id="tabla"></section>

<section>
  <h2>Últimos movimientos</h2>
  <div id="movs"></div>
</section>

<script>
const D = __DATA__;
const miles = v => (v<0?"\u2212":"" ) + Math.abs(v).toLocaleString("es-ES",{minimumFractionDigits:2,maximumFractionDigits:2,useGrouping:true});
const eur = v => miles(v) + " €";
const corto = v => Math.abs(v)>=1000 ? (v/1000).toLocaleString("es-ES",{maximumFractionDigits:1})+"k" : Math.round(v);

document.getElementById("neto").textContent = miles(D.tot.neto) + " €";
document.getElementById("neto").className = "big " + (D.tot.neto>=0?"pos":"neg");
document.getElementById("delta").textContent = D.datos.length + " meses registrados · margen " +
  (D.tot.ingresos? Math.round(D.tot.neto/D.tot.ingresos*100) : 0) + "%";
document.getElementById("ing").textContent = miles(D.tot.ingresos) + " €";
document.getElementById("gas").textContent = miles(D.tot.gastos) + " €";
document.getElementById("fac").textContent = miles(D.tot.facturado) + " €";
document.getElementById("sin").textContent = miles(D.tot.sinFactura) + " €";
document.getElementById("rango").textContent = "Julio 2026 — hoy";

// gráfico de barras SVG
(function(){
  const w = Math.min(window.innerWidth-60, 500), h = 210, pad = 26;
  const n = D.datos.length;
  const max = Math.max(...D.datos.map(d=>Math.max(d.ingresos,d.gastos)),1);
  const minNeto = Math.min(...D.datos.map(d=>d.neto),0);
  const min = Math.min(minNeto, 0);
  const gw = (w-pad)/n, bw = Math.min(16, gw/3.4);
  const puntos = [];
  let s = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" role="img">`;
  const escala = v => h-30-(h-50)*(v-min)/(max-min);
  [0,.25,.5,.75,1].forEach(f=>{
    const v = min + (max-min)*f;
    const y = escala(v);
    s += `<line x1="0" y1="${y}" x2="${w}" y2="${y}" stroke="#1e2836" stroke-width="1"/>`;
    s += `<text x="0" y="${y-4}" fill="#7c8ba1" font-size="10.5">${corto(v)}</text>`;
  });
  D.datos.forEach((d,i)=>{
    const x0 = pad + i*gw + gw/2;
    const yI = escala(d.ingresos), yG = escala(d.gastos), base = escala(0);
    s += `<rect x="${x0-bw-1}" y="${yI}" width="${bw}" height="${Math.max(base-yI,0)}" rx="3" fill="#3ddc97"/>`;
    s += `<rect x="${x0+1}" y="${yG}" width="${bw}" height="${Math.max(base-yG,0)}" rx="3" fill="#ff6b6b"/>`;
    const yN = escala(d.neto);
    puntos.push([x0,yN]);
    s += `<text x="${x0}" y="${h-12}" fill="#9fb0c4" font-size="11.5" text-anchor="middle">${d.etiqueta}</text>`;
  });
  if (puntos.length > 1){
    s += `<polyline points="${puntos.map(p=>p.join(",")).join(" ")}" fill="none" stroke="#5aa9ff" stroke-width="2.5" stroke-linejoin="round" opacity=".95"/>`;
  }
  puntos.forEach(p=>{ s += `<circle cx="${p[0]}" cy="${p[1]}" r="4.5" fill="#0b0f17" stroke="#5aa9ff" stroke-width="2.5"/>`; });
  s += "</svg>";
  document.getElementById("chart").innerHTML = s;
})();

function tabla(cab, filas, total){
  let h = `<table><thead><tr>${cab.map((c,i)=>`<th>${c}</th>`).join("")}</tr></thead><tbody>`;
  filas.forEach(f=>{
    h += "<tr>" + f.map((c,i)=>{
      const neg = i && String(c).indexOf("\u2212") === 0;
      return "<td" + (i ? ' style="color:' + (neg ? "var(--red)" : "inherit") + '"' : "") + ">" + c + "</td>";
    }).join("") + "</tr>";
  });
  h += "</tbody>";
  if(total) h += `<tfoot><tr>${total.map(c=>`<td>${c}</td>`).join("")}</tr></tfoot>`;
  return h + "</table>";
}

function pintar(t){
  const el = document.getElementById("tabla");
  if (t==="mes"){
    el.innerHTML = tabla(["Mes","Ingresos","Gastos","Resultado"],
      D.datos.map(d=>[d.etiqueta, eur(d.ingresos), eur(d.gastos), eur(d.neto)]),
      ["Total", eur(D.tot.ingresos), eur(D.tot.gastos), eur(D.tot.neto)]);
  } else if (t==="proy"){
    const maxp = D.proyectos[0] ? D.proyectos[0].importe : 1;
    el.innerHTML = "<h2>Ingresos por proyecto</h2>" + D.proyectos.map(p=>`
      <div style="padding:8px 0">
        <div class="row" style="border:0;padding:0"><span>${p.nombre}</span><b>${eur(p.importe)}</b></div>
        <div class="bar"><span style="width:${p.importe/maxp*100}%;background:var(--blue)"></span></div>
      </div>`).join("");
  } else {
    const maxc = D.categorias[0] ? D.categorias[0].importe : 1;
    el.innerHTML = "<h2>Gastos por tipo</h2>" + D.categorias.map(c=>`
      <div style="padding:8px 0">
        <div class="row" style="border:0;padding:0"><span>${c.nombre}</span><b>${eur(c.importe)}</b></div>
        <div class="bar"><span style="width:${c.importe/maxc*100}%;background:var(--red)"></span></div>
      </div>`).join("");
  }
}
pintar("mes");
document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>{
  document.querySelectorAll(".tab").forEach(x=>x.classList.remove("on"));
  t.classList.add("on"); pintar(t.dataset.t);
});

document.getElementById("movs").innerHTML = D.movimientos.map(m=>`
  <div class="mov">
    <div>
      <div class="t">${m.titulo}</div>
      <div class="d">${m.fecha} · ${m.detalle}${m.proyecto?" · "+m.proyecto:""}</div>
    </div>
    <div class="a ${m.tipo==='ingreso'?'pos':'neg'}">${m.tipo==='ingreso'?'+':'−'}${eur(m.importe)}</div>
  </div>`).join("");
</script>
</body>
</html>
"""

OUT.write_text(HTML.replace("__DATA__", D), encoding="utf-8")
print("generado:", OUT, len(HTML), "chars")
print("meses:", [d["etiqueta"] for d in datos])
print("neto:", tot["neto"], "| ingresos:", tot["ingresos"], "| gastos:", tot["gastos"])
