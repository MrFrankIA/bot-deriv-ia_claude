from flask import Flask
import csv
import os
import time

app = Flask(__name__)

ARCHIVO_OPERACIONES = "operaciones_paper.csv"
ARCHIVO_SENALES     = "senales.csv"

BOT_ACTIVO_SEGUNDOS   = 120
BOT_SIN_SENAL_SEGUNDOS = 600


# ─── Lectura de datos ────────────────────────────────────────────────────────

def leer_operaciones():
    if not os.path.exists(ARCHIVO_OPERACIONES):
        return []
    with open(ARCHIVO_OPERACIONES, mode="r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def leer_senales():
    if not os.path.exists(ARCHIVO_SENALES):
        return []
    with open(ARCHIVO_SENALES, mode="r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def numero(valor, defecto=0.0):
    try:
        return float(valor)
    except Exception:
        return defecto


# ─── Estado del bot ──────────────────────────────────────────────────────────

def estado_bot():
    if not os.path.exists(ARCHIVO_SENALES):
        return "DETENIDO", "🔴", "#EF4444", "Archivo de señales no encontrado"

    ultima_mod = os.path.getmtime(ARCHIVO_SENALES)
    segundos   = time.time() - ultima_mod
    minutos    = int(segundos // 60)
    segs       = int(segundos % 60)

    if segundos < BOT_ACTIVO_SEGUNDOS:
        texto_tiempo = f"hace {int(segundos)}s"
        return "ACTIVO", "🟢", "#22C55E", texto_tiempo
    elif segundos < BOT_SIN_SENAL_SEGUNDOS:
        texto_tiempo = f"hace {minutos}m {segs}s"
        return "SIN SEÑALES", "🟡", "#EAB308", texto_tiempo
    else:
        texto_tiempo = f"hace {minutos}m {segs}s"
        return "DETENIDO", "🔴", "#EF4444", texto_tiempo


# ─── Ruta principal ──────────────────────────────────────────────────────────

@app.route("/")
def inicio():
    operaciones = leer_operaciones()
    senales     = leer_senales()

    # ── Métricas principales ─────────────────────────────────────────────────
    total         = len(operaciones)
    ganadas       = 0
    perdidas      = 0
    profit_total  = 0.0
    drawdown_max  = 0.0
    balance_actual = 0.0
    profit_score2 = 0.0
    profit_score3 = 0.0

    for op in operaciones:
        resultado  = op.get("resultado", "")
        pl         = numero(op.get("profit_loss", 0))
        drawdown   = numero(op.get("drawdown", 0))
        score      = numero(op.get("score_senal", 0))
        balance_actual = numero(op.get("balance", 0))

        profit_total += pl

        if resultado == "CORRECTA":
            ganadas += 1
        else:
            perdidas += 1

        if drawdown > drawdown_max:
            drawdown_max = drawdown

        if score == 2:
            profit_score2 += pl
        elif score >= 3:
            profit_score3 += pl

    win_rate = (ganadas / total * 100) if total > 0 else 0.0

    # ── Última operación ─────────────────────────────────────────────────────
    ultima_op = operaciones[-1] if operaciones else None

    # ── Última señal ─────────────────────────────────────────────────────────
    ultima_senal = senales[-1] if senales else None

    # ── Estado del bot ───────────────────────────────────────────────────────
    estado, emoji_estado, color_estado, tiempo_estado = estado_bot()

    # ── Últimas 10 operaciones (tabla) ────────────────────────────────────────
    ultimas = operaciones[-10:]
    filas_html = ""
    for op in reversed(ultimas):
        res = op.get("resultado", "")
        color_res = "#22C55E" if res == "CORRECTA" else "#EF4444"
        pl_val = numero(op.get("profit_loss", 0))
        pl_str = f"+{pl_val:.2f}" if pl_val >= 0 else f"{pl_val:.2f}"
        pl_color = "#22C55E" if pl_val >= 0 else "#EF4444"
        filas_html += f"""
        <tr>
            <td>{op.get('hora', '')}</td>
            <td>{op.get('senal', '')}</td>
            <td style="color:{color_res};font-weight:bold">{res}</td>
            <td style="color:{pl_color};font-weight:bold">{pl_str}</td>
            <td>{numero(op.get('balance', 0)):.2f}</td>
            <td>{op.get('score_senal', '')}</td>
            <td>{op.get('patron', '')}</td>
        </tr>"""

    # ── Última operación: bloque HTML ────────────────────────────────────────
    if ultima_op:
        uo_res   = ultima_op.get("resultado", "-")
        uo_color = "#22C55E" if uo_res == "CORRECTA" else "#EF4444"
        uo_pl    = numero(ultima_op.get("profit_loss", 0))
        uo_pl_str   = f"+{uo_pl:.2f}" if uo_pl >= 0 else f"{uo_pl:.2f}"
        uo_pl_color = "#22C55E" if uo_pl >= 0 else "#EF4444"
        html_ultima_op = f"""
        <div class="card">
            <h2>Última Operación</h2>
            <div class="grid grid3">
                <div class="metric">
                    <span class="label">Hora</span>
                    <span class="value">{ultima_op.get('hora', '-')}</span>
                </div>
                <div class="metric">
                    <span class="label">Señal</span>
                    <span class="value">{ultima_op.get('senal', '-')}</span>
                </div>
                <div class="metric">
                    <span class="label">Resultado</span>
                    <span class="value" style="color:{uo_color}">{uo_res}</span>
                </div>
                <div class="metric">
                    <span class="label">P&amp;L</span>
                    <span class="value" style="color:{uo_pl_color}">{uo_pl_str}</span>
                </div>
                <div class="metric">
                    <span class="label">Balance</span>
                    <span class="value">{numero(ultima_op.get('balance', 0)):.2f}</span>
                </div>
                <div class="metric">
                    <span class="label">Score</span>
                    <span class="value">{ultima_op.get('score_senal', '-')}</span>
                </div>
            </div>
        </div>"""
    else:
        html_ultima_op = ""

    # ── Última señal: bloque HTML ────────────────────────────────────────────
    if ultima_senal:
        us_tecnica  = ultima_senal.get("senal_tecnica", "-")
        us_permitida = ultima_senal.get("permitida", "-")
        us_motivo   = ultima_senal.get("motivo_bloqueo", "") or "—"
        us_color_senal = "#22C55E" if us_tecnica == "COMPRAR" else (
                         "#EF4444" if us_tecnica == "VENDER" else "#9CA3AF")
        html_ultima_senal = f"""
        <div class="card">
            <h2>Última Señal Generada</h2>
            <div class="grid grid3">
                <div class="metric">
                    <span class="label">Hora</span>
                    <span class="value">{ultima_senal.get('hora', '-')}</span>
                </div>
                <div class="metric">
                    <span class="label">Señal</span>
                    <span class="value" style="color:{us_color_senal}">{us_tecnica}</span>
                </div>
                <div class="metric">
                    <span class="label">Score</span>
                    <span class="value">{ultima_senal.get('score_senal', '-')}</span>
                </div>
                <div class="metric">
                    <span class="label">Patrón</span>
                    <span class="value">{ultima_senal.get('patron_actual', '-')}</span>
                </div>
                <div class="metric">
                    <span class="label">Permitida</span>
                    <span class="value">{us_permitida}</span>
                </div>
                <div class="metric">
                    <span class="label">Motivo bloqueo</span>
                    <span class="value small">{us_motivo}</span>
                </div>
            </div>
        </div>"""
    else:
        html_ultima_senal = ""

    # ── Color profit helpers ─────────────────────────────────────────────────
    def color_profit(val):
        return "#22C55E" if val >= 0 else "#EF4444"

    def fmt_profit(val):
        return f"+{val:.2f}" if val >= 0 else f"{val:.2f}"

    # ── HTML final ───────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="10">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Bot Deriv IA — Dashboard V2</title>
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #f1f5f9;
            padding: 24px;
        }}

        header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }}

        header h1 {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #f1f5f9;
        }}

        .estado-badge {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: #1e293b;
            padding: 8px 18px;
            border-radius: 999px;
            font-size: 0.9rem;
            font-weight: bold;
            border: 1px solid #334155;
        }}

        .estado-dot {{
            font-size: 1.1rem;
        }}

        .estado-tiempo {{
            font-size: 0.78rem;
            color: #94a3b8;
            margin-left: 4px;
        }}

        .card {{
            background: #1e293b;
            padding: 20px;
            border-radius: 14px;
            margin-bottom: 18px;
        }}

        .card h2 {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            margin-bottom: 14px;
        }}

        .grid {{
            display: grid;
            gap: 12px;
        }}

        .grid4  {{ grid-template-columns: repeat(4, 1fr); }}
        .grid3  {{ grid-template-columns: repeat(3, 1fr); }}
        .grid2  {{ grid-template-columns: repeat(2, 1fr); }}

        .metric {{
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 10px;
            padding: 14px 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .metric .label {{
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #64748b;
        }}

        .metric .value {{
            font-size: 1.35rem;
            font-weight: bold;
            color: #f1f5f9;
        }}

        .metric .value.small {{
            font-size: 0.82rem;
            font-weight: normal;
            word-break: break-word;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
        }}

        th, td {{
            padding: 10px 12px;
            text-align: center;
            border-bottom: 1px solid #1e293b;
        }}

        th {{
            background: #0f172a;
            color: #64748b;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}

        tr:hover td {{
            background: #162032;
        }}

        .refresh-note {{
            text-align: center;
            color: #334155;
            font-size: 0.75rem;
            margin-top: 10px;
        }}

        @media (max-width: 800px) {{
            .grid4 {{ grid-template-columns: repeat(2, 1fr); }}
            .grid3 {{ grid-template-columns: repeat(2, 1fr); }}
        }}

        @media (max-width: 500px) {{
            .grid4, .grid3, .grid2 {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>

<header>
    <h1>🤖 Bot Deriv IA &mdash; Dashboard V2</h1>
    <div class="estado-badge">
        <span class="estado-dot">{emoji_estado}</span>
        <span style="color:{color_estado}">{estado}</span>
        <span class="estado-tiempo">{tiempo_estado}</span>
    </div>
</header>

<!-- Métricas principales -->
<div class="card">
    <h2>Resumen General</h2>
    <div class="grid grid4">
        <div class="metric">
            <span class="label">Operaciones</span>
            <span class="value">{total}</span>
        </div>
        <div class="metric">
            <span class="label">Win Rate</span>
            <span class="value">{win_rate:.1f}%</span>
        </div>
        <div class="metric">
            <span class="label">Profit Total</span>
            <span class="value" style="color:{color_profit(profit_total)}">{fmt_profit(profit_total)}</span>
        </div>
        <div class="metric">
            <span class="label">Drawdown Máx.</span>
            <span class="value" style="color:#EF4444">{drawdown_max:.2f}</span>
        </div>
    </div>
</div>

<!-- Desglose de resultados -->
<div class="card">
    <h2>Resultados</h2>
    <div class="grid grid3">
        <div class="metric">
            <span class="label">Ganadas</span>
            <span class="value" style="color:#22C55E">{ganadas}</span>
        </div>
        <div class="metric">
            <span class="label">Perdidas</span>
            <span class="value" style="color:#EF4444">{perdidas}</span>
        </div>
        <div class="metric">
            <span class="label">Balance Actual</span>
            <span class="value">{balance_actual:.2f}</span>
        </div>
    </div>
</div>

<!-- Profit por Score -->
<div class="card">
    <h2>Profit por Score de Señal</h2>
    <div class="grid grid2">
        <div class="metric">
            <span class="label">Profit Score 2</span>
            <span class="value" style="color:{color_profit(profit_score2)}">{fmt_profit(profit_score2)}</span>
        </div>
        <div class="metric">
            <span class="label">Profit Score 3+</span>
            <span class="value" style="color:{color_profit(profit_score3)}">{fmt_profit(profit_score3)}</span>
        </div>
    </div>
</div>

<!-- Última señal -->
{html_ultima_senal}

<!-- Última operación -->
{html_ultima_op}

<!-- Tabla de últimas 10 operaciones -->
<div class="card">
    <h2>Últimas 10 Operaciones</h2>
    <table>
        <tr>
            <th>Hora</th>
            <th>Señal</th>
            <th>Resultado</th>
            <th>P&amp;L</th>
            <th>Balance</th>
            <th>Score</th>
            <th>Patrón</th>
        </tr>
        {filas_html}
    </table>
</div>

<p class="refresh-note">Auto-refresco cada 10 segundos</p>

</body>
</html>"""

    return html


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
