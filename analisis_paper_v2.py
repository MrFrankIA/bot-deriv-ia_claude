
import csv
import os
from collections import defaultdict

ARCHIVO_OPERACIONES = "operaciones_paper.csv"
ARCHIVO_RESUMEN = "resumen_paper_trading.csv"
ARCHIVO_RACHAS = "rachas_paper_trading.csv"

BALANCE_INICIAL = 1000

def leer_operaciones():
    if not os.path.exists(ARCHIVO_OPERACIONES):
        print(f"❌ No existe {ARCHIVO_OPERACIONES}")
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

def calcular_rachas(operaciones):
    mejor_racha = 0
    peor_racha = 0

    racha_ganadas = 0
    racha_perdidas = 0

    for operacion in operaciones:
        resultado = operacion.get("resultado", "")

        if resultado == "CORRECTA":
            racha_ganadas += 1
            racha_perdidas = 0
            mejor_racha = max(mejor_racha, racha_ganadas)
        else:
            racha_perdidas += 1
            racha_ganadas = 0
            peor_racha = max(peor_racha, racha_perdidas)

    return mejor_racha, peor_racha

def main():
    operaciones = leer_operaciones()

    if not operaciones:
        print("No hay operaciones paper para analizar.")
        return

    total = len(operaciones)
    ganadas = 0
    perdidas = 0
    profit_total = 0
    peor_drawdown = 0

    profits = []
    losses = []

    estadisticas_score = defaultdict(
        lambda: {
            "total": 0,
            "ganadas": 0,
            "perdidas": 0,
            "profit": 0
        }
    )

    for operacion in operaciones:

        resultado = operacion.get("resultado", "")
        score = str(operacion.get("score_senal", "SIN_SCORE"))

        profit_loss = numero(
            operacion.get("profit_loss", 0)
        )

        drawdown = numero(
            operacion.get("drawdown", 0)
        )

        profit_total += profit_loss

        estadisticas_score[score]["total"] += 1
        estadisticas_score[score]["profit"] += profit_loss

        if resultado == "CORRECTA":
            ganadas += 1
            profits.append(profit_loss)
            estadisticas_score[score]["ganadas"] += 1
        else:
            perdidas += 1
            losses.append(profit_loss)
            estadisticas_score[score]["perdidas"] += 1

        peor_drawdown = max(peor_drawdown, drawdown)

    balance_final = numero(
        operaciones[-1].get("balance", BALANCE_INICIAL)
    )

    win_rate = (ganadas / total) * 100 if total > 0 else 0

    profit_promedio = (
        sum(profits) / len(profits)
        if profits else 0
    )

    perdida_promedio = (
        sum(losses) / len(losses)
        if losses else 0
    )

    mejor_racha, peor_racha = calcular_rachas(
        operaciones
    )

    print("\n💼 ANALISIS PAPER TRADING")
    print(f"📌 Total operaciones: {total}")
    print(f"✅ Ganadas: {ganadas}")
    print(f"❌ Perdidas: {perdidas}")
    print(f"🎯 Win Rate: {win_rate:.2f}%")
    print(f"💰 Balance inicial: {BALANCE_INICIAL}")
    print(f"💵 Balance final: {balance_final}")
    print(f"📈 Profit total: {profit_total:.2f}")
    print(f"📉 Drawdown máximo: {peor_drawdown:.2f}")
    print(f"🔥 Mejor racha: {mejor_racha}")
    print(f"🥶 Peor racha: {peor_racha}")
    print(f"📊 Profit promedio: {profit_promedio:.2f}")
    print(f"📊 Perdida promedio: {perdida_promedio:.2f}")

    print("\n📊 ANALISIS POR SCORE")

    mejor_score = None
    mejor_profit = -999999

    for score in sorted(
        estadisticas_score.keys(),
        key=lambda x: int(x) if str(x).isdigit() else 999
    ):
        datos = estadisticas_score[score]

        wr = (
            datos["ganadas"] / datos["total"]
        ) * 100

        profit = datos["profit"]

        print(f"\n🎯 SCORE {score}")
        print(f"Operaciones: {datos['total']}")
        print(f"Win Rate: {wr:.2f}%")
        print(f"Profit: {profit:.2f}")

        if profit > mejor_profit:
            mejor_profit = profit
            mejor_score = score

    print("\n🏆 MEJOR SCORE")
    print(f"Score: {mejor_score}")
    print(f"Profit: {mejor_profit:.2f}")

if __name__ == "__main__":
    main()
