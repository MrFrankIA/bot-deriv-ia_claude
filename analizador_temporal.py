# -*- coding: utf-8 -*-
"""
analizador_temporal.py
------------------------------------------------------------------------
Lee operaciones_paper.csv y analiza el rendimiento por hora del dia.

Uso:
    python analizador_temporal.py
    python analizador_temporal.py --min-ops 5 --top 5
    python analizador_temporal.py --orden wr
    python analizador_temporal.py --solo-contexto
    python analizador_temporal.py --solo-contexto --export-csv
    python analizador_temporal.py --csv /ruta/archivo.csv

Secciones:
    1. Mejores horas
    2. Peores horas
    3. Tabla completa 00-23
    4. Bloques horarios
    5. Tendencia temporal (cuartos)
------------------------------------------------------------------------
"""

import csv
import os
import sys
import argparse
from collections import defaultdict
from datetime import datetime


# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

ARCHIVO_DEFAULT  = "operaciones_paper.csv"
MIN_OPS_DEFAULT  = 5
TOP_DEFAULT      = 5
ORDEN_DEFAULT    = "expectativa"
ANCHO            = 74

COLUMNAS_EXTRA = ["estructura", "bos", "choch", "sweep", "contexto_valido"]

BLOQUES = [
    ("MADRUGADA", "00-05", list(range(0, 6))),
    ("MANANA",    "06-11", list(range(6, 12))),
    ("TARDE",     "12-17", list(range(12, 18))),
    ("NOCHE",     "18-23", list(range(18, 24))),
]


# ---------------------------------------------------------------------------
# Lectura de CSV
# ---------------------------------------------------------------------------

def numero(v, d=0.0):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return d


def leer_operaciones(ruta):
    if not os.path.exists(ruta):
        print("\nERROR: Archivo no encontrado: " + ruta)
        sys.exit(1)

    with open(ruta, mode="r", newline="", encoding="utf-8") as f:
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


def tiene_contexto(op):
    """Retorna True si la operacion tiene al menos un campo de contexto con dato."""
    return any(
        op.get(campo, "") not in ("", None)
        for campo in ["estructura", "bos", "choch", "contexto_valido"]
    )


def extraer_hora(op):
    """Extrae la hora (int 0-23) del campo hora en formato HH:MM:SS."""
    hora_raw = op.get("hora", "") or ""
    if not hora_raw or ":" not in hora_raw:
        return None
    try:
        return int(hora_raw.split(":")[0])
    except ValueError:
        return None


def es_valida(op):
    return op.get("resultado") in ("CORRECTA", "INCORRECTA")


# ---------------------------------------------------------------------------
# Agrupacion y metricas
# ---------------------------------------------------------------------------

def nuevo_grupo():
    return dict(ops=0, gan=0, per=0, profit=0.0, dd_max=0.0, indice_min=None)


def acumular(g, op, indice):
    g["ops"]    += 1
    g["profit"] += numero(op.get("profit_loss", 0))
    dd = numero(op.get("drawdown", 0))
    if dd > g["dd_max"]:
        g["dd_max"] = dd
    if op.get("resultado") == "CORRECTA":
        g["gan"] += 1
    else:
        g["per"] += 1
    if g["indice_min"] is None:
        g["indice_min"] = indice


def calcular_stats(g):
    ops    = g["ops"]
    profit = round(g["profit"], 2)
    wr     = round(g["gan"] / ops * 100, 1) if ops else 0.0
    expect = round(profit / ops, 4)          if ops else 0.0
    dd_max = round(g["dd_max"], 2)
    return dict(ops=ops, gan=g["gan"], per=g["per"],
                wr=wr, profit=profit, expect=expect, dd_max=dd_max)


def agrupar_por_hora(ops):
    grupos = defaultdict(nuevo_grupo)
    for i, op in enumerate(ops):
        h = extraer_hora(op)
        if h is None:
            continue
        acumular(grupos[h], op, i)
    return grupos


def agrupar_por_bloque(ops):
    grupos = {}
    for nombre, rango_str, horas in BLOQUES:
        grupos[nombre] = (rango_str, nuevo_grupo())

    for i, op in enumerate(ops):
        h = extraer_hora(op)
        if h is None:
            continue
        for nombre, rango_str, horas in BLOQUES:
            if h in horas:
                acumular(grupos[nombre][1], op, i)
                break
    return grupos


def agrupar_por_cuarto(ops):
    """Divide las operaciones en 4 cuartos cronologicos."""
    validas = [op for op in ops if es_valida(op)]
    n = len(validas)
    if n == 0:
        return []
    size = max(1, n // 4)
    cuartos = []
    for i in range(4):
        inicio = i * size
        fin    = (i + 1) * size if i < 3 else n
        bloque = validas[inicio:fin]
        g = nuevo_grupo()
        for j, op in enumerate(bloque):
            acumular(g, op, inicio + j)
        s = calcular_stats(g)
        s["etiqueta"] = "Q{} (ops {}-{})".format(i + 1, inicio + 1, fin)
        cuartos.append(s)
    return cuartos


def ordenar_horas(grupos, criterio, min_ops):
    filas = []
    for h, g in grupos.items():
        s = calcular_stats(g)
        if s["ops"] < min_ops:
            continue
        s["hora"] = h
        filas.append(s)

    if criterio == "wr":
        filas.sort(key=lambda x: (-x["wr"], -x["ops"]))
    elif criterio == "profit":
        filas.sort(key=lambda x: (-x["profit"], -x["ops"]))
    else:
        filas.sort(key=lambda x: (-x["expect"], -x["ops"]))

    return filas


# ---------------------------------------------------------------------------
# Formato e impresion
# ---------------------------------------------------------------------------

SEP  = "-" * ANCHO
SEP2 = "=" * ANCHO

HDR_HORA = "  {:<8} {:>4} {:>4} {:>4} {:>6} {:>9} {:>10} {:>7}".format(
             "Hora", "Ops", "Gan", "Per", "WR%", "Profit", "Expect/Op", "DD Max")

HDR_BLOQUE = "  {:<12} {:<8} {:>5} {:>6} {:>9} {:>10} {:>7}".format(
               "Bloque", "Rango", "Ops", "WR%", "Profit", "Expect/Op", "DD Max")

HDR_CUARTO = "  {:<22} {:>4} {:>6} {:>9} {:>10}".format(
               "Periodo", "Ops", "WR%", "Profit", "Expect/Op")


def fmt_p(v):
    return ("+{:.2f}".format(v) if v >= 0 else "{:.2f}".format(v))


def fmt_e(v):
    return ("+{:.4f}".format(v) if v >= 0 else "{:.4f}".format(v))


def imprimir_fila_hora(s):
    print("  {:02d}:xx   {:>4} {:>4} {:>4} {:>5.1f}% {:>9} {:>10} {:>7.2f}".format(
        s["hora"], s["ops"], s["gan"], s["per"],
        s["wr"], fmt_p(s["profit"]), fmt_e(s["expect"]), s["dd_max"]))


def imprimir_seccion_horas(titulo, filas_ordenadas, top, modo):
    print("")
    print(SEP2)
    print("  {}".format(titulo))
    print(SEP2)
    print(HDR_HORA)
    print(SEP)

    if not filas_ordenadas:
        print("  Sin horas con datos suficientes.")
        return

    muestra = filas_ordenadas[:top] if modo == "mejores" else list(reversed(filas_ordenadas))[:top]
    for s in muestra:
        imprimir_fila_hora(s)


def imprimir_tabla_completa(grupos, min_ops):
    print("")
    print(SEP2)
    print("  3. TABLA COMPLETA POR HORA (00-23)")
    print(SEP2)
    print(HDR_HORA)
    print(SEP)

    for h in range(24):
        if h not in grupos:
            print("  {:02d}:xx   {:>4}".format(h, 0) + "  (sin operaciones)")
            continue
        g = grupos[h]
        s = calcular_stats(g)
        marker = " *" if s["ops"] < min_ops else ""
        print("  {:02d}:xx   {:>4} {:>4} {:>4} {:>5.1f}% {:>9} {:>10} {:>7.2f}{}".format(
            h, s["ops"], s["gan"], s["per"],
            s["wr"], fmt_p(s["profit"]), fmt_e(s["expect"]), s["dd_max"], marker))
    print("  (* = menos de {} ops, excluida de rankings)".format(min_ops))


def imprimir_bloques(grupos_bloque):
    print("")
    print(SEP2)
    print("  4. BLOQUES HORARIOS")
    print(SEP2)
    print(HDR_BLOQUE)
    print(SEP)

    for nombre, rango_str, _ in BLOQUES:
        rango_str_real, g = grupos_bloque[nombre]
        s = calcular_stats(g)
        if s["ops"] == 0:
            print("  {:<12} {:<8} {:>5}  sin datos".format(nombre, rango_str_real, 0))
            continue
        print("  {:<12} {:<8} {:>5} {:>5.1f}% {:>9} {:>10} {:>7.2f}".format(
            nombre, rango_str_real, s["ops"],
            s["wr"], fmt_p(s["profit"]), fmt_e(s["expect"]), s["dd_max"]))


def imprimir_tendencia(cuartos):
    print("")
    print(SEP2)
    print("  5. TENDENCIA TEMPORAL (cuartos cronologicos)")
    print("  Muestra si el rendimiento mejora o empeora a lo largo del historial.")
    print(SEP2)
    print(HDR_CUARTO)
    print(SEP)

    if not cuartos:
        print("  Sin datos suficientes.")
        return

    for s in cuartos:
        print("  {:<22} {:>4} {:>5.1f}% {:>9} {:>10}".format(
            s["etiqueta"], s["ops"],
            s["wr"], fmt_p(s["profit"]), fmt_e(s["expect"])))

    # Indicar tendencia simple
    if len(cuartos) >= 2:
        print("")
        e1 = cuartos[0]["expect"]
        e4 = cuartos[-1]["expect"]
        diff = e4 - e1
        if diff > 0.02:
            print("  Tendencia: MEJORANDO  (expect Q1={} -> Q4={})".format(
                fmt_e(e1), fmt_e(e4)))
        elif diff < -0.02:
            print("  Tendencia: EMPEORANDO (expect Q1={} -> Q4={})".format(
                fmt_e(e1), fmt_e(e4)))
        else:
            print("  Tendencia: ESTABLE    (expect Q1={} -> Q4={})".format(
                fmt_e(e1), fmt_e(e4)))


# ---------------------------------------------------------------------------
# Exportacion CSV
# ---------------------------------------------------------------------------

def exportar_csv(filas_ordenadas, grupos_bloque, cuartos):
    nombre = "ranking_temporal.csv"
    if os.path.exists(nombre):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = "ranking_temporal_{}.csv".format(ts)

    with open(nombre, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Ranking por hora
        writer.writerow(["tipo", "categoria", "operaciones", "ganadas", "perdidas",
                         "win_rate", "profit_total", "expectativa", "drawdown_max"])
        for s in filas_ordenadas:
            writer.writerow([
                "hora", "{:02d}:xx".format(s["hora"]),
                s["ops"], s["gan"], s["per"],
                s["wr"], s["profit"], s["expect"], s["dd_max"]
            ])
        # Bloques
        for nombre_b, rango_str, _ in BLOQUES:
            _, g = grupos_bloque[nombre_b]
            s = calcular_stats(g)
            writer.writerow([
                "bloque", nombre_b,
                s["ops"], s["gan"], s["per"],
                s["wr"], s["profit"], s["expect"], s["dd_max"]
            ])
        # Cuartos
        for s in cuartos:
            writer.writerow([
                "cuarto", s["etiqueta"],
                s["ops"], s["gan"], s["per"],
                s["wr"], s["profit"], s["expect"], 0
            ])

    print("")
    print(SEP2)
    print("  EXPORTACION CSV")
    print(SEP2)
    print("  Exportado: {} ({} horas + 4 bloques + 4 cuartos)".format(
        nombre, len(filas_ordenadas)))
    return nombre


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analizador temporal -- Bot Deriv IA"
    )
    parser.add_argument("--csv", default=ARCHIVO_DEFAULT,
                        help="Ruta al CSV de operaciones")
    parser.add_argument("--min-ops", type=int, default=MIN_OPS_DEFAULT,
                        help="Min ops para aparecer en ranking (default: {})".format(MIN_OPS_DEFAULT))
    parser.add_argument("--top", type=int, default=TOP_DEFAULT,
                        help="Filas en mejores/peores (default: {})".format(TOP_DEFAULT))
    parser.add_argument("--orden", default=ORDEN_DEFAULT,
                        choices=["wr", "profit", "expectativa"],
                        help="Criterio de orden (default: {})".format(ORDEN_DEFAULT))
    parser.add_argument("--solo-contexto", action="store_true", default=False,
                        help="Usar solo operaciones con datos de contexto estructural")
    parser.add_argument("--export-csv", action="store_true", default=False,
                        help="Exportar resultados a ranking_temporal.csv")
    args = parser.parse_args()

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print("")
    print(SEP2)
    print("  BOT DERIV IA -- Analizador Temporal")
    print("  Archivo      : {}".format(args.csv))
    print("  Fecha        : {}".format(ahora))
    print("  Min ops      : {}".format(args.min_ops))
    print("  Top          : {}".format(args.top))
    print("  Orden        : {}".format(args.orden))
    print("  Solo contexto: {}".format("si" if args.solo_contexto else "no"))
    print("  Export CSV   : {}".format("si" if args.export_csv else "no"))
    print(SEP2)

    todas = leer_operaciones(args.csv)
    ops   = [op for op in todas if es_valida(op)]

    total_cargadas = len(ops)

    if args.solo_contexto:
        ops = [op for op in ops if tiene_contexto(op)]
        print("  Operaciones cargadas  : {}".format(total_cargadas))
        print("  Con contexto (usadas) : {}".format(len(ops)))
        print("  Sin contexto (omitidas): {}".format(total_cargadas - len(ops)))
    else:
        print("  Operaciones cargadas  : {}".format(total_cargadas))

    if not ops:
        print("\nERROR: Sin operaciones validas para analizar.")
        sys.exit(0)

    # Calcular grupos
    grupos_hora   = agrupar_por_hora(ops)
    grupos_bloque = agrupar_por_bloque(ops)
    cuartos       = agrupar_por_cuarto(ops)

    # Ranking ordenado
    filas_ordenadas = ordenar_horas(grupos_hora, args.orden, args.min_ops)

    # Secciones 1 y 2: Mejores y Peores
    imprimir_seccion_horas(
        "1. MEJORES HORAS  (orden={} | min-ops={})".format(args.orden, args.min_ops),
        filas_ordenadas, args.top, "mejores")

    imprimir_seccion_horas(
        "2. PEORES HORAS   (orden={} | min-ops={})".format(args.orden, args.min_ops),
        filas_ordenadas, args.top, "peores")

    # Seccion 3: Tabla completa
    imprimir_tabla_completa(grupos_hora, args.min_ops)

    # Seccion 4: Bloques
    imprimir_bloques(grupos_bloque)

    # Seccion 5: Tendencia
    imprimir_tendencia(cuartos)

    # Exportacion
    if args.export_csv:
        exportar_csv(filas_ordenadas, grupos_bloque, cuartos)

    print("")
    print(SEP2)
    print("  OK  Analisis completado -- {} operaciones procesadas".format(len(ops)))
    print(SEP2)
    print("")


if __name__ == "__main__":
    main()
