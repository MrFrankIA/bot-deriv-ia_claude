# -*- coding: utf-8 -*-
"""
Capa de ejecucion DEMO sobre Deriv (contrato Rise/Fall por ticks en R_75).

Flujo por operacion: authorize -> proposal -> buy -> seguir hasta settlement.

SEGURIDAD:
  - Solo opera si la cuenta autorizada es VIRTUAL (demo). Si el token pertenece
    a una cuenta real y SOLO_CUENTA_VIRTUAL=True, aborta y NO compra.
  - El token se lee de la variable de entorno DERIV_API_TOKEN_DEMO, nunca del
    repositorio.

AISLAMIENTO:
  - main.py solo invoca este modulo si MODO_EJECUCION == "demo".
  - Abre y cierra su propia conexion WebSocket, sin estado compartido con el
    loop de ticks que genera senales.
"""
import sys
import json
import asyncio
import websockets

from config import (
    ACTIVO,
    DERIV_APP_ID,
    DERIV_API_TOKEN,
    DURACION_TICKS,
    MONTO_CONTRATO,
    SOLO_CUENTA_VIRTUAL,
)

WS_URL = "wss://ws.derivws.com/websockets/v3?app_id={}".format(DERIV_APP_ID)

SENAL_A_CONTRATO = {
    "COMPRAR": "CALL",
    "VENDER": "PUT",
}


class ErrorEjecucion(Exception):
    pass


async def _enviar_recibir(ws, payload, esperado, timeout=20):
    """Envia payload y espera el primer mensaje cuyo msg_type sea 'esperado'."""
    await ws.send(json.dumps(payload))
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        data = json.loads(raw)
        if data.get("error"):
            raise ErrorEjecucion(data["error"].get("message", "error desconocido"))
        if data.get("msg_type") == esperado:
            return data


async def operar_demo(senal):
    """
    Ejecuta UNA operacion demo para la senal dada ('COMPRAR'/'VENDER').

    Devuelve un dict con el resultado REAL del contrato, o None si la senal no
    es operable. Lanza ErrorEjecucion ante cualquier problema (token ausente,
    cuenta no virtual, error de API).
    """
    contract_type = SENAL_A_CONTRATO.get(senal)
    if contract_type is None:
        return None
    if not DERIV_API_TOKEN:
        raise ErrorEjecucion("DERIV_API_TOKEN_DEMO no configurado en el entorno")

    async with websockets.connect(WS_URL) as ws:
        # 1) authorize + guard de cuenta virtual
        auth = await _enviar_recibir(ws, {"authorize": DERIV_API_TOKEN}, "authorize")
        info = auth.get("authorize", {})
        es_virtual = info.get("is_virtual", 0)
        loginid = info.get("loginid", "?")
        if SOLO_CUENTA_VIRTUAL and not es_virtual:
            raise ErrorEjecucion(
                "ABORTADO: la cuenta {} NO es virtual (demo). No se opera.".format(loginid)
            )

        # 2) proposal (cotizacion)
        prop = await _enviar_recibir(ws, {
            "proposal": 1,
            "amount": MONTO_CONTRATO,
            "basis": "stake",
            "contract_type": contract_type,
            "currency": info.get("currency", "USD"),
            "duration": DURACION_TICKS,
            "duration_unit": "t",
            "symbol": ACTIVO,
        }, "proposal")
        proposal_id = prop["proposal"]["id"]
        ask_price = prop["proposal"]["ask_price"]

        # 3) buy (compra real en demo)
        compra = await _enviar_recibir(ws, {
            "buy": proposal_id,
            "price": ask_price,
        }, "buy")
        contract_id = compra["buy"]["contract_id"]
        buy_price = compra["buy"]["buy_price"]

        # 4) seguir el contrato hasta settlement
        await ws.send(json.dumps({
            "proposal_open_contract": 1,
            "contract_id": contract_id,
            "subscribe": 1,
        }))
        resultado = None
        while resultado is None:
            raw = await asyncio.wait_for(ws.recv(), timeout=120)
            data = json.loads(raw)
            if data.get("error"):
                raise ErrorEjecucion(data["error"].get("message", "error en seguimiento"))
            if data.get("msg_type") != "proposal_open_contract":
                continue
            poc = data.get("proposal_open_contract", {})
            if poc.get("is_sold"):
                profit = float(poc.get("profit", 0.0))
                resultado = {
                    "contract_id": contract_id,
                    "senal": senal,
                    "contract_type": contract_type,
                    "buy_price": float(buy_price),
                    "payout": float(poc.get("payout", 0.0)),
                    "profit": round(profit, 2),
                    "status": poc.get("status", ""),
                    "resultado": "CORRECTA" if profit > 0 else "INCORRECTA",
                    "entry_spot": poc.get("entry_spot"),
                    "exit_spot": poc.get("exit_spot"),
                }
        return resultado


if __name__ == "__main__":
    # Prueba aislada: ejecuta UNA operacion demo y muestra el resultado real.
    #   python ejecucion.py COMPRAR
    #   python ejecucion.py VENDER
    senal_test = sys.argv[1].upper() if len(sys.argv) > 1 else "COMPRAR"
    print("Probando operacion demo: {} {} ({} ticks)".format(senal_test, ACTIVO, DURACION_TICKS))
    try:
        res = asyncio.run(operar_demo(senal_test))
        print("RESULTADO:")
        print(json.dumps(res, indent=2))
    except Exception as error:
        print("ERROR: {}".format(error))
        sys.exit(1)
