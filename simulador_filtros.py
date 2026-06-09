#!/usr/bin/env python3
"""
simulador_filtros.py
Simula el impacto de filtrar horas en los resultados del sistema.
No modifica el bot ni ningun archivo existente.
"""

import csv
import argparse
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

def calcular_metricas(filas):
    ops = len(filas)
    if ops == 0:
        return {'ops': 0, 'gan': 0, 'per': 0, 'wr': 0.0, 'profit': 0.0, 'expectativa': 0.0}
    gan = sum(1 for f in filas if es_ganada(f))
    per = ops - gan
    profit = sum(profit_fila(f) for f in filas)
    wr = gan / ops * 100
    exp = profit / ops
    return {'ops': ops, 'gan': gan, 'per': per, 'wr': wr, 'profit': profit, 'expectativa': exp}

def filtrar_horas(filas, excluir=None, incluir=None):
    """Filtra filas por hora. excluir e incluir son sets de strings HH."""
    resultado = []
    for f in filas:
        h = extraer_hora(f)
        if h is None:
            continue
        if excluir and h in excluir:
            continue
        if incluir and h not in incluir:
            continue
        resultado.append(f)
    return resultado

# ─────────────────────── OUTPUT ──────────────────────

SEP = "=" * 75
SEP2 = "-" * 75

def fmt_metricas(m):
    return (
        "  Ops: {ops}  |  Gan: {gan}  |  Per: {per}  |  "
        "WR: {wr:.1f}%  |  Profit: {profit:+.2f}  |  Expect/Op: {expectativa:+.4f}"
    ).format(**m)

def fmt_delta(base, sim):
    d_ops     = sim['ops']     - base['ops']
    d_wr      = sim['wr']      - base['wr']
    d_profit  = sim['profit']  - base['profit']
    d_exp     = sim['expectativa'] - base['expectativa']
    ops_excl  = base['ops'] - sim['ops']

    signo = lambda x: "+" if x >= 0 else ""
    return (
        "  Delta vs actual:  "
        "ops excluidas={excl}  |  WR {s_wr}{d_wr:.2f}pp  |  "
        "Profit {s_p}{d_profit:.2f}  |  Expect/Op {s_e}{d_exp:.4f}"
    ).format(
        excl=ops_excl,
        s_wr=signo(d_wr), d_wr=d_wr,
        s_p=signo(d_profit), d_profit=d_profit,
        s_e=signo(d_exp), d_exp=d_exp,
    )

def imprimir_bloque(titulo, descripcion, m, base=None):
    print("\n" + SEP2)
    print("  " + titulo)
    print("  " + descripcion)
    print(SEP2)
    print(fmt_metricas(m))
    if base is not None:
        print(fmt_delta(base, m))

# ─────────────────────── MAIN ────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Simulador de filtros de hora')
    parser.add_argument('--csv',           default='operaciones_paper.csv', help='Ruta al CSV')
    parser.add_argument('--solo-contexto', action='store_true',             help='Usar solo ops con contexto')
    args = parser.parse_args()

    filas_raw = leer_csv(args.csv)
    total_raw = len(filas_raw)

    if args.solo_contexto:
        filas = [f for f in filas_raw if tiene_contexto(f)]
    else:
        filas = filas_raw

    # Excluir filas sin hora valida
    filas = [f for f in filas if extraer_hora(f) is not None]
    total_usadas = len(filas)

    modo_str = "solo-contexto ({}/{})".format(total_usadas, total_raw) if args.solo_contexto else "todas ({})".format(total_usadas)

    print("\n" + SEP)
    print("  SIMULADOR DE FILTROS DE HORA")
    print("  Archivo : {}".format(args.csv))
    print("  Ops     : {}".format(modo_str))
    print("  Fecha   : {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print(SEP)

    # [1] Global actual
    m_actual = calcular_metricas(filas)
    imprimir_bloque(
        "[1] RESULTADO GLOBAL ACTUAL",
        "Sin ningun filtro de hora aplicado",
        m_actual
    )

    # [2] Excluir horas malas: 18, 19, 20
    excl_2 = {'18', '19', '20'}
    f2 = filtrar_horas(filas, excluir=excl_2)
    m2 = calcular_metricas(f2)
    imprimir_bloque(
        "[2] SIMULACION -- Excluir horas malas (18, 19, 20)",
        "Se eliminan operaciones de las horas 18xx, 19xx, 20xx",
        m2, base=m_actual
    )

    # [3] Solo horas buenas: 23, 00, 03, 04
    incl_3 = {'23', '00', '03', '04'}
    f3 = filtrar_horas(filas, incluir=incl_3)
    m3 = calcular_metricas(f3)
    imprimir_bloque(
        "[3] SIMULACION -- Solo horas buenas (23, 00, 03, 04)",
        "Solo operaciones en las mejores horas identificadas",
        m3, base=m_actual
    )

    # [4] Solo madrugada: 00-05
    incl_4 = {'00', '01', '02', '03', '04', '05'}
    f4 = filtrar_horas(filas, incluir=incl_4)
    m4 = calcular_metricas(f4)
    imprimir_bloque(
        "[4] SIMULACION -- Solo madrugada (00, 01, 02, 03, 04, 05)",
        "Solo operaciones entre medianoche y las 06:00",
        m4, base=m_actual
    )

    # [5] Excluir horas criticas: 18, 19, 20, 22
    excl_5 = {'18', '19', '20', '22'}
    f5 = filtrar_horas(filas, excluir=excl_5)
    m5 = calcular_metricas(f5)
    imprimir_bloque(
        "[5] SIMULACION -- Excluir horas criticas (18, 19, 20, 22)",
        "Se eliminan las 4 horas con peor rendimiento historico",
        m5, base=m_actual
    )


    # [6] Solo horas candidatas + solo contexto: 23, 00, 03, 04
    incl_6 = {'23', '00', '03', '04'}
    # Siempre calcular base de solo-contexto para la segunda comparacion
    filas_ctx_base = [f for f in filas_raw if tiene_contexto(f) and extraer_hora(f) is not None]
    m_ctx_base = calcular_metricas(filas_ctx_base)

    f6 = [f for f in filas_raw if extraer_hora(f) in incl_6 and tiene_contexto(f)]
    m6 = calcular_metricas(f6)

    print("\n" + SEP2)
    print("  [6] SIMULACION -- Solo horas candidatas + solo contexto (23, 00, 03, 04)")
    print("  Horas: 23xx, 00xx, 03xx, 04xx | Solo ops con campo de contexto")
    print(SEP2)
    print(fmt_metricas(m6))
    print("  Delta vs global actual:   " + fmt_delta(m_actual, m6).replace("  Delta vs actual:  ", ""))
    print("  Delta vs solo-contexto:   " + fmt_delta(m_ctx_base, m6).replace("  Delta vs actual:  ", ""))

    print("\n" + SEP)
    print("  NOTA: Resultados locales son prueba tecnica.")
    print("  Ejecutar en VPS con CSV completo para validacion definitiva.")
    print(SEP + "\n")

if __name__ == '__main__':
    main()
