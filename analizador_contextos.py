# -*- coding: utf-8 -*-
"""
analizador_contextos.py  V2
------------------------------------------------------------------------
Lee operaciones_paper.csv y genera rankings de contexto estructural.

Uso:
    python analizador_contextos.py
    python analizador_contextos.py --min-ops 20 --ocultar-sin-dato
    python analizador_contextos.py --min-ops 5 --orden wr --top 5
    python analizador_contextos.py --ocultar-sin-dato --export-csv
    python analizador_contextos.py --min-confianza 30
    python analizador_contextos.py --csv /ruta/al/archivo.csv

Secciones:
    1. Estructuras de mercado
    2. BOS (Break of Structure)
    3. CHOCH (Change of Character)
    4. Combinaciones contexto completo
    5. Contextos con mayor confianza   [NUEVO]
    6. Resumen global de contexto
    7. Resumen ejecutivo               [NUEVO]
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

ARCHIVO_DEFAULT    = "operaciones_paper.csv"
MIN_OPS_DEFAULT    = 20
MIN_CONF_DEFAULT   = 30
TOP_DEFAULT        = 10
ORDEN_DEFAULT      = "expectativa"
ANCHO              = 76

COLUMNAS_EXTRA = ["estructura", "bos", "choch", "sweep", "contexto_valido"]


# ---------------------------------------------------------------------------
# Lectura de CSV
# ---------------------------------------------------------------------------

def numero(v, d=0.0):
    try:
        return float(v)
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


# ---------------------------------------------------------------------------
# Agrupacion y metricas
# ---------------------------------------------------------------------------

def nuevo_grupo():
    return dict(ops=0, gan=0, per=0, profit=0.0)


def acumular(g, op):
    g["ops"]    += 1
    g["profit"] += numero(op.get("profit_loss", 0))
    if op.get("resultado", "") == "CORRECTA":
        g["gan"] += 1
    else:
        g["per"] += 1


def calcular_stats(g):
    ops    = g["ops"]
    profit = round(g["profit"], 4)
    wr     = round(g["gan"] / ops * 100, 1) if ops else 0.0
    expect = round(profit / ops, 4)          if ops else 0.0
    return dict(ops=ops, gan=g["gan"], per=g["per"],
                wr=wr, profit=profit, expect=expect)


def agrupar_por_campo(ops, campo):
    grupos = defaultdict(nuevo_grupo)
    for op in ops:
        clave = op.get(campo, "") or "SIN_DATO"
        acumular(grupos[clave], op)
    return grupos


def agrupar_combinaciones(ops):
    grupos = defaultdict(nuevo_grupo)
    for op in ops:
        est = op.get("estructura",      "") or ""
        bos = op.get("bos",             "") or ""
        ch  = op.get("choch",           "") or ""
        ctx = op.get("contexto_valido", "") or ""
        if not any([est, bos, ch, ctx]):
            continue
        clave = "{}|{}|{}|{}".format(
            est or "SIN_EST",
            bos or "SIN_BOS",
            ch  or "SIN_CH",
            ctx or "SIN_CTX"
        )
        acumular(grupos[clave], op)
    return grupos


def ordenar(grupos, criterio, min_ops, ocultar_sin_dato=False):
    filas = []
    for cat, g in grupos.items():
        if ocultar_sin_dato and cat == "SIN_DATO":
            continue
        s = calcular_stats(g)
        if s["ops"] < min_ops:
            continue
        s["cat"] = cat
        filas.append(s)

    if criterio == "wr":
        filas.sort(key=lambda x: (-x["wr"], -x["ops"]))
    elif criterio == "profit":
        filas.sort(key=lambda x: (-x["profit"], -x["ops"]))
    else:
        filas.sort(key=lambda x: (-x["expect"], -x["ops"]))

    return filas


# ---------------------------------------------------------------------------
# Helpers de formato
# ---------------------------------------------------------------------------

SEP  = "-" * ANCHO
SEP2 = "=" * ANCHO


def fmt_p(v):
    return ("+{:.2f}".format(v) if v >= 0 else "{:.2f}".format(v))


def fmt_e(v):
    return ("+{:.4f}".format(v) if v >= 0 else "{:.4f}".format(v))


# ---------------------------------------------------------------------------
# Impresion de secciones principales
# ---------------------------------------------------------------------------

HDR = "  {:<30} {:>5} {:>5} {:>5} {:>7} {:>9} {:>10}".format(
        "Categoria", "Ops", "Gan", "Per", "WR%", "Profit", "Expect/Op")


def imprimir_fila(pos, s):
    cat = s["cat"]
    if len(cat) > 29:
        cat = cat[:27] + ".."
    print("  {:>2}. {:<29} {:>5} {:>5} {:>5} {:>6.1f}% {:>9} {:>10}".format(
        pos, cat, s["ops"], s["gan"], s["per"],
        s["wr"], fmt_p(s["profit"]), fmt_e(s["expect"])))


def imprimir_seccion(titulo, grupos, criterio, min_ops, top, ocultar_sin_dato=False):
    print("")
    print(SEP2)
    print("  {}".format(titulo))
    print("  orden={} | min-ops={} | top={} | sin-dato={}".format(
        criterio, min_ops, top,
        "oculto" if ocultar_sin_dato else "visible"))
    print(SEP2)
    print(HDR)
    print(SEP)

    filas = ordenar(grupos, criterio, min_ops, ocultar_sin_dato)

    if not filas:
        grupos_vis = {k: v for k, v in grupos.items()
                     if not (ocultar_sin_dato and k == "SIN_DATO")}
        con_datos  = sum(1 for g in grupos_vis.values() if g["ops"] > 0)
        print("  Sin datos suficientes con min-ops={}.".format(min_ops))
        print("  Grupos visibles: {} | Con operaciones: {}".format(
            len(grupos_vis), con_datos))
        print("  Reduce --min-ops o espera mas operaciones del bot.")
        return

    print("  MEJORES:")
    for i, s in enumerate(filas[:top], 1):
        imprimir_fila(i, s)

    if len(filas) > 1:
        print("")
        print("  PEORES:")
        for i, s in enumerate(reversed(filas[:top if len(filas) >= top else len(filas)]), 1):
            imprimir_fila(i, s)


# ---------------------------------------------------------------------------
# Seccion 5: Contextos con mayor confianza
# ---------------------------------------------------------------------------

HDR_CONF = "  {:<14} {:<30} {:>5} {:>6} {:>9} {:>10}".format(
             "Tipo", "Categoria", "Ops", "WR%", "Profit", "Expect/Op")


def imprimir_seccion_confianza(g_est, g_bos, g_ch, g_comb,
                                min_confianza, ocultar_sin_dato=False):
    print("")
    print(SEP2)
    print("  5. CONTEXTOS CON MAYOR CONFIANZA")
    print("  min-confianza={} | orden=expectativa".format(min_confianza))
    print(SEP2)
    print(HDR_CONF)
    print(SEP)

    # Recolectar todas las categorias que pasan el umbral, con su tipo
    candidatos = []

    fuentes = [
        ("ESTRUCTURA", g_est),
        ("BOS",        g_bos),
        ("CHOCH",      g_ch),
        ("COMBINACION",g_comb),
    ]

    for tipo, grupos in fuentes:
        for cat, g in grupos.items():
            if ocultar_sin_dato and cat == "SIN_DATO":
                continue
            s = calcular_stats(g)
            if s["ops"] < min_confianza:
                continue
            s["cat"]  = cat
            s["tipo"] = tipo
            candidatos.append(s)

    if not candidatos:
        print("  Sin contextos con {} o mas operaciones.".format(min_confianza))
        print("  Aumenta el volumen de operaciones del bot o reduce --min-confianza.")
        return

    candidatos.sort(key=lambda x: (-x["expect"], -x["ops"]))

    for s in candidatos:
        cat = s["cat"]
        if len(cat) > 29:
            cat = cat[:27] + ".."
        print("  {:<14} {:<30} {:>5} {:>5.1f}% {:>9} {:>10}".format(
            s["tipo"], cat, s["ops"],
            s["wr"], fmt_p(s["profit"]), fmt_e(s["expect"])))


# ---------------------------------------------------------------------------
# Seccion 6: Resumen global de contexto
# ---------------------------------------------------------------------------

def resumen_global_contexto(ops):
    print("")
    print(SEP2)
    print("  6. RESUMEN GLOBAL DE CONTEXTO")
    print("  (siempre muestra ambos grupos, independiente de --ocultar-sin-dato)")
    print(SEP2)

    con_ctx = nuevo_grupo()
    sin_ctx = nuevo_grupo()

    for op in ops:
        est = op.get("estructura",      "") or ""
        bos = op.get("bos",             "") or ""
        ch  = op.get("choch",           "") or ""
        ctx = op.get("contexto_valido", "") or ""
        acumular(con_ctx if any([est, bos, ch, ctx]) else sin_ctx, op)

    def mostrar(label, g):
        if g["ops"] == 0:
            print("  {:<28}: sin datos".format(label))
            return
        s = calcular_stats(g)
        print("  {:<28}: ops={:>4}  WR={:>5.1f}%  profit={:>8}  expect/op={:>9}".format(
            label, s["ops"], s["wr"], fmt_p(s["profit"]), fmt_e(s["expect"])))

    mostrar("Con contexto completo", con_ctx)
    mostrar("Sin contexto",          sin_ctx)


# ---------------------------------------------------------------------------
# Seccion 7: Resumen ejecutivo
# ---------------------------------------------------------------------------

def _mejor_peor(grupos, criterio, min_ops, ocultar_sin_dato):
    filas = ordenar(grupos, criterio, min_ops, ocultar_sin_dato)
    if not filas:
        return None, None
    return filas[0], filas[-1]


def imprimir_resumen_ejecutivo(g_est, g_bos, g_ch, g_comb,
                                criterio, min_ops, ocultar_sin_dato):
    print("")
    print(SEP2)
    print("  7. RESUMEN EJECUTIVO")
    print("  orden={} | min-ops={}".format(criterio, min_ops))
    print(SEP2)

    etiquetas = [
        ("ESTRUCTURA",  g_est),
        ("BOS",         g_bos),
        ("CHOCH",       g_ch),
        ("COMBINACION", g_comb),
    ]

    for etiqueta, grupos in etiquetas:
        mejor, peor = _mejor_peor(grupos, criterio, min_ops, ocultar_sin_dato)

        def fmt_cat(s):
            if s is None:
                return "sin datos suficientes"
            cat = s["cat"]
            if len(cat) > 24:
                cat = cat[:22] + ".."
            return "{:<25} WR={:>5.1f}%  expect={:>9}".format(
                cat, s["wr"], fmt_e(s["expect"]))

        print("  {:<12} mejor: {}".format(etiqueta, fmt_cat(mejor)))
        print("  {:<12} peor : {}".format("",        fmt_cat(peor)))
        print("")


# ---------------------------------------------------------------------------
# Exportacion CSV
# ---------------------------------------------------------------------------

def exportar_ranking_csv(filas, nombre_archivo, etiqueta_campo):
    ruta = nombre_archivo
    # Evitar sobreescribir sin aviso
    if os.path.exists(ruta):
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = nombre_archivo.replace(".csv", "")
        ruta = "{}_{}.csv".format(base, ts)

    with open(ruta, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "categoria", "operaciones", "ganadas", "perdidas",
            "win_rate", "profit_total", "expectativa"
        ])
        for s in filas:
            writer.writerow([
                s["cat"], s["ops"], s["gan"], s["per"],
                round(s["wr"], 1), round(s["profit"], 2), round(s["expect"], 4)
            ])

    print("  Exportado: {} ({} filas)".format(ruta, len(filas)))
    return ruta


def exportar_todos(g_est, g_bos, g_ch, g_comb,
                   criterio, min_ops, ocultar_sin_dato):
    print("")
    print(SEP2)
    print("  EXPORTACION CSV")
    print(SEP2)

    pares = [
        (g_est,  "ranking_estructuras.csv",   "estructura"),
        (g_bos,  "ranking_bos.csv",           "bos"),
        (g_ch,   "ranking_choch.csv",         "choch"),
        (g_comb, "ranking_combinaciones.csv", "combinacion"),
    ]

    for grupos, nombre, campo in pares:
        filas = ordenar(grupos, criterio, min_ops, ocultar_sin_dato)
        exportar_ranking_csv(filas, nombre, campo)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analizador de contextos estructurales V2 -- Bot Deriv IA"
    )
    parser.add_argument("--csv",     default=ARCHIVO_DEFAULT,
                        help="Ruta al CSV de operaciones")
    parser.add_argument("--min-ops", type=int, default=MIN_OPS_DEFAULT,
                        help="Min ops para rankings (default: {})".format(MIN_OPS_DEFAULT))
    parser.add_argument("--min-confianza", type=int, default=MIN_CONF_DEFAULT,
                        help="Min ops para seccion confianza (default: {})".format(MIN_CONF_DEFAULT))
    parser.add_argument("--top",     type=int, default=TOP_DEFAULT,
                        help="Filas por ranking (default: {})".format(TOP_DEFAULT))
    parser.add_argument("--orden",   default=ORDEN_DEFAULT,
                        choices=["wr", "profit", "expectativa"],
                        help="Criterio de orden (default: {})".format(ORDEN_DEFAULT))
    parser.add_argument("--ocultar-sin-dato", action="store_true", default=False,
                        help="Excluir SIN_DATO de los rankings")
    parser.add_argument("--export-csv", action="store_true", default=False,
                        help="Exportar rankings a archivos CSV")
    args = parser.parse_args()

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print("")
    print(SEP2)
    print("  BOT DERIV IA -- Analizador de Contextos Estructurales V2")
    print("  Archivo      : {}".format(args.csv))
    print("  Fecha        : {}".format(ahora))
    print("  Min ops      : {}".format(args.min_ops))
    print("  Min confianza: {}".format(args.min_confianza))
    print("  Orden        : {}".format(args.orden))
    print("  Top          : {}".format(args.top))
    print("  Sin dato     : {}".format("oculto" if args.ocultar_sin_dato else "visible"))
    print("  Export CSV   : {}".format("si" if args.export_csv else "no"))
    print(SEP2)

    ops = leer_operaciones(args.csv)

    if not ops:
        print("\nERROR: Sin operaciones en el archivo.")
        sys.exit(0)

    print("  Operaciones cargadas: {}".format(len(ops)))

    osd = args.ocultar_sin_dato

    # Calcular grupos
    g_est  = agrupar_por_campo(ops, "estructura")
    g_bos  = agrupar_por_campo(ops, "bos")
    g_ch   = agrupar_por_campo(ops, "choch")
    g_comb = agrupar_combinaciones(ops)

    # Secciones 1-4
    imprimir_seccion("1. ESTRUCTURAS DE MERCADO",
                     g_est, args.orden, args.min_ops, args.top, osd)

    imprimir_seccion("2. BOS (Break of Structure)",
                     g_bos, args.orden, args.min_ops, args.top, osd)

    imprimir_seccion("3. CHOCH (Change of Character)",
                     g_ch, args.orden, args.min_ops, args.top, osd)

    imprimir_seccion("4. COMBINACIONES (Estructura+BOS+CHOCH+Contexto)",
                     g_comb, args.orden, args.min_ops, args.top, osd)

    # Seccion 5: confianza
    imprimir_seccion_confianza(g_est, g_bos, g_ch, g_comb,
                                args.min_confianza, osd)

    # Seccion 6: resumen global
    resumen_global_contexto(ops)

    # Seccion 7: resumen ejecutivo
    imprimir_resumen_ejecutivo(g_est, g_bos, g_ch, g_comb,
                                args.orden, args.min_ops, osd)

    # Exportacion CSV opcional
    if args.export_csv:
        exportar_todos(g_est, g_bos, g_ch, g_comb,
                       args.orden, args.min_ops, osd)

    print(SEP2)
    print("  OK  Analisis completado -- {} operaciones procesadas".format(len(ops)))
    print(SEP2)
    print("")


if __name__ == "__main__":
    main()
