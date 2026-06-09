# -*- coding: utf-8 -*-
"""
Capa de ejecucion DEMO sobre la API NUEVA de Deriv (Options v1).

Flujo (confirmado contra el servidor 2026-06-09):
  1. GET  /trading/v1/options/accounts            -> lista cuentas (Bearer PAT + Deriv-App-ID)
  2. elegir la cuenta account_type == "demo"
  3. POST /trading/v1/options/accounts/{id}/otp   -> url ws autenticada (otp de un solo uso)
  4. conectar a esa url y enviar proposal -> buy -> seguir proposal_open_contract

SEGURIDAD:
  - SOLO opera la cuenta cuyo account_type == "demo". Si SOLO_CUENTA_VIRTUAL=True
    y no hay cuenta demo, aborta y NO compra (jamas toca la cuenta real "ROT...").
  - Credenciales leidas del entorno (DERIV_API_TOKEN_DEMO, DERIV_APP_ID), nunca
    del repositorio.

AISLAMIENTO:
  - main.py solo invoca este modulo si MODO_EJECUCION == "demo".
  - Abre/cierra su propia conexion, sin estado compartido con el loop de ticks.
"""
import sys
import json
import asyncio
import urllib.request
import urllib.error

import websockets

from config import (
    ACTIVO,
    DERIV_APP_ID,
    DERIV_API_TOKEN,
    DURACION_TICKS,
    MONTO_CONTRATO,
    SOLO_CUENTA_VIRTUAL,
)

REST_BASE = "https://api.derivws.com/trading/v1/options"

SENAL_A_CONTRATO = {
    "COMPRAR": "CALL",
    "VENDER": "PUT",
}


class ErrorEjecucion(Exception):
    pass


def _rest(method, path, body=None):
    """Llamada REST autenticada. Bloqueante; se invoca via asyncio.to_thread."""
    if not DERIV_API_TOKEN:
        raise ErrorEjecucion("DERIV_API_TOKEN_DEMO no configurado en el entorno")
    if not DERIV_APP_ID:
        raise ErrorEjecucion("DERIV_APP_ID no configurado en el entorno")
    url = REST_BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + DERIV_API_TOKEN)
    req.add_header("Deriv-App-ID", DERIV_APP_ID)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise ErrorEjecucion("REST {} {} -> {}: {}".format(
            method, path, e.code, e.read().decode()[:200]))


async def _obtener_url_ws():
    """Autentica, elige la cuenta demo y devuelve la url ws con OTP."""
    cuentas = (await asyncio.to_thread(_rest, "GET", "/accounts")).get("data", [])
    demo = next((c for c in cuentas if c.get("account_type") == "demo"), None)
    if demo is None:
        if SOLO_CUENTA_VIRTUAL:
            raise ErrorEjecucion("ABORTADO: no se encontro cuenta demo; no se opera.")
        demo = cuentas[0] if cuentas else None
    if demo is None:
        raise ErrorEjecucion("No hay cuentas disponibles para el token.")
    account_id = demo["account_id"]
    resp = await asyncio.to_thread(_rest, "POST", "/accounts/{}/otp".format(account_id))
    ws_url = (resp.get("data") or {}).get("url")
    if not ws_url:
        raise ErrorEjecucion("La respuesta de OTP no incluyo url de ws.")
    return account_id, ws_url


async def _esperar(ws, msg_type, timeout=30):
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        d = json.loads(raw)
        if d.get("error"):
            raise ErrorEjecucion(d["error"].get("message", "error de API"))
        if d.get("msg_type") == msg_type:
            return d


async def operar_demo(senal):
    """
    Ejecuta UNA operacion demo para la senal ('COMPRAR'/'VENDER').
    Devuelve un dict con el resultado REAL del contrato, o None si la senal
    no es operable. Lanza ErrorEjecucion ante cualquier fallo.
    """
    contract_type = SENAL_A_CONTRATO.get(senal)
    if contract_type is None:
        return None

    account_id, ws_url = await _obtener_url_ws()

    async with websockets.connect(ws_url) as ws:
        # proposal
        await ws.send(json.dumps({
            "proposal": 1,
            "amount": MONTO_CONTRATO,
            "basis": "stake",
            "contract_type": contract_type,
            "currency": "USD",
            "duration": DURACION_TICKS,
            "duration_unit": "t",
            "underlying_symbol": ACTIVO,
            "req_id": 1,
        }))
        prop = await _esperar(ws, "proposal")
        proposal_id = prop["proposal"]["id"]
        ask_price = prop["proposal"]["ask_price"]

        # buy
        await ws.send(json.dumps({"buy": proposal_id, "price": ask_price, "req_id": 2}))
        compra = await _esperar(ws, "buy")
        contract_id = compra["buy"]["contract_id"]
        buy_price = compra["buy"]["buy_price"]

        # seguir hasta settlement
        await ws.send(json.dumps({
            "proposal_open_contract": 1,
            "contract_id": contract_id,
            "subscribe": 1,
            "req_id": 3,
        }))
        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout=120)
            d = json.loads(raw)
            if d.get("error"):
                raise ErrorEjecucion(d["error"].get("message", "error en seguimiento"))
            if d.get("msg_type") != "proposal_open_contract":
                continue
            poc = d.get("proposal_open_contract", {})
            if poc.get("is_sold"):
                profit = float(poc.get("profit", 0.0))
                return {
                    "account_id": account_id,
                    "contract_id": contract_id,
                    "senal": senal,
                    "contract_type": contract_type,
                    "buy_price": float(buy_price),
                    "payout": float(poc.get("payout", 0.0)),
                    "profit": round(profit, 2),
                    "status": poc.get("status", ""),
                    "resultado": "CORRECTA" if poc.get("status") == "won" else "INCORRECTA",
                    "entry_spot": poc.get("entry_spot"),
                    "exit_spot": poc.get("exit_spot"),
                }


if __name__ == "__main__":
    # Prueba aislada: ejecuta UNA operacion demo y muestra el resultado real.
    #   python ejecucion.py COMPRAR
    senal_test = sys.argv[1].upper() if len(sys.argv) > 1 else "COMPRAR"
    print("Probando operacion demo: {} {} ({} ticks)".format(senal_test, ACTIVO, DURACION_TICKS))
    try:
        res = asyncio.run(operar_demo(senal_test))
        print("RESULTADO:")
        print(json.dumps(res, indent=2))
    except Exception as error:
        print("ERROR: {}".format(error))
        sys.exit(1)
