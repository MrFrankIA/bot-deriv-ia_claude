from flask import Flask
import csv
import os

app = Flask(__name__)

ARCHIVO_OPERACIONES = "operaciones_paper.csv"


def leer_operaciones():
    if not os.path.exists(ARCHIVO_OPERACIONES):
        return []

    with open(
        ARCHIVO_OPERACIONES,
        mode="r",
        newline="",
        encoding="utf-8"
    ) as archivo:
        return list(csv.DictReader(archivo))


def numero(valor, defecto=0):
    try:
        return float(valor)
    except:
        return defecto


@app.route("/")
def inicio():
    operaciones = leer_operaciones()

    total = len(operaciones)
    ganadas = 0
    perdidas = 0
    profit_total = 0
    drawdown_maximo = 0

    for operacion in operaciones:
        resultado = operacion.get("resultado", "")
        profit_loss = numero(operacion.get("profit_loss", 0))
        drawdown = numero(operacion.get("drawdown", 0))

        profit_total += profit_loss

        if resultado == "CORRECTA":
            ganadas += 1
        else:
            perdidas += 1

        if drawdown > drawdown_maximo:
            drawdown_maximo = drawdown

    win_rate = (ganadas / total) * 100 if total > 0 else 0

    ultimas = operaciones[-10:]

    filas = ""

    for op in reversed(ultimas):
        filas += f"""
        <tr>
            <td>{op.get('hora', '')}</td>
            <td>{op.get('senal', '')}</td>
            <td>{op.get('resultado', '')}</td>
            <td>{op.get('profit_loss', '')}</td>
            <td>{op.get('score_senal', '')}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bot Deriv IA</title>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="10">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #111827;
                color: #f9fafb;
                margin: 30px;
            }}
            .card {{
                background: #1f2937;
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 20px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 15px;
            }}
            .metric {{
                background: #374151;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}
            th, td {{
                border-bottom: 1px solid #4b5563;
                padding: 10px;
                text-align: center;
            }}
            th {{
                background: #374151;
            }}
        </style>
    </head>
    <body>
        <h1>🤖 Bot Deriv IA - Dashboard</h1>

        <div class="card">
            <h2>Resumen Paper Trading</h2>
            <div class="grid">
                <div class="metric">
                    <h3>Operaciones</h3>
                    <p>{total}</p>
                </div>
                <div class="metric">
                    <h3>Win Rate</h3>
                    <p>{win_rate:.2f}%</p>
                </div>
                <div class="metric">
                    <h3>Profit</h3>
                    <p>{profit_total:.2f}</p>
                </div>
                <div class="metric">
                    <h3>Drawdown Máx</h3>
                    <p>{drawdown_maximo:.2f}</p>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Últimas operaciones</h2>
            <table>
                <tr>
                    <th>Hora</th>
                    <th>Señal</th>
                    <th>Resultado</th>
                    <th>Profit</th>
                    <th>Score</th>
                </tr>
                {filas}
            </table>
        </div>
    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
