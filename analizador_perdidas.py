#!/usr/bin/env python3
"""
analizador_perdidas.py
Analiza que tienen en comun las operaciones perdedoras.
Identifica grupos con peor rendimiento por hora, contexto y combinacion.
"""

import csv
import argparse
from collections import defaultdict
from datetime import datetime

# ─────────────────────── CSV ─────────────────────────

COLUMNAS_EXTRA = ['estructura', 'bos', 'choch', 'sweep', 'contexto_valido']

def leer_csv(ruta):
    with open(ruta, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        raw = list(reader)

    header_antiguo = all(c not in header for c in COLUMNAS_EXTRA)

    filas = []
    for fila in raw:
        norm = {}
        for k, v in fila.items():
            if k is None:
                if header_antiguo and isinstance(v, list):
                    for nombre, valor in zip(COLUMNAS_EXTRA, v):
                        norm[nombre] = valor.strip() if valor else ''
                continue
            if isinstance(v, list):
                continue
            norm[k] = v.strip() if v else ''
        filas.append(norm)
    return filas

def extraer_hora(fila):
    h = fila.get('hora', '') or ''
    if ':' in h:
        return h.split(':')[0].zfill(2)
    return None

def profit_fila(fila):
    try:
        return float(fila.get('profit_loss', 0) or 0)
    except ValueError:
        return 0.0

def es_ganada(fila):
    return (fila.get('resultado', '') or '').strip().upper() == 'CORRECTA'

CAMPOS_CONTEXTO = ['estructura', 'bos', 'choch', 'contexto_valido']

def tiene_contexto(fila):
    for c in CAMPOS_CONTEXTO:
        v = (fila.get(c, '') or '').strip()
        if v and v != 'None':
            return True
    return False

# ─────────────────────── METRICAS ────────────────────

def nuevo_grupo():
    return {'ops': 0, 'gan': 0, 'per': 0, 'profit': 0.0}

def acumular(g, fila):
    g['ops'] += 1
    g['profit'] += profit_fila(fila)
    if es_ganada(fila):
        g['gan'] += 1
    else:
        g['per'] += 1

def finalizar(g):
    ops = g['ops']
    if ops == 0:
        return dict(g, wr=0.0, expectativa=0.0)
    return dict(g,
        wr=g['gan'] / ops * 100,
        expectativa=g['profit'] / ops)

def calcular_global(filas):
    g = nuevo_grupo()
    for f in filas:
        acumular(g, f)
    return finalizar(g)

# ─────────────────────── AGRUPACION ──────────────────

def agrupar_campo(filas, campo):
    grupos = defaultdict(nuevo_grupo)
    for f in filas:
        v = (f.get(campo, '') or '').strip()
        if not v or v == 'None':
            v = 'SIN_DATO'
        acumular(grupos[v], f)
    return {k: finalizar(v) for k, v in grupos.items()}

def agrupar_hora(filas):
    grupos = defaultdict(nuevo_grupo)
    for f in filas:
        h = extraer_hora(f)
        if h is None:
            continue
        acumular(grupos[h + 'xx'], f)
    return {k: finalizar(v) for k, v in grupos.items()}

def agrupar_combinacion(filas):
    grupos = defaultdict(nuevo_grupo)
    for f in filas:
        h = extraer_hora(f)
        if h is None:
            continue
        est = (f.get('estructura', '') or '').strip() or 'SIN_DATO'
        bos = (f.get('bos', '') or '').strip() or 'SIN_DATO'
        choch = (f.get('choch', '') or '').strip() or 'SIN_DATO'
        ctx = (f.get('contexto_valido', '') or '').strip() or 'SIN_DATO'
        key = "{}xx | {} | {} | {} | ctx={}".format(h, est, bos, choch, ctx)
        acumular(grupos[key], f)
    return {k: finalizar(v) for k, v in grupos.items()}

# ─────────────────────── OUTPUT ──────────────────────

SEP  = "=" * 90
SEP2 = "-" * 90
ANC  = {'label': 40, 'ops': 5, 'gan': 5, 'per': 5, 'wr': 8, 'profit': 9, 'exp': 10}

def header_tabla():
    return "  {:<{}} {:>{}} {:>{}} {:>{}} {:>{}} {:>{}} {:>{}}".format(
        'GRUPO/VALOR', ANC['label'],
        'OPS', ANC['ops'], 'GAN', ANC['gan'], 'PER', ANC['per'],
        'WR%', ANC['wr'], 'PROFIT', ANC['profit'], 'EXPECT/OP', ANC['exp'])

def fila_tabla(label, m):
    label_str = label[:ANC['label']].ljust(ANC['label'])
    wr_str     = "{:.1f}%".format(m['wr'])
    profit_str = "{:+.2f}".format(m['profit'])
    exp_str    = "{:+.4f}".format(m['expectativa'])
    return "  {} {:>{}} {:>{}} {:>{}} {:>{}} {:>{}} {:>{}}".format(
        label_str,
        m['ops'], ANC['ops'], m['gan'], ANC['gan'], m['per'], ANC['per'],
        wr_str, ANC['wr'], profit_str, ANC['profit'], exp_str, ANC['exp'])

def separador():
    return "  " + "-" * 87

def imprimir_ranking(titulo, grupos, min_ops, top, orden):
    # orden: 'expectativa' (asc) o 'profit' (asc)
    filtrados = {k: v for k, v in grupos.items() if v['ops'] >= min_ops}

    print("\n" + SEP2)
    print("  " + titulo)
    nota = "  (min {} ops | orden: {} ascendente | peores primero)".format(min_ops, orden)
    print(nota)
    print(SEP2)

    if not filtrados:
        print("  [Sin grupos con >= {} ops]".format(min_ops))
        return

    ordenados = sorted(filtrados.items(), key=lambda x: x[1][orden])

    print(header_tabla())
    print(separador())
    for label, m in ordenados[:top]:
        print(fila_tabla(label, m))

# ─────────────────────── EXPORT CSV ──────────────────

def exportar_csv(todas_secciones, min_ops, ruta_out='ranking_perdidas.csv'):
    filas_out = []
    for seccion, grupos in todas_secciones:
        for label, m in grupos.items():
            if m['ops'] >= min_ops:
                filas_out.append({
                    'seccion': seccion,
                    'grupo': label,
                    'ops': m['ops'],
                    'ganadas': m['gan'],
                    'perdidas': m['per'],
                    'win_rate': round(m['wr'], 2),
                    'profit_total': round(m['profit'], 4),
                    'expectativa': round(m['expectativa'], 4),
                })
    if not filas_out:
        print("  [Export CSV: sin datos]")
        return
    with open(ruta_out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=filas_out[0].keys())
        writer.writeheader()
        writer.writerows(filas_out)
    print("\n  CSV exportado -> {}  ({} grupos)".format(ruta_out, len(filas_out)))

# ─────────────────────── MAIN ────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Analizador de perdidas')
    parser.add_argument('--csv',           default='operaciones_paper.csv')
    parser.add_argument('--min-ops',       type=int, default=30)
    parser.add_argument('--top',           type=int, default=10)
    parser.add_argument('--solo-contexto', action='store_true')
    parser.add_argument('--orden',         default='expectativa',
                        choices=['expectativa', 'profit'],
                        help='Criterio de ordenacion ascendente (peores primero)')
    parser.add_argument('--export-csv',    action='store_true')
    args = parser.parse_args()

    filas_raw = leer_csv(args.csv)
    total_raw = len(filas_raw)

    if args.solo_contexto:
        filas = [f for f in filas_raw if tiene_contexto(f)]
    else:
        filas = filas_raw

    usadas = len(filas)
    modo_str = "solo-contexto ({}/{})".format(usadas, total_raw) if args.solo_contexto else "todas ({})".format(usadas)
    orden_nota = "Expect/Op identifica peor rendimiento promedio | Profit identifica mayor destruccion de capital"

    print("\n" + SEP)
    print("  ANALIZADOR DE PERDIDAS")
    print("  Archivo : {}".format(args.csv))
    print("  Ops     : {}  |  min-ops: {}  |  top: {}  |  orden: {}".format(
        modo_str, args.min_ops, args.top, args.orden))
    print("  Nota    : " + orden_nota)
    print("  Fecha   : {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print(SEP)

    # [1] Global
    m_global = calcular_global(filas)
    print("\n" + SEP2)
    print("  [1] RESUMEN GLOBAL")
    print(SEP2)
    print("  Ops: {}  |  Gan: {}  |  Per: {}  |  WR: {:.1f}%  |  Profit: {:+.2f}  |  Expect/Op: {:+.4f}".format(
        m_global['ops'], m_global['gan'], m_global['per'],
        m_global['wr'], m_global['profit'], m_global['expectativa']))

    # Agrupaciones
    g_hora  = agrupar_hora(filas)
    g_est   = agrupar_campo(filas, 'estructura')
    g_bos   = agrupar_campo(filas, 'bos')
    g_choch = agrupar_campo(filas, 'choch')
    g_sweep = agrupar_campo(filas, 'sweep')
    g_ctx   = agrupar_campo(filas, 'contexto_valido')
    g_comb  = agrupar_combinacion(filas)

    # Ajuste automatico de min-ops para combinaciones
    min_ops_comb = args.min_ops
    if not any(v['ops'] >= min_ops_comb for v in g_comb.values()):
        min_ops_comb = 5
        aviso_comb = "  [Aviso: ninguna combinacion alcanza {} ops. Usando min-ops=5 para seccion [8]]".format(args.min_ops)
    else:
        aviso_comb = None

    imprimir_ranking("[2] PEORES GRUPOS -- Por hora",           g_hora,  args.min_ops, args.top, args.orden)
    imprimir_ranking("[3] PEORES GRUPOS -- Por estructura",     g_est,   args.min_ops, args.top, args.orden)
    imprimir_ranking("[4] PEORES GRUPOS -- Por BOS",            g_bos,   args.min_ops, args.top, args.orden)
    imprimir_ranking("[5] PEORES GRUPOS -- Por CHOCH",          g_choch, args.min_ops, args.top, args.orden)
    imprimir_ranking("[6] PEORES GRUPOS -- Por sweep",          g_sweep, args.min_ops, args.top, args.orden)
    imprimir_ranking("[7] PEORES GRUPOS -- Por contexto_valido",g_ctx,   args.min_ops, args.top, args.orden)

    if aviso_comb:
        print("\n" + aviso_comb)
    imprimir_ranking("[8] PEORES COMBINACIONES -- Hora + Estructura + BOS + CHOCH + Contexto",
                     g_comb, min_ops_comb, args.top, args.orden)

    print("\n" + SEP)
    print("  NOTA: Resultados locales son prueba tecnica.")
    print("  Ejecutar en VPS con CSV completo para validacion definitiva.")
    print(SEP + "\n")

    if args.export_csv:
        todas = [
            ('hora', g_hora), ('estructura', g_est), ('bos', g_bos),
            ('choch', g_choch), ('sweep', g_sweep), ('contexto_valido', g_ctx),
            ('combinacion', g_comb),
        ]
        exportar_csv(todas, args.min_ops)

if __name__ == '__main__':
    main()
