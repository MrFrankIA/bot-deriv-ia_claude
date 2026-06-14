import csv
import os
from config import (
    ARCHIVO_VELAS,
    ARCHIVO_VELAS_M1,
    ARCHIVO_SENALES,
    ARCHIVO_EVALUACIONES,
    ARCHIVO_OPERACIONES_PAPER,
    ARCHIVO_OPERACIONES_DEMO
)
import db


def _db_seguro(funcion, valores):
    """Persiste en SQLite sin que un fallo de DB rompa nunca el bot: el CSV ya
    se escribio antes y la ejecucion del contrato ya ocurrio. La DB es la copia
    analitica/operativa para el motor de aprendizaje."""
    try:
        funcion(valores)
    except Exception as error:
        print(f"⚠️ DB: no se persistio en SQLite ({error}); CSV intacto")


def crear_archivos_csv():
    # Inicializa tambien el esquema SQLite (idempotente). Si falla, el bot
    # sigue con CSV.
    try:
        db.inicializar_db()
    except Exception as error:
        print(f"⚠️ DB: no se pudo inicializar SQLite ({error}); se usa solo CSV")

    if not os.path.exists(ARCHIVO_VELAS):
        with open(ARCHIVO_VELAS, mode="w", newline="") as archivo:
            writer = csv.writer(archivo)
            writer.writerow([
                "hora", "open", "high", "low", "close",
                "tipo", "patron", "impulso", "continuidad"
            ])

    if not os.path.exists(ARCHIVO_VELAS_M1):
        with open(ARCHIVO_VELAS_M1, mode="w", newline="") as archivo:
            writer = csv.writer(archivo)
            writer.writerow([
                "hora_inicio",
                "hora_cierre",
                "open",
                "high",
                "low",
                "close",
                "tipo"
            ])

    if not os.path.exists(ARCHIVO_SENALES):
        with open(ARCHIVO_SENALES, mode="w", newline="") as archivo:
            writer = csv.writer(archivo)
            writer.writerow([
                "fecha",
                "hora",
                "senal_tecnica",
                "tendencia_contexto",
                "patron_actual",
                "impulso",
                "continuidad",
                "score_senal",
                "permitida",
                "motivo_bloqueo",
                "combinacion",
                "wr_combinacion",
                "estructura",
                "bos",
                "choch",
                "sweep",
                "mercado_lateral",
                "contexto_valido",
                "motivo_contexto"
            ])

    if not os.path.exists(ARCHIVO_EVALUACIONES):
        with open(ARCHIVO_EVALUACIONES, mode="w", newline="") as archivo:
            writer = csv.writer(archivo)
            writer.writerow([
                "hora", "senal", "precio_entrada", "precio_salida",
                "resultado", "patron", "impulso", "continuidad",
                "score_senal"
            ])

    if not os.path.exists(ARCHIVO_OPERACIONES_PAPER):
        with open(ARCHIVO_OPERACIONES_PAPER, mode="w", newline="") as archivo:
            writer = csv.writer(archivo)
            writer.writerow([
                "fecha",
                "hora",
                "senal",
                "resultado",
                "stake",
                "profit_loss",
                "balance",
                "equity_maxima",
                "drawdown",
                "patron",
                "impulso",
                "continuidad",
                "score_senal",
                "estructura",
                "bos",
                "choch",
                "sweep",
                "contexto_valido"
            ])

    if not os.path.exists(ARCHIVO_OPERACIONES_DEMO):
        with open(ARCHIVO_OPERACIONES_DEMO, mode="w", newline="") as archivo:
            writer = csv.writer(archivo)
            writer.writerow([
                "fecha",
                "hora",
                "senal",
                "resultado",
                "buy_price",
                "profit",
                "payout",
                "entry_spot",
                "exit_spot",
                "contract_id",
                "patron",
                "impulso",
                "continuidad",
                "score_senal",
                "estructura",
                "bos",
                "choch",
                "sweep",
                "contexto_valido"
            ])


def guardar_vela(hora, vela, continuidad):
    with open(ARCHIVO_VELAS, mode="a", newline="") as archivo:
        writer = csv.writer(archivo)
        writer.writerow([
            hora,
            vela["open"],
            vela["high"],
            vela["low"],
            vela["close"],
            vela["tipo"],
            vela["patron"],
            vela["impulso"],
            continuidad
        ])


def guardar_vela_m1(vela):
    with open(ARCHIVO_VELAS_M1, mode="a", newline="") as archivo:
        writer = csv.writer(archivo)
        writer.writerow([
            vela["hora_inicio"],
            vela["hora_cierre"],
            vela["open"],
            vela["high"],
            vela["low"],
            vela["close"],
            vela["tipo"]
        ])


def guardar_senal(
    fecha,
    hora,
    senal_tecnica,
    tendencia_contexto,
    patron_actual,
    impulso,
    continuidad,
    score_senal,
    permitida,
    motivo_bloqueo,
    combinacion_actual,
    wr_combinacion,
    estructura,
    bos,
    choch,
    sweep,
    mercado_lateral,
    contexto_valido,
    motivo_contexto
):
    with open(ARCHIVO_SENALES, mode="a", newline="") as archivo:
        writer = csv.writer(archivo)
        writer.writerow([
            fecha,
            hora,
            senal_tecnica,
            tendencia_contexto,
            patron_actual,
            impulso,
            continuidad,
            score_senal,
            permitida,
            motivo_bloqueo,
            combinacion_actual,
            wr_combinacion,
            estructura,
            bos,
            choch,
            sweep,
            mercado_lateral,
            contexto_valido,
            motivo_contexto
        ])

    _db_seguro(db.insertar_senal, [
        fecha, hora, senal_tecnica, tendencia_contexto, patron_actual,
        impulso, continuidad, score_senal, str(permitida), motivo_bloqueo,
        combinacion_actual, wr_combinacion, estructura, bos, choch, sweep,
        str(mercado_lateral), str(contexto_valido), motivo_contexto,
    ])


def guardar_evaluacion(
    hora,
    senal,
    precio_entrada,
    precio_salida,
    resultado,
    patron,
    impulso,
    continuidad,
    score_senal
):
    with open(ARCHIVO_EVALUACIONES, mode="a", newline="") as archivo:
        writer = csv.writer(archivo)
        writer.writerow([
            hora,
            senal,
            precio_entrada,
            precio_salida,
            resultado,
            patron,
            impulso,
            continuidad,
            score_senal
        ])


def guardar_operacion_paper(
    fecha,
    hora,
    senal,
    resultado,
    stake,
    profit_loss,
    balance,
    equity_maxima,
    drawdown,
    patron,
    impulso,
    continuidad,
    score_senal,
    estructura,
    bos,
    choch,
    sweep,
    contexto_valido
):
    with open(ARCHIVO_OPERACIONES_PAPER, mode="a", newline="") as archivo:
        writer = csv.writer(archivo)
        writer.writerow([
            fecha,
            hora,
            senal,
            resultado,
            stake,
            profit_loss,
            balance,
            equity_maxima,
            drawdown,
            patron,
            impulso,
            continuidad,
            score_senal,
            estructura,
            bos,
            choch,
            sweep,
            contexto_valido
        ])

    _db_seguro(db.insertar_operacion_paper, [
        fecha, hora, senal, resultado, stake, profit_loss, balance,
        equity_maxima, drawdown, patron, impulso, continuidad, score_senal,
        estructura, bos, choch, sweep, str(contexto_valido),
    ])


def guardar_operacion_demo(
    fecha,
    hora,
    senal,
    resultado,
    buy_price,
    profit,
    payout,
    entry_spot,
    exit_spot,
    contract_id,
    patron,
    impulso,
    continuidad,
    score_senal,
    estructura,
    bos,
    choch,
    sweep,
    contexto_valido
):
    with open(ARCHIVO_OPERACIONES_DEMO, mode="a", newline="") as archivo:
        writer = csv.writer(archivo)
        writer.writerow([
            fecha,
            hora,
            senal,
            resultado,
            buy_price,
            profit,
            payout,
            entry_spot,
            exit_spot,
            contract_id,
            patron,
            impulso,
            continuidad,
            score_senal,
            estructura,
            bos,
            choch,
            sweep,
            contexto_valido
        ])

    _db_seguro(db.insertar_operacion_demo, [
        fecha, hora, senal, resultado, buy_price, profit, payout,
        entry_spot, exit_spot, contract_id, patron, impulso, continuidad,
        score_senal, estructura, bos, choch, sweep, str(contexto_valido),
    ])
