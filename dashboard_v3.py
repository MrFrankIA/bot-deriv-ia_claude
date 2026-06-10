# -*- coding: utf-8 -*-
from flask import Flask, request
import csv, os, re, time, json

app = Flask(__name__)

try:
    from config import FILTRO_V5_ACTIVO, HORAS_V5_BLOQUEADAS
except ImportError:
    FILTRO_V5_ACTIVO  = None
    HORAS_V5_BLOQUEADAS = None

ARCHIVO_OPERACIONES_PAPER = "operaciones_paper.csv"
ARCHIVO_OPERACIONES_DEMO  = "operaciones_demo.csv"
ARCHIVO_SENALES     = "senales.csv"
ARCHIVO_CONFIG      = "config.py"

# La cuenta demo de Deriv (DOT) arranca con 10000 USD virtuales; el CSV demo no
# guarda balance corrido, asi que se reconstruye desde el profit acumulado.
BALANCE_INICIAL_PAPER = 1000.0
BALANCE_INICIAL_DEMO  = 10000.0

MODOS = {
    "demo":  dict(archivo=ARCHIVO_OPERACIONES_DEMO,  inicial=BALANCE_INICIAL_DEMO,
                  etiqueta="DEMO (real)",   color="#22C55E"),
    "paper": dict(archivo=ARCHIVO_OPERACIONES_PAPER, inicial=BALANCE_INICIAL_PAPER,
                  etiqueta="PAPER (sim)",   color="#60a5fa"),
}

BOT_ACTIVO_SEG    = 120
BOT_SIN_SENAL_SEG = 600

COLUMNAS_EXTRA = ["estructura", "bos", "choch", "sweep", "contexto_valido"]

NOMBRES_ACTIVO = {
    "R_10":  "Volatility 10 Index",
    "R_25":  "Volatility 25 Index",
    "R_50":  "Volatility 50 Index",
    "R_75":  "Volatility 75 Index",
    "R_100": "Volatility 100 Index",
}

def numero(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def leer_operaciones(archivo):
    if not os.path.exists(archivo):
        return []
    with open(archivo, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        filas  = list(reader)
    header_antiguo = all(c not in header for c in COLUMNAS_EXTRA)
    resultado = []
    for fila in filas:
        norm = {}
        for k, v in fila.items():
            if k is None:
                if header_antiguo and isinstance(v, list):
                    for nombre, valor in zip(COLUMNAS_EXTRA, v):
                        norm[nombre] = valor.strip() if valor else ""
                continue
            if isinstance(v, list):
                continue
            norm[k] = v.strip() if v else ""
        resultado.append(norm)
    return resultado


def normalizar_demo(ops, balance_inicial):
    """El CSV demo guarda 'profit' (no 'profit_loss') y no lleva balance/drawdown.
    Se reconstruyen para que el resto del dashboard (pensado para paper) funcione
    sin cambios. El balance corrido = balance_inicial + profit acumulado refleja
    el saldo real de la cuenta demo (solo este bot la opera)."""
    bal = balance_inicial
    eq_max = balance_inicial
    for op in ops:
        pl = numero(op.get("profit", 0))
        op["profit_loss"] = "{:.2f}".format(pl)
        op.setdefault("stake", op.get("buy_price", ""))
        bal += pl
        if bal > eq_max:
            eq_max = bal
        op["balance"]  = "{:.2f}".format(bal)
        op["drawdown"] = "{:.2f}".format(eq_max - bal)
    return ops


def leer_senales():
    if not os.path.exists(ARCHIVO_SENALES):
        return []
    with open(ARCHIVO_SENALES, mode="r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def leer_activo():
    if not os.path.exists(ARCHIVO_CONFIG):
        return "DESCONOCIDO", "DESCONOCIDO"
    with open(ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
        contenido = f.read()
    m = re.search(r'ACTIVO\s*=\s*["\'](.+?)["\']', contenido)
    simbolo = m.group(1) if m else "DESCONOCIDO"
    nombre  = NOMBRES_ACTIVO.get(simbolo, simbolo)
    return simbolo, nombre


def estado_bot():
    if not os.path.exists(ARCHIVO_SENALES):
        return "DETENIDO", "#EF4444", "archivo no encontrado"
    seg = time.time() - os.path.getmtime(ARCHIVO_SENALES)
    mi, s = int(seg // 60), int(seg % 60)
    if seg < BOT_ACTIVO_SEG:
        return "ACTIVO", "#22C55E", "hace {}s".format(int(seg))
    if seg < BOT_SIN_SENAL_SEG:
        return "SIN SENALES", "#EAB308", "hace {}m {}s".format(mi, s)
    return "DETENIDO", "#EF4444", "hace {}m {}s".format(mi, s)


def calcular_metricas(ops):
    total = len(ops)
    ganadas = perdidas = 0
    profit_total = drawdown_max = balance_actual = ps2 = ps3 = 0.0
    for op in ops:
        res = op.get("resultado", "")
        pl  = numero(op.get("profit_loss", 0))
        dd  = numero(op.get("drawdown", 0))
        sc  = numero(op.get("score_senal", 0))
        balance_actual = numero(op.get("balance", 0))
        profit_total  += pl
        if res == "CORRECTA":
            ganadas += 1
        else:
            perdidas += 1
        if dd > drawdown_max:
            drawdown_max = dd
        if sc == 2:
            ps2 += pl
        elif sc >= 3:
            ps3 += pl
    wr = (ganadas / total * 100) if total else 0.0
    return dict(total=total, ganadas=ganadas, perdidas=perdidas,
                wr=wr, profit_total=round(profit_total,2),
                drawdown_max=round(drawdown_max,2),
                balance_actual=balance_actual,
                ps2=round(ps2,2), ps3=round(ps3,2))


def calcular_ranking_campo(ops, campo):
    grupos = {}
    for op in ops:
        val = op.get(campo, "") or ""
        if val not in grupos:
            grupos[val] = dict(ops=0, gan=0, per=0, profit=0.0)
        g = grupos[val]
        g["ops"] += 1
        g["profit"] += numero(op.get("profit_loss", 0))
        if op.get("resultado", "") == "CORRECTA":
            g["gan"] += 1
        else:
            g["per"] += 1
    filas = []
    for cat, g in grupos.items():
        wr = (g["gan"] / g["ops"] * 100) if g["ops"] else 0.0
        filas.append(dict(cat=cat or "Sin dato", ops=g["ops"],
                          gan=g["gan"], per=g["per"],
                          wr=round(wr,1), profit=round(g["profit"],2)))
    filas.sort(key=lambda x: (-x["wr"], -x["ops"]))
    return filas


def calcular_top_contextos(ops, top=5):
    grupos = {}
    for op in ops:
        est = op.get("estructura","") or ""
        bos = op.get("bos","") or ""
        ch  = op.get("choch","") or ""
        ctx = op.get("contexto_valido","") or ""
        if not any([est, bos, ch, ctx]):
            continue
        clave = "{}|{}|{}|{}".format(est, bos, ch, ctx)
        if clave not in grupos:
            grupos[clave] = dict(ops=0, gan=0, profit=0.0,
                                 estructura=est, bos=bos, choch=ch, ctx=ctx)
        g = grupos[clave]
        g["ops"]    += 1
        g["profit"] += numero(op.get("profit_loss",0))
        if op.get("resultado","") == "CORRECTA":
            g["gan"] += 1
    return sorted(grupos.values(), key=lambda x: -x["profit"])[:top]


def preparar_series(ops):
    horas = []; balances = []; profits = []; dds = []
    acum = 0.0
    for op in ops:
        horas.append(op.get("hora",""))
        balances.append(numero(op.get("balance",0)))
        acum += numero(op.get("profit_loss",0))
        profits.append(round(acum,2))
        dds.append(numero(op.get("drawdown",0)))
    return horas, balances, profits, dds


def fmt_p(v):
    return ("+{:.2f}".format(v) if v >= 0 else "{:.2f}".format(v))


def col_p(v):
    return "#22C55E" if v >= 0 else "#EF4444"


def tabla_ranking_html(filas, titulo, tbl_id):
    tiene_reales = any(f["cat"] != "Sin dato" for f in filas)
    if not filas or not tiene_reales:
        return (
            '<div class="card"><h2>' + titulo + '</h2>'
            '<p class="aviso">Sin datos aun. Se poblaran cuando el bot opere '
            'con contexto completo.</p></div>'
        )
    rows = ""
    for f in filas:
        sd = ' class="sin-dato"' if f["cat"] == "Sin dato" else ""
        pc = col_p(f["profit"])
        rows += (
            "<tr{}><td>{}</td><td>{}</td>"
            '<td style="color:#22C55E">{}</td>'
            '<td style="color:#EF4444">{}</td>'
            "<td>{:.1f}%</td>"
            '<td style="color:{};font-weight:bold">{}</td></tr>'
        ).format(sd, f["cat"], f["ops"], f["gan"], f["per"],
                 f["wr"], pc, fmt_p(f["profit"]))
    return (
        '<div class="card"><h2>' + titulo + '</h2>'
        '<table id="' + tbl_id + '">'
        '<tr><th>Categoria</th><th>Ops</th><th>Gan</th>'
        '<th>Per</th><th>WR%</th><th>Profit</th></tr>'
        + rows + '</table></div>'
    )


def calcular_simulacion_v5(ops, balance_inicial=1000.0):
    horas_v5 = HORAS_V5_BLOQUEADAS or set()
    filtradas = []
    bloqueadas = []
    for op in ops:
        est  = op.get("estructura", "") or ""
        bos  = op.get("bos", "")        or ""
        hora = (op.get("hora", "") or "")[:2].zfill(2)
        if est == "ESTRUCTURA_ALCISTA" and bos == "SIN_BOS" and hora in horas_v5:
            bloqueadas.append(op)
        else:
            filtradas.append(op)
    def m(lst):
        total = len(lst)
        gan = sum(1 for o in lst if o.get("resultado","") == "CORRECTA")
        pl  = sum(numero(o.get("profit_loss",0)) for o in lst)
        wr  = (gan / total * 100) if total else 0.0
        exp = (pl / total)        if total else 0.0
        # drawdown max via acumulado
        bal = balance_inicial; eq_max = balance_inicial; dd_max = 0.0
        for o in lst:
            bal += numero(o.get("profit_loss",0))
            if bal > eq_max: eq_max = bal
            dd = eq_max - bal
            if dd > dd_max: dd_max = dd
        return dict(total=total, gan=gan, wr=round(wr,2),
                    profit=round(pl,2), exp=round(exp,4), dd_max=round(dd_max,2))
    return m(ops), m(filtradas), len(bloqueadas)


def calcular_promedio_diario(ops):
    """Retorna None si no hay campo fecha en el CSV."""
    tiene_fecha = any(op.get("fecha","").strip() for op in ops)
    if not tiene_fecha:
        return None
    dias = {}
    for op in ops:
        fecha = op.get("fecha","").strip()
        if fecha:
            dias[fecha] = dias.get(fecha, 0) + 1
    if not dias:
        return None
    total = sum(dias.values())
    promedio = total / len(dias)
    return dict(promedio=round(promedio,1), dias=len(dias), total=total)


def calcular_alertas(ops, senales, archivo_ops):
    alertas = []
    ahora = time.time()
    # Alerta señal reciente
    if senales:
        mtime = os.path.getmtime(ARCHIVO_SENALES) if os.path.exists(ARCHIVO_SENALES) else 0
        if ahora - mtime > 120:
            seg = int(ahora - mtime)
            alertas.append("Sin senales recientes hace {}s".format(seg))
    else:
        alertas.append("No hay senales registradas")
    # Alerta operacion reciente (basada en mtime del CSV)
    if os.path.exists(archivo_ops):
        mtime_op = os.path.getmtime(archivo_ops)
        if ops and ahora - mtime_op > 1800:
            seg = int(ahora - mtime_op)
            alertas.append("Sin operaciones nuevas hace {}s".format(seg))
    return alertas

@app.route("/")
def inicio():
    modo = request.args.get("modo", "demo")
    if modo not in MODOS:
        modo = "demo"
    cfg_modo = MODOS[modo]

    ops     = leer_operaciones(cfg_modo["archivo"])
    if modo == "demo":
        ops = normalizar_demo(ops, cfg_modo["inicial"])
    senales = leer_senales()

    simbolo, nombre_activo = leer_activo()
    estado, color_estado, tiempo_estado = estado_bot()

    m   = calcular_metricas(ops)
    r_e = calcular_ranking_campo(ops, "estructura")
    r_b = calcular_ranking_campo(ops, "bos")
    r_c = calcular_ranking_campo(ops, "choch")
    r_x = calcular_ranking_campo(ops, "contexto_valido")
    top = calcular_top_contextos(ops)

    horas, balances, profits, dds = preparar_series(ops)

    ultima_op  = ops[-1]     if ops     else None
    ultima_sig = senales[-1] if senales else None

    # ── ultima operacion ──────────────────────────────────────────────────────
    if ultima_op:
        uo_res   = ultima_op.get("resultado","-")
        uo_color = "#22C55E" if uo_res == "CORRECTA" else "#EF4444"
        uo_pl    = numero(ultima_op.get("profit_loss",0))
        html_uo  = (
            '<div class="card"><h2>Ultima Operacion</h2>'
            '<div class="grid g3">'
            '<div class="metric"><span class="lbl">Hora</span>'
            '<span class="val">' + ultima_op.get("hora","-") + '</span></div>'
            '<div class="metric"><span class="lbl">Senal</span>'
            '<span class="val">' + ultima_op.get("senal","-") + '</span></div>'
            '<div class="metric"><span class="lbl">Resultado</span>'
            '<span class="val" style="color:' + uo_color + '">' + uo_res + '</span></div>'
            '<div class="metric"><span class="lbl">P&L</span>'
            '<span class="val" style="color:' + col_p(uo_pl) + ';font-weight:bold">' + fmt_p(uo_pl) + '</span></div>'
            '<div class="metric"><span class="lbl">Balance</span>'
            '<span class="val">{:.2f}</span></div>'.format(numero(ultima_op.get("balance",0)))
            + '<div class="metric"><span class="lbl">Score</span>'
            '<span class="val">' + ultima_op.get("score_senal","-") + '</span></div>'
            '</div></div>'
        )
    else:
        html_uo = ""

    # ── ultima senal ──────────────────────────────────────────────────────────
    if ultima_sig:
        us_tec = ultima_sig.get("senal_tecnica","-")
        us_col = "#22C55E" if us_tec=="COMPRAR" else ("#EF4444" if us_tec=="VENDER" else "#9CA3AF")
        html_us = (
            '<div class="card"><h2>Ultima Senal Generada</h2>'
            '<div class="grid g3">'
            '<div class="metric"><span class="lbl">Hora</span>'
            '<span class="val">' + ultima_sig.get("hora","-") + '</span></div>'
            '<div class="metric"><span class="lbl">Senal</span>'
            '<span class="val" style="color:' + us_col + '">' + us_tec + '</span></div>'
            '<div class="metric"><span class="lbl">Score</span>'
            '<span class="val">' + ultima_sig.get("score_senal","-") + '</span></div>'
            '<div class="metric"><span class="lbl">Patron</span>'
            '<span class="val">' + ultima_sig.get("patron_actual","-") + '</span></div>'
            '<div class="metric"><span class="lbl">Permitida</span>'
            '<span class="val">' + ultima_sig.get("permitida","-") + '</span></div>'
            '<div class="metric"><span class="lbl">Motivo</span>'
            '<span class="val small">' + (ultima_sig.get("motivo_bloqueo","") or "&mdash;") + '</span></div>'
            '</div></div>'
        )
    else:
        html_us = ""

    # ── tabla ultimas 10 ──────────────────────────────────────────────────────
    ultimas = ops[-10:]
    filas_t = ""
    for op in reversed(ultimas):
        res = op.get("resultado","")
        rc  = "#22C55E" if res=="CORRECTA" else "#EF4444"
        pl  = numero(op.get("profit_loss",0))
        filas_t += (
            "<tr><td>{}</td><td>{}</td>"
            '<td style="color:{};font-weight:bold">{}</td>'
            '<td style="color:{};font-weight:bold">{}</td>'
            "<td>{:.2f}</td><td>{}</td><td>{}</td></tr>"
        ).format(op.get("hora",""), op.get("senal",""),
                 rc, res, col_p(pl), fmt_p(pl),
                 numero(op.get("balance",0)),
                 op.get("score_senal",""), op.get("patron",""))

    # ── top contextos ─────────────────────────────────────────────────────────
    if top:
        rows_top = ""
        for i, g in enumerate(top, 1):
            wr  = (g["gan"] / g["ops"] * 100) if g["ops"] else 0.0
            pc  = col_p(g["profit"])
            cat = "{} / {} / {}".format(g["estructura"] or "-",
                                         g["bos"] or "-",
                                         g["choch"] or "-")
            rows_top += (
                "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td>"
                '<td>{:.1f}%</td><td style="color:{};font-weight:bold">{}</td></tr>'
            ).format(i, cat, g["ops"], g["gan"], wr, pc, fmt_p(g["profit"]))
        html_top = (
            '<div class="card"><h2>Top 5 Contextos Ganadores</h2>'
            "<table><tr><th>#</th><th>Estructura / BOS / CHOCH</th>"
            "<th>Ops</th><th>Gan</th><th>WR%</th><th>Profit</th></tr>"
            + rows_top + "</table></div>"
        )
    else:
        html_top = (
            '<div class="card"><h2>Top 5 Contextos Ganadores</h2>'
            '<p class="aviso">Sin datos aun. Se poblaran cuando el bot opere '
            "con contexto completo.</p></div>"
        )

    # ── rankings ──────────────────────────────────────────────────────────────
    html_re = tabla_ranking_html(r_e, "Ranking por Estructura",      "tbl-est")
    html_rb = tabla_ranking_html(r_b, "Ranking por BOS",             "tbl-bos")
    html_rc = tabla_ranking_html(r_c, "Ranking por CHOCH",           "tbl-choch")
    html_rx = tabla_ranking_html(r_x, "Ranking por Contexto Valido", "tbl-ctx")

    # ── V5 simulation ────────────────────────────────────────────────────────
    m_actual, m_v5, ops_bloqueadas = calcular_simulacion_v5(ops, cfg_modo["inicial"])

    # ── promedio diario ───────────────────────────────────────────────────────
    promedio_info = calcular_promedio_diario(ops)

    # ── alertas ───────────────────────────────────────────────────────────────
    alertas = calcular_alertas(ops, senales, cfg_modo["archivo"])

    # ── ultima op completa (expand) ───────────────────────────────────────────
    if ultima_op:
        campos_ctx = [
            ("Estructura",     ultima_op.get("estructura","-") or "-"),
            ("BOS",            ultima_op.get("bos","-") or "-"),
            ("CHOCH",          ultima_op.get("choch","-") or "-"),
            ("Ctx Valido",     ultima_op.get("contexto_valido","-") or "-"),
        ]
        ctx_html = "".join(
            '<div class="metric"><span class="lbl">{}</span>'
            '<span class="val small">{}</span></div>'.format(k, v)
            for k, v in campos_ctx
        )
        uo_res   = ultima_op.get("resultado","-")
        uo_color = "#22C55E" if uo_res == "CORRECTA" else "#EF4444"
        uo_pl    = numero(ultima_op.get("profit_loss",0))
        html_uo  = (
            '<div class="card"><h2>Ultima Operacion</h2>'
            '<div class="grid g3">'
            '<div class="metric"><span class="lbl">Hora</span>'
            '<span class="val">' + ultima_op.get("hora","-") + '</span></div>'
            '<div class="metric"><span class="lbl">Senal</span>'
            '<span class="val">' + ultima_op.get("senal","-") + '</span></div>'
            '<div class="metric"><span class="lbl">Resultado</span>'
            '<span class="val" style="color:' + uo_color + '">' + uo_res + '</span></div>'
            '<div class="metric"><span class="lbl">P&L</span>'
            '<span class="val" style="color:' + col_p(uo_pl) + ';font-weight:bold">' + fmt_p(uo_pl) + '</span></div>'
            '<div class="metric"><span class="lbl">Balance</span>'
            '<span class="val">{:.2f}</span></div>'.format(numero(ultima_op.get("balance",0)))
            + ctx_html
            + '</div></div>'
        )

    # ── V5 estado ─────────────────────────────────────────────────────────────
    if FILTRO_V5_ACTIVO is None:
        v5_estado_html = '<span style="color:#9CA3AF">No disponible</span>'
    elif FILTRO_V5_ACTIVO:
        v5_estado_html = '<span style="color:#22C55E;font-weight:bold">ACTIVO</span>'
    else:
        v5_estado_html = '<span style="color:#9CA3AF">Inactivo</span>'

    horas_v5_str = ", ".join(sorted(HORAS_V5_BLOQUEADAS)) if HORAS_V5_BLOQUEADAS else "No disponible"

    def delta_color(v): return "#22C55E" if v > 0 else ("#EF4444" if v < 0 else "#9CA3AF")
    def sfmt(v, decimals=2): return ("+{:.{}f}".format(v,decimals) if v>0 else "{:.{}f}".format(v,decimals))

    dwr  = m_v5["wr"]  - m_actual["wr"]
    dpl  = m_v5["profit"] - m_actual["profit"]
    dexp = m_v5["exp"] - m_actual["exp"]
    ddd  = m_actual["dd_max"] - m_v5["dd_max"]  # positive = drawdown reduced

    html_v5 = (
        '<div class="card"><h2>Filtro V5 — Estado y Simulacion</h2>'
        '<div class="grid g3" style="margin-bottom:14px">'
        '<div class="metric"><span class="lbl">Estado</span>'
        '<span class="val">' + v5_estado_html + '</span></div>'
        '<div class="metric"><span class="lbl">Horas Bloqueadas</span>'
        '<span class="val small">' + horas_v5_str + '</span></div>'
        '<div class="metric"><span class="lbl">Ops que bloquea</span>'
        '<span class="val">' + str(ops_bloqueadas) + ' / ' + str(m_actual["total"]) + '</span></div>'
        '</div>'
        '<table><tr><th>Metrica</th><th>Actual</th><th>Con V5 activo</th><th>Delta</th></tr>'
        '<tr><td>Win Rate</td><td>{:.2f}%</td><td>{:.2f}%</td>'
        '<td style="color:{}">{}</td></tr>'
        '<tr><td>Profit</td><td>{}</td><td>{}</td>'
        '<td style="color:{}">{}</td></tr>'
        '<tr><td>Expect/Op</td><td>{:.4f}</td><td>{:.4f}</td>'
        '<td style="color:{}">{}</td></tr>'
        '<tr><td>Drawdown Max</td><td>{:.2f}</td><td>{:.2f}</td>'
        '<td style="color:{}">{}</td></tr>'
        '</table></div>'
    ).format(
        m_actual["wr"], m_v5["wr"], delta_color(dwr), sfmt(dwr),
        fmt_p(m_actual["profit"]), fmt_p(m_v5["profit"]), delta_color(dpl), sfmt(dpl),
        m_actual["exp"], m_v5["exp"], delta_color(dexp), sfmt(dexp,4),
        m_actual["dd_max"], m_v5["dd_max"], delta_color(ddd), sfmt(ddd),
    )

    # ── promedio diario html ──────────────────────────────────────────────────
    if promedio_info:
        html_promedio = (
            '<div class="card"><h2>Promedio de Operaciones por Dia</h2>'
            '<div class="grid g3">'
            '<div class="metric"><span class="lbl">Promedio diario</span>'
            '<span class="val">{:.1f}</span></div>'
            '<div class="metric"><span class="lbl">Dias registrados</span>'
            '<span class="val">{}</span></div>'
            '<div class="metric"><span class="lbl">Total ops</span>'
            '<span class="val">{}</span></div>'
            '</div></div>'
        ).format(promedio_info["promedio"], promedio_info["dias"], promedio_info["total"])
    else:
        html_promedio = (
            '<div class="card"><h2>Promedio de Operaciones por Dia</h2>'
            '<p class="aviso">No disponible — CSV sin fecha</p></div>'
        )

    # ── alertas html ──────────────────────────────────────────────────────────
    if alertas:
        items = "".join('<li style="color:#EF4444">' + a + '</li>' for a in alertas)
        html_alertas = (
            '<div class="card" style="border:1px solid #EF4444">'
            '<h2 style="color:#EF4444">Alertas</h2>'
            '<ul style="padding-left:16px;font-size:.9rem">' + items + '</ul></div>'
        )
    else:
        html_alertas = ""

    j_h  = json.dumps(horas)
    j_b  = json.dumps(balances)
    j_p  = json.dumps(profits)
    j_dd = json.dumps(dds)

    # ── selector de modo (DEMO real / PAPER sim) ──────────────────────────────
    botones = ""
    for k, c in MODOS.items():
        activo = (k == modo)
        estilo = ("background:{};color:#0f172a;font-weight:bold".format(c["color"])
                  if activo else "background:#1e293b;color:#94a3b8")
        botones += (
            '<a href="/?modo={}" class="badge" style="{};text-decoration:none">{}</a>'
        ).format(k, estilo, c["etiqueta"])
    html_modo = (
        '<div class="badge" style="color:{}">MODO: {}</div>{}'
    ).format(cfg_modo["color"], cfg_modo["etiqueta"], botones)

    return HTML_TEMPLATE.format(
        html_modo=html_modo,
        color_estado=color_estado, estado=estado, tiempo_estado=tiempo_estado,
        nombre_activo=nombre_activo, simbolo=simbolo,
        total=m["total"], wr=m["wr"],
        pt=fmt_p(m["profit_total"]),  cpt=col_p(m["profit_total"]),
        ddm=m["drawdown_max"],
        gan=m["ganadas"], per=m["perdidas"], bal=m["balance_actual"],
        ps2=fmt_p(m["ps2"]), cs2=col_p(m["ps2"]),
        ps3=fmt_p(m["ps3"]), cs3=col_p(m["ps3"]),
        html_top=html_top,
        html_re=html_re, html_rb=html_rb,
        html_rc=html_rc, html_rx=html_rx,
        html_us=html_us, html_uo=html_uo,
        html_v5=html_v5, html_promedio=html_promedio,
        html_alertas=html_alertas,
        filas_t=filas_t,
        j_h=j_h, j_b=j_b, j_p=j_p, j_dd=j_dd,
    )

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="10">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Bot Deriv IA -- Dashboard V3</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:Arial,sans-serif;background:#0f172a;color:#f1f5f9;padding:20px}}
    header{{display:flex;align-items:center;justify-content:space-between;
            flex-wrap:wrap;gap:10px;margin-bottom:18px}}
    header h1{{font-size:1.4rem;font-weight:bold}}
    .badges{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
    .badge{{padding:6px 14px;border-radius:999px;font-size:.82rem;font-weight:bold;
            background:#1e293b;border:1px solid #334155}}
    .card{{background:#1e293b;padding:18px;border-radius:14px;margin-bottom:16px}}
    .card h2{{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;
              color:#64748b;margin-bottom:12px}}
    .grid{{display:grid;gap:10px}}
    .g4{{grid-template-columns:repeat(4,1fr)}}
    .g3{{grid-template-columns:repeat(3,1fr)}}
    .g2{{grid-template-columns:repeat(2,1fr)}}
    .metric{{background:#0f172a;border:1px solid #1e293b;border-radius:10px;
             padding:12px;display:flex;flex-direction:column;gap:4px}}
    .lbl{{font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;color:#64748b}}
    .val{{font-size:1.25rem;font-weight:bold;color:#f1f5f9}}
    .val.small{{font-size:.8rem;font-weight:normal;word-break:break-word}}
    .chart-wrap{{position:relative;height:180px}}
    .charts-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}}
    table{{width:100%;border-collapse:collapse;font-size:.85rem}}
    th,td{{padding:8px 10px;text-align:center;border-bottom:1px solid #1e293b}}
    th{{background:#0f172a;color:#64748b;font-size:.72rem;text-transform:uppercase}}
    tr:hover td{{background:#162032}}
    tr.sin-dato{{opacity:.45}}
    tr.sin-dato.oculto{{display:none}}
    .aviso{{color:#64748b;font-size:.85rem;padding:8px 0}}
    .filtro-bar{{display:flex;align-items:center;gap:10px;
                 background:#1e293b;padding:12px 18px;border-radius:10px;margin-bottom:14px}}
    .filtro-bar label{{font-size:.85rem;color:#94a3b8;cursor:pointer;
                       display:flex;align-items:center;gap:6px}}
    .note{{text-align:center;color:#334155;font-size:.72rem;margin-top:8px}}
    @media(max-width:800px){{
      .g4,.g3{{grid-template-columns:repeat(2,1fr)}}
      .charts-grid{{grid-template-columns:1fr}}
    }}
    @media(max-width:480px){{
      .g4,.g3,.g2{{grid-template-columns:1fr}}
    }}
  </style>
</head>
<body>

<header>
  <h1>Bot Deriv IA -- Dashboard V3</h1>
  <div class="badges">
    {html_modo}
    <div class="badge" style="color:{color_estado}">{estado} &bull; {tiempo_estado}</div>
    <div class="badge" style="color:#60a5fa">{nombre_activo} ({simbolo})</div>
  </div>
</header>

{html_alertas}

<div class="card">
  <h2>Resumen General</h2>
  <div class="grid g4">
    <div class="metric"><span class="lbl">Operaciones</span><span class="val">{total}</span></div>
    <div class="metric"><span class="lbl">Win Rate</span><span class="val">{wr:.1f}%</span></div>
    <div class="metric"><span class="lbl">Profit Total</span>
      <span class="val" style="color:{cpt}">{pt}</span></div>
    <div class="metric"><span class="lbl">Drawdown Max</span>
      <span class="val" style="color:#EF4444">{ddm:.2f}</span></div>
  </div>
</div>

<div class="card">
  <h2>Resultados</h2>
  <div class="grid g3">
    <div class="metric"><span class="lbl">Ganadas</span>
      <span class="val" style="color:#22C55E">{gan}</span></div>
    <div class="metric"><span class="lbl">Perdidas</span>
      <span class="val" style="color:#EF4444">{per}</span></div>
    <div class="metric"><span class="lbl">Balance Actual</span>
      <span class="val">{bal:.2f}</span></div>
  </div>
</div>

<div class="card">
  <h2>Profit por Score de Senal</h2>
  <div class="grid g2">
    <div class="metric"><span class="lbl">Profit Score 2</span>
      <span class="val" style="color:{cs2}">{ps2}</span></div>
    <div class="metric"><span class="lbl">Profit Score 3+</span>
      <span class="val" style="color:{cs3}">{ps3}</span></div>
  </div>
</div>

<div class="charts-grid">
  <div class="card">
    <h2>Curva de Equity (Balance)</h2>
    <div class="chart-wrap"><canvas id="cEq"></canvas></div>
  </div>
  <div class="card">
    <h2>Profit Acumulado</h2>
    <div class="chart-wrap"><canvas id="cPr"></canvas></div>
  </div>
</div>

<div class="card" style="margin-bottom:16px">
  <h2>Drawdown</h2>
  <div class="chart-wrap"><canvas id="cDD"></canvas></div>
</div>

{html_top}

<div class="filtro-bar">
  <label>
    <input type="checkbox" id="chkSD" onchange="filtrar(this.checked)">
    Ocultar filas "Sin dato" en rankings
  </label>
</div>

<div class="grid g2">
  {html_re}
  {html_rb}
</div>
<div class="grid g2" style="margin-top:0">
  {html_rc}
  {html_rx}
</div>

{html_v5}

{html_promedio}

{html_us}
{html_uo}

<div class="card">
  <h2>Ultimas 10 Operaciones</h2>
  <table>
    <tr><th>Hora</th><th>Senal</th><th>Resultado</th>
        <th>P&L</th><th>Balance</th><th>Score</th><th>Patron</th></tr>
    {filas_t}
  </table>
</div>

<p class="note">Auto-refresco cada 10 segundos -- Dashboard V3</p>

<script>
const H   = {j_h};
const BAL = {j_b};
const PRF = {j_p};
const DDS = {j_dd};

function mkChart(id, data, color, fill) {{
  new Chart(document.getElementById(id), {{
    type: "line",
    data: {{
      labels: H,
      datasets: [{{
        data, borderColor: color,
        backgroundColor: fill || "transparent",
        borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: !!fill
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ display: false }},
        y: {{ ticks: {{ color:"#94a3b8", font:{{size:10}} }},
              grid:  {{ color:"#1e293b" }} }}
      }}
    }}
  }});
}}

mkChart("cEq", BAL, "#60a5fa", null);
mkChart("cPr", PRF, "#22C55E", "rgba(34,197,94,.15)");
mkChart("cDD", DDS, "#EF4444", "rgba(239,68,68,.15)");

function filtrar(hide) {{
  document.querySelectorAll("tr.sin-dato").forEach(tr =>
    tr.classList.toggle("oculto", hide));
}}
</script>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
