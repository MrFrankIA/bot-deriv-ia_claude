# -*- coding: utf-8 -*-
"""
analizador_rendimiento.py
Lee operaciones_paper.csv y genera rankings de rendimiento.

Uso:
    python analizador_rendimiento.py
    python analizador_rendimiento.py --csv otra_ruta.csv
    python analizador_rendimiento.py --min-ops 5

Rankings generados:
    1. Patrones de vela
    2. Score de senal
    3. Estructuras de mercado
    4. Contexto de entrada
    5. BOS (Break of Structure)
    6. CHOCH (Change of Character)
"""

import csv
import os
import sys
import argparse
from collections import defaultdict
from datetime import datetime


# --- Configuracion -----------------------------------------------------------

ARCHIVO_DEFAULT  = "operaciones_paper.csv"
MIN_OPS_DEFAULT  = 1
ANCHO_TABLA      = 72

# Nombres de los 5 campos de contexto ausentes en headers antiguos de 12 col.
COLUMNAS_EXTRA = ["estructura", "bos", "choch", "sweep", "contexto_valido"]


# --- Helpers -----------------------------------------------------------------

def numero(valor, defecto=0.0):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def leer_operaciones(ruta):
    if not os.path.exists(ruta):
        print("\n ERROR: Archivo no encontrado: " + ruta)
        sys.exit(1)

    with open(ruta, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        filas  = list(reader)

    # Detectar si el header es el antiguo de 12 columnas (sin los 5 campos de contexto).
    # En ese caso, DictReader agrupa los valores sobrantes de filas nuevas
    # en fila[None] = [estructura, bos, choch, sweep, contexto_valido].
    # Los reasignamos a sus nombres correctos.
    header_antiguo = all(c not in header for c in COLUMNAS_EXTRA)

    resultado = []
    for fila in filas:
        normalizada = {}

        for k, v in fila.items():
            if k is None:
                # Header antiguo + fila nueva: reasignar valores a nombres correctos
                if header_antiguo and isinstance(v, list):
                    for nombre, valor in zip(COLUMNAS_EXTRA, v):
                        normalizada[nombre] = valor.strip() if valor else ""
                continue

            if isinstance(v, list):
                continue

            normalizada[k] = v.strip() if v else ""

        resultado.append(normalizada)

    return resultado


def acumular(grupos, clave, fila):
    g = grupos[clave]
    g["ops"]     += 1
    resultado     = fila.get("resultado", "")
    pl            = numero(fila.get("profit_loss", 0))
    dd            = numero(fila.get("drawdown", 0))

    if resultado == "CORRECTA":
        g["ganadas"] += 1
    else:
        g["perdidas"] += 1

    g["profit"] += pl

    if dd > g["drawdown_max"]:
        g["drawdown_max"] = dd


def nuevo_grupo():
    return {
        "ops":          0,
        "ganadas":      0,
        "perdidas":     0,
        "profit":       0.0,
        "drawdown_max": 0.0,
    }


def calcular_wr(g):
    if g["ops"] == 0:
        return 0.0
    return g["ganadas"] / g["ops"] * 100


def construir_ranking(grupos, min_ops=1, orden="wr"):
    filas = []
    for nombre, g in grupos.items():
        if g["ops"] < min_ops:
            continue
        wr = calcular_wr(g)
        filas.append({
            "nombre":       nombre,
            "ops":          g["ops"],
            "ganadas":      g["ganadas"],
            "perdidas":     g["perdidas"],
            "wr":           wr,
            "profit":       round(g["profit"], 2),
            "drawdown_max": round(g["drawdown_max"], 2),
        })

    if orden == "wr":
        filas.sort(key=lambda x: (-x["wr"], -x["ops"]))
    elif orden == "profit":
        filas.sort(key=lambda x: (-x["profit"], -x["ops"]))
    else:
        filas.sort(key=lambda x: -x["ops"])

    return filas


# --- Impresion de tabla ------------------------------------------------------

SEP  = "-" * ANCHO_TABLA
SEP2 = "=" * ANCHO_TABLA


def imprimir_encabezado(titulo):
    print("")
    print(SEP2)
    print("  " + titulo)
    print(SEP2)
    print("  {:<28}  {:>4}  {:>4}  {:>4}  {:>6}  {:>8}  {:>7}".format(
        "Categoria", "Ops", "Gan", "Per", "WR%", "Profit", "DD Max"))
    print(SEP)


def imprimir_fila(pos, nombre, f):
    profit_str = "+{:.2f}".format(f["profit"]) if f["profit"] >= 0 else "{:.2f}".format(f["profit"])
    print("  {:>2}. {:<26}  {:>4}  {:>4}  {:>4}  {:>5.1f}%  {:>8}  {:>7.2f}".format(
        pos, nombre,
        f["ops"], f["ganadas"], f["perdidas"],
        f["wr"], profit_str, f["drawdown_max"]
    ))


def imprimir_ranking(titulo, filas):
    imprimir_encabezado(titulo)
    if not filas:
        print("  AVISO: Sin datos suficientes para este ranking.")
        print("     (Las columnas correspondientes estan vacias en el CSV actual.)")
        print("     Se poblaran automaticamente a medida que el bot opere.")
        return
    for i, f in enumerate(filas, start=1):
        imprimir_fila(i, f["nombre"], f)


def imprimir_resumen_global(operaciones):
    total    = len(operaciones)
    if total == 0:
        print("\n ERROR: No hay operaciones registradas.")
        return

    ganadas  = sum(1 for r in operaciones if r.get("resultado") == "CORRECTA")
    perdidas = total - ganadas
    profit   = sum(numero(r.get("profit_loss", 0)) for r in operaciones)
    wr       = ganadas / total * 100
    balance  = numero(operaciones[-1].get("balance", 0)) if operaciones else 0
    dd_max   = max((numero(r.get("drawdown_max", r.get("drawdown", 0))) for r in operaciones), default=0)

    profit_str = "+{:.2f}".format(profit) if profit >= 0 else "{:.2f}".format(profit)

    print("")
    print(SEP2)
    print("  RESUMEN GLOBAL")
    print(SEP2)
    print("  Operaciones totales : {}".format(total))
    print("  Ganadas             : {}".format(ganadas))
    print("  Perdidas            : {}".format(perdidas))
    print("  Win Rate            : {:.1f}%".format(wr))
    print("  Profit total        : {}".format(profit_str))
    print("  Balance actual      : {:.2f}".format(balance))
    print("  Drawdown maximo     : {:.2f}".format(dd_max))


# --- Rankings ----------------------------------------------------------------

def ranking_patron(operaciones, min_ops):
    grupos = defaultdict(nuevo_grupo)
    for fila in operaciones:
        clave = fila.get("patron", "") or "DESCONOCIDO"
        acumular(grupos, clave, fila)
    return construir_ranking(grupos, min_ops)


def ranking_score(operaciones, min_ops):
    grupos = defaultdict(nuevo_grupo)
    for fila in operaciones:
        sc    = fila.get("score_senal", "") or ""
        clave = "Score " + sc if sc else "Sin score"
        acumular(grupos, clave, fila)
    return construir_ranking(grupos, min_ops, orden="ops")


def ranking_campo(operaciones, campo, min_ops, etiqueta_vacia="Sin dato"):
    grupos      = defaultdict(nuevo_grupo)
    tiene_datos = False

    for fila in operaciones:
        val = fila.get(campo, "") or ""
        if val:
            tiene_datos = True
        clave = val if val else etiqueta_vacia
        acumular(grupos, clave, fila)

    if not tiene_datos:
        return []

    return construir_ranking(grupos, min_ops)


# --- Main --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analizador de rendimiento -- Bot Deriv IA"
    )
    parser.add_argument(
        "--csv",
        default=ARCHIVO_DEFAULT,
        help="Ruta al CSV de operaciones (default: " + ARCHIVO_DEFAULT + ")"
    )
    parser.add_argument(
        "--min-ops",
        type=int,
        default=MIN_OPS_DEFAULT,
        help="Minimo de operaciones para incluir en ranking"
    )
    args = parser.parse_args()

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print("")
    print(SEP2)
    print("  BOT DERIV IA -- Analizador de Rendimiento")
    print("  Archivo : " + args.csv)
    print("  Fecha   : " + ahora)
    print("  Min ops : {}".format(args.min_ops))
    print(SEP2)

    operaciones = leer_operaciones(args.csv)

    if not operaciones:
        print("\n ERROR: El archivo esta vacio o no tiene operaciones validas.")
        sys.exit(0)

    imprimir_resumen_global(operaciones)

    imprimir_ranking("1. RANKING -- PATRONES DE VELA",
                     ranking_patron(operaciones, args.min_ops))

    imprimir_ranking("2. RANKING -- SCORE DE SENAL",
                     ranking_score(operaciones, args.min_ops))

    imprimir_ranking("3. RANKING -- ESTRUCTURA DE MERCADO",
                     ranking_campo(operaciones, "estructura", args.min_ops))

    imprimir_ranking("4. RANKING -- CONTEXTO DE ENTRADA",
                     ranking_campo(operaciones, "contexto_valido", args.min_ops))

    imprimir_ranking("5. RANKING -- BOS (Break of Structure)",
                     ranking_campo(operaciones, "bos", args.min_ops))

    imprimir_ranking("6. RANKING -- CHOCH (Change of Character)",
                     ranking_campo(operaciones, "choch", args.min_ops))

    print("")
    print(SEP2)
    print("  OK  Analisis completado -- {} operaciones procesadas".format(len(operaciones)))
    print(SEP2)
    print("")


if __name__ == "__main__":
    main()
