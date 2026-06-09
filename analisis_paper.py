
import csv
import os

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

            if racha_ganadas > mejor_racha:
                mejor_racha = racha_ganadas

        else:
            racha_perdidas += 1
            racha_ganadas = 0

            if racha_perdidas > peor_racha:
                peor_racha = racha_perdidas

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

    for operacion in operaciones:
        resultado = operacion.get("resultado", "")

        profit_loss = numero(
            operacion.get("profit_loss", 0)
        )

        balance = numero(
            operacion.get("balance", BALANCE_INICIAL)
        )

        drawdown = numero(
            operacion.get("drawdown", 0)
        )

        profit_total += profit_loss

        if resultado == "CORRECTA":
            ganadas += 1
            profits.append(profit_loss)

        else:
            perdidas += 1
            losses.append(profit_loss)

        if drawdown > peor_drawdown:
            peor_drawdown = drawdown

    balance_final = numero(
        operaciones[-1].get("balance", BALANCE_INICIAL)
    )

    if total > 0:
        win_rate = (ganadas / total) * 100
    else:
        win_rate = 0

    if profits:
        profit_promedio = sum(profits) / len(profits)
    else:
        profit_promedio = 0

    if losses:
        perdida_promedio = sum(losses) / len(losses)
    else:
        perdida_promedio = 0

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

    with open(
        ARCHIVO_RESUMEN,
        mode="w",
        newline="",
        encoding="utf-8"
    ) as archivo:
        writer = csv.writer(archivo)

        writer.writerow([
            "total_operaciones",
            "ganadas",
            "perdidas",
            "win_rate",
            "balance_inicial",
            "balance_final",
            "profit_total",
            "drawdown_maximo",
            "mejor_racha",
            "peor_racha",
            "profit_promedio",
            "perdida_promedio"
        ])

        writer.writerow([
            total,
            ganadas,
            perdidas,
            round(win_rate, 2),
            BALANCE_INICIAL,
            round(balance_final, 2),
            round(profit_total, 2),
            round(peor_drawdown, 2),
            mejor_racha,
            peor_racha,
            round(profit_promedio, 2),
            round(perdida_promedio, 2)
        ])

    with open(
        ARCHIVO_RACHAS,
        mode="w",
        newline="",
        encoding="utf-8"
    ) as archivo:
        writer = csv.writer(archivo)

        writer.writerow([
            "mejor_racha",
            "peor_racha"
        ])

        writer.writerow([
            mejor_racha,
            peor_racha
        ])

    print("\n💾 Reportes generados:")
    print(f"- {ARCHIVO_RESUMEN}")
    print(f"- {ARCHIVO_RACHAS}")


if __name__ == "__main__":
    main()
