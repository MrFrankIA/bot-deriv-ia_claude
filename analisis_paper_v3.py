import csv
import os
from collections import defaultdict

ARCHIVO_OPERACIONES = "operaciones_paper.csv"
BALANCE_INICIAL = 1000


def leer_operaciones():
    if not os.path.exists(ARCHIVO_OPERACIONES):
        print(f"❌ No existe {ARCHIVO_OPERACIONES}")
        return []

    with open(ARCHIVO_OPERACIONES, mode="r", newline="", encoding="utf-8") as archivo:
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


def crear_grupo():
    return {"total": 0, "ganadas": 0, "perdidas": 0, "profit": 0}


def actualizar_grupo(grupo, resultado, profit_loss):
    grupo["total"] += 1
    grupo["profit"] += profit_loss

    if resultado == "CORRECTA":
        grupo["ganadas"] += 1
    else:
        grupo["perdidas"] += 1


def imprimir_grupos(titulo, grupos):
    print(f"\n{titulo}")

    if not grupos:
        print("Sin datos.")
        return

    datos = sorted(
        grupos.items(),
        key=lambda item: item[1]["total"],
        reverse=True
    )

    for nombre, grupo in datos:
        total = grupo["total"]
        wr = (grupo["ganadas"] / total) * 100 if total else 0

        print(f"\n📌 {nombre}")
        print(f"Operaciones: {total}")
        print(f"Ganadas: {grupo['ganadas']}")
        print(f"Perdidas: {grupo['perdidas']}")
        print(f"Win Rate: {wr:.2f}%")
        print(f"Profit: {grupo['profit']:.2f}")


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

    por_score = defaultdict(crear_grupo)
    por_estructura = defaultdict(crear_grupo)
    por_bos = defaultdict(crear_grupo)
    por_choch = defaultdict(crear_grupo)
    por_sweep = defaultdict(crear_grupo)
    por_contexto = defaultdict(crear_grupo)
    por_score_bos = defaultdict(crear_grupo)
    por_score_contexto = defaultdict(crear_grupo)

    for operacion in operaciones:
        resultado = operacion.get("resultado", "")
        profit_loss = numero(operacion.get("profit_loss", 0))
        drawdown = numero(operacion.get("drawdown", 0))

        score = operacion.get("score_senal", "SIN_SCORE") or "SIN_SCORE"
        estructura = operacion.get("estructura", "SIN_DATO") or "SIN_DATO"
        bos = operacion.get("bos", "SIN_DATO") or "SIN_DATO"
        choch = operacion.get("choch", "SIN_DATO") or "SIN_DATO"
        sweep = operacion.get("sweep", "SIN_DATO") or "SIN_DATO"
        contexto = operacion.get("contexto_valido", "SIN_DATO") or "SIN_DATO"

        profit_total += profit_loss
        peor_drawdown = max(peor_drawdown, drawdown)

        if resultado == "CORRECTA":
            ganadas += 1
            profits.append(profit_loss)
        else:
            perdidas += 1
            losses.append(profit_loss)

        actualizar_grupo(por_score[score], resultado, profit_loss)
        actualizar_grupo(por_estructura[estructura], resultado, profit_loss)
        actualizar_grupo(por_bos[bos], resultado, profit_loss)
        actualizar_grupo(por_choch[choch], resultado, profit_loss)
        actualizar_grupo(por_sweep[sweep], resultado, profit_loss)
        actualizar_grupo(por_contexto[contexto], resultado, profit_loss)
        actualizar_grupo(por_score_bos[f"Score {score} | {bos}"], resultado, profit_loss)
        actualizar_grupo(por_score_contexto[f"Score {score} | Contexto {contexto}"], resultado, profit_loss)

    balance_final = numero(operaciones[-1].get("balance", BALANCE_INICIAL))
    win_rate = (ganadas / total) * 100 if total else 0
    profit_promedio = sum(profits) / len(profits) if profits else 0
    perdida_promedio = sum(losses) / len(losses) if losses else 0
    mejor_racha, peor_racha = calcular_rachas(operaciones)

    print("\n💼 ANALISIS PAPER TRADING v3")
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

    imprimir_grupos("📊 ANALISIS POR SCORE", por_score)
    imprimir_grupos("🏗️ ANALISIS POR ESTRUCTURA", por_estructura)
    imprimir_grupos("🧱 ANALISIS POR BOS", por_bos)
    imprimir_grupos("🔄 ANALISIS POR CHOCH", por_choch)
    imprimir_grupos("💧 ANALISIS POR SWEEP", por_sweep)
    imprimir_grupos("🧭 ANALISIS POR CONTEXTO", por_contexto)
    imprimir_grupos("🧬 ANALISIS SCORE + BOS", por_score_bos)
    imprimir_grupos("🧬 ANALISIS SCORE + CONTEXTO", por_score_contexto)


if __name__ == "__main__":
    main()
