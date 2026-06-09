#!/usr/bin/env python3
"""
analizador_cruzado.py
Analiza combinaciones entre hora y campos de contexto.
Cruces: Hora x Estructura, Hora x BOS, Hora x CHOCH, Hora x Contexto valido
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

def profit(fila):
    try:
        return float(fila.get('profit_loss', 0) or 0)
    except ValueError:
        return 0.0

def es_ganada(fila):
    return (fila.get('resultado', '') or '').strip().upper() == 'CORRECTA'

CAMPOS_CONTEXTO = ['estructura', 'bos', 'choch', 'contexto_valido']

def tiene_contexto(fila):
    """True si al menos un campo de contexto tiene dato real."""
    for c in CAMPOS_CONTEXTO:
        v = (fila.get(c, '') or '').strip()
        if v and v != 'None':
            return True
    return False

# ─────────────────────── CRUCE ───────────────────────

def calcular_cruce(filas, campo, ocultar_sin_dato):
    grupos = defaultdict(lambda: {'ops': 0, 'gan': 0, 'per': 0, 'profit': 0.0})

    for f in filas:
        hora = extraer_hora(f)
        if hora is None:
            continue
        valor = (f.get(campo, '') or '').strip()
        if not valor or valor == 'None':
            valor = 'SIN_DATO'
        if ocultar_sin_dato and valor == 'SIN_DATO':
            continue
        key = (hora, valor)
        grupos[key]['ops'] += 1
        grupos[key]['profit'] += profit(f)
        if es_ganada(f):
            grupos[key]['gan'] += 1
        else:
            grupos[key]['per'] += 1

    resultados = []
    for (hora, valor), g in grupos.items():
        ops = g['ops']
        gan = g['gan']
        per = g['per']
        prof = g['profit']
        wr = (gan / ops * 100) if ops > 0 else 0.0
        exp = prof / ops if ops > 0 else 0.0
        resultados.append({
            'hora': hora,
            'valor': valor,
            'ops': ops,
            'gan': gan,
            'per': per,
            'wr': wr,
            'profit': prof,
            'expectativa': exp,
        })
    return resultados

# ─────────────────────── OUTPUT ──────────────────────

ANCHOS = {'hora': 7, 'valor': 30, 'ops': 5, 'gan': 5, 'per': 5, 'wr': 8, 'profit': 9, 'exp': 10}

def header_tabla():
    return (
        "  {:<{}} {:<{}} {:>{}} {:>{}} {:>{}} {:>{}} {:>{}} {:>{}}".format(
            'HORA', ANCHOS['hora'], 'CAMPO', ANCHOS['valor'],
            'OPS', ANCHOS['ops'], 'GAN', ANCHOS['gan'], 'PER', ANCHOS['per'],
            'WR%', ANCHOS['wr'], 'PROFIT', ANCHOS['profit'], 'EXPECT/OP', ANCHOS['exp']
        )
    )

def fila_tabla(r):
    valor_str = r['valor'][:ANCHOS['valor']].ljust(ANCHOS['valor'])
    wr_str = "{:.1f}%".format(r['wr'])
    profit_str = "{:+.2f}".format(r['profit'])
    exp_str = "{:+.4f}".format(r['expectativa'])
    hora_str = (r['hora'] + 'xx').ljust(ANCHOS['hora'])
    return (
        "  {} {} {:>{}} {:>{}} {:>{}} {:>{}} {:>{}} {:>{}}".format(
            hora_str, valor_str,
            r['ops'], ANCHOS['ops'],
            r['gan'], ANCHOS['gan'],
            r['per'], ANCHOS['per'],
            wr_str, ANCHOS['wr'],
            profit_str, ANCHOS['profit'],
            exp_str, ANCHOS['exp']
        )
    )

def separador():
    return "  " + "-" * 85

def imprimir_seccion(nombre_campo, datos, min_ops, top, orden, ocultar_sin_dato):
    filtrados = [r for r in datos if r['ops'] >= min_ops]
    if not filtrados:
        print("\n  [Sin combinaciones con >= {} ops]\n".format(min_ops))
        return

    filtrados_sort = sorted(filtrados, key=lambda x: x[orden], reverse=True)
    modo = 'sin SIN_DATO' if ocultar_sin_dato else 'incluye SIN_DATO'

    print("\n" + "-" * 90)
    print("  HORA x {}".format(nombre_campo.upper()))
    print("  (min {} ops | orden: {} | {})".format(min_ops, orden, modo))
    print("-" * 90)

    print("\n  MEJORES (top {})".format(top))
    print(header_tabla())
    print(separador())
    for r in filtrados_sort[:top]:
        print(fila_tabla(r))

    print("\n  PEORES (top {})".format(top))
    print(header_tabla())
    print(separador())
    for r in reversed(filtrados_sort[-top:]):
        print(fila_tabla(r))

# ─────────────────────── RESUMEN ─────────────────────

BREAKEVEN = 55.56

def imprimir_resumen(todos_cruces, min_ops):
    print("\n" + "=" * 90)
    print("  RESUMEN EJECUTIVO -- Combinaciones ganadoras (WR > 55.56%)")
    print("  (min {} ops, todos los cruces)".format(min_ops))
    print("=" * 90)
    print(header_tabla())
    print(separador())

    ganadoras = []
    for nombre, datos in todos_cruces:
        filtrados = [r for r in datos if r['ops'] >= min_ops and r['wr'] > BREAKEVEN]
        for r in filtrados:
            ganadoras.append((nombre, r))

    ganadoras.sort(key=lambda x: x[1]['expectativa'], reverse=True)

    if not ganadoras:
        print("  No hay combinaciones ganadoras con los parametros dados.")
    else:
        for nombre, r in ganadoras:
            tag = "[{}]".format(nombre[:8])
            r2 = dict(r)
            r2['valor'] = "{} {}".format(tag, r['valor'])[:ANCHOS['valor']]
            print(fila_tabla(r2))
    print()

# ─────────────────────── EXPORT CSV ──────────────────

def exportar_csv(todos_cruces, min_ops, ruta_out='ranking_cruzado.csv'):
    filas = []
    for nombre, datos in todos_cruces:
        for r in datos:
            if r['ops'] >= min_ops:
                filas.append({
                    'cruce': nombre,
                    'hora': r['hora'],
                    'valor': r['valor'],
                    'ops': r['ops'],
                    'ganadas': r['gan'],
                    'perdidas': r['per'],
                    'win_rate': round(r['wr'], 2),
                    'profit_total': round(r['profit'], 4),
                    'expectativa': round(r['expectativa'], 4),
                })
    if not filas:
        print("  [Export CSV: sin datos para exportar]")
        return
    with open(ruta_out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=filas[0].keys())
        writer.writeheader()
        writer.writerows(filas)
    print("\n  CSV exportado -> {}  ({} combinaciones)".format(ruta_out, len(filas)))

# ─────────────────────── MAIN ────────────────────────

CAMPOS = [
    ('estructura',      'Estructura'),
    ('bos',             'BOS'),
    ('choch',           'CHOCH'),
    ('contexto_valido', 'Contexto Valido'),
]

def main():
    parser = argparse.ArgumentParser(description='Analizador cruzado Hora x Contexto')
    parser.add_argument('--csv',              default='operaciones_paper.csv', help='Ruta al CSV')
    parser.add_argument('--min-ops',          type=int, default=10,            help='Minimo ops por combinacion')
    parser.add_argument('--top',              type=int, default=5,             help='Top N mejores/peores')
    parser.add_argument('--orden',            default='expectativa',
                        choices=['expectativa', 'wr', 'profit'],               help='Criterio de ordenacion')
    parser.add_argument('--ocultar-sin-dato', action='store_true',             help='Excluir filas sin contexto')
    parser.add_argument('--solo-contexto',    action='store_true',             help='Usar solo ops con al menos un campo de contexto con dato')
    parser.add_argument('--export-csv',       action='store_true',             help='Exportar ranking_cruzado.csv')
    args = parser.parse_args()

    filas = leer_csv(args.csv)
    total = len(filas)

    if args.solo_contexto:
        filas = [f for f in filas if tiene_contexto(f)]

    usadas = len(filas)
    filtro_ctx = "solo-contexto ({}/{})".format(usadas, total) if args.solo_contexto else "todas ({})".format(total)

    print("\n" + "=" * 90)
    print("  ANALIZADOR CRUZADO -- Hora x Contexto")
    print("  Archivo : {}".format(args.csv))
    print("  Ops     : {}  |  min-ops: {}  |  top: {}  |  orden: {}".format(
        filtro_ctx, args.min_ops, args.top, args.orden))
    print("  Fecha   : {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print("=" * 90)

    todos_cruces = []
    for campo, nombre in CAMPOS:
        datos = calcular_cruce(filas, campo, args.ocultar_sin_dato)
        todos_cruces.append((nombre, datos))
        imprimir_seccion(nombre, datos, args.min_ops, args.top, args.orden, args.ocultar_sin_dato)

    imprimir_resumen(todos_cruces, args.min_ops)

    if args.export_csv:
        exportar_csv(todos_cruces, args.min_ops)

if __name__ == '__main__':
    main()
