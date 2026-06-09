from config import (
    BALANCE_INICIAL,
    STAKE_VIRTUAL,
    PAYOUT_SIMULADO,
    USAR_STAKE_DINAMICO,
    RIESGO_POR_OPERACION,
    STAKE_MINIMO,
    STAKE_MAXIMO
)


def crear_cuenta_paper():
    return {
        "balance": BALANCE_INICIAL,
        "equity_maxima": BALANCE_INICIAL,
        "drawdown": 0,
        "operaciones": 0,
        "ganadas": 0,
        "perdidas": 0,
        "profit_total": 0
    }




def recuperar_cuenta_paper(ruta_csv, reset_drawdown_operativo=True):
    import csv as _csv
    import os

    if not os.path.exists(ruta_csv):
        return crear_cuenta_paper()

    balance       = BALANCE_INICIAL
    equity_maxima = BALANCE_INICIAL
    operaciones   = 0
    ganadas       = 0
    perdidas      = 0
    profit_total  = 0.0

    try:
        with open(ruta_csv, newline='', encoding='utf-8') as f:
            reader = _csv.DictReader(f)
            for fila in reader:
                valor_profit = fila.get('profit_loss', '')
                if not valor_profit or not valor_profit.strip():
                    continue
                try:
                    profit_loss = float(valor_profit)
                except (ValueError, TypeError):
                    continue
                resultado = (fila.get('resultado', '') or '').strip().upper()
                balance       = round(balance + profit_loss, 2)
                profit_total  = round(profit_total + profit_loss, 2)
                operaciones  += 1
                if resultado == 'CORRECTA':
                    ganadas += 1
                else:
                    perdidas += 1
                if balance > equity_maxima:
                    equity_maxima = balance
    except Exception:
        return crear_cuenta_paper()

    if operaciones == 0:
        return crear_cuenta_paper()

    if reset_drawdown_operativo:
        equity_maxima_ret = balance
        drawdown_ret = 0.0
    else:
        equity_maxima_ret = equity_maxima
        drawdown_ret = round(equity_maxima - balance, 2)

    return {
        'balance':       balance,
        'equity_maxima': equity_maxima_ret,
        'drawdown':      drawdown_ret,
        'operaciones':   operaciones,
        'ganadas':       ganadas,
        'perdidas':      perdidas,
        'profit_total':  profit_total,
    }

def calcular_stake(cuenta):
    if not USAR_STAKE_DINAMICO:
        return STAKE_VIRTUAL

    stake = cuenta["balance"] * RIESGO_POR_OPERACION

    if stake < STAKE_MINIMO:
        stake = STAKE_MINIMO

    if stake > STAKE_MAXIMO:
        stake = STAKE_MAXIMO

    return round(stake, 2)


def calcular_resultado_paper(cuenta, resultado):
    stake = calcular_stake(cuenta)

    if resultado == "CORRECTA":
        profit_loss = stake * PAYOUT_SIMULADO
    else:
        profit_loss = -stake

    return stake, round(profit_loss, 2)


def actualizar_cuenta_paper(cuenta, resultado):
    stake, profit_loss = calcular_resultado_paper(
        cuenta,
        resultado
    )

    cuenta["balance"] = round(
        cuenta["balance"] + profit_loss,
        2
    )

    cuenta["profit_total"] = round(
        cuenta["profit_total"] + profit_loss,
        2
    )

    cuenta["operaciones"] += 1

    if resultado == "CORRECTA":
        cuenta["ganadas"] += 1
    else:
        cuenta["perdidas"] += 1

    if cuenta["balance"] > cuenta["equity_maxima"]:
        cuenta["equity_maxima"] = cuenta["balance"]

    cuenta["drawdown"] = round(
        cuenta["equity_maxima"] - cuenta["balance"],
        2
    )

    return stake, profit_loss


def mostrar_cuenta_paper(cuenta):
    print("\n💼 PAPER TRADING")
    print(f"💰 Balance virtual: {cuenta['balance']}")
    print(f"📈 Profit total: {cuenta['profit_total']}")
    print(f"📌 Operaciones paper: {cuenta['operaciones']}")
    print(f"✅ Ganadas: {cuenta['ganadas']}")
    print(f"❌ Perdidas: {cuenta['perdidas']}")
    print(f"📉 Drawdown: {cuenta['drawdown']}")
    print(f"🎲 Próximo stake estimado: {calcular_stake(cuenta)}")
