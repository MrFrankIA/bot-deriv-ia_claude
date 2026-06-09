from datetime import datetime


def crear_estado_vela_tiempo():
    return {
        "minuto_actual": None,
        "open": None,
        "high": None,
        "low": None,
        "close": None
    }


def actualizar_vela_tiempo(
    estado,
    precio,
    duracion_segundos=None
):
    ahora = datetime.now()

    minuto_actual = ahora.replace(
        second=0,
        microsecond=0
    )

    if estado["minuto_actual"] is None:

        estado["minuto_actual"] = minuto_actual
        estado["open"] = precio
        estado["high"] = precio
        estado["low"] = precio
        estado["close"] = precio

        return None

    if minuto_actual == estado["minuto_actual"]:

        estado["high"] = max(
            estado["high"],
            precio
        )

        estado["low"] = min(
            estado["low"],
            precio
        )

        estado["close"] = precio

        return None

    vela_cerrada = {
        "hora_inicio":
            estado["minuto_actual"].strftime("%H:%M:%S"),

        "hora_cierre":
            minuto_actual.strftime("%H:%M:%S"),

        "open":
            estado["open"],

        "high":
            estado["high"],

        "low":
            estado["low"],

        "close":
            estado["close"]
    }

    if vela_cerrada["close"] > vela_cerrada["open"]:
        vela_cerrada["tipo"] = "ALCISTA"

    elif vela_cerrada["close"] < vela_cerrada["open"]:
        vela_cerrada["tipo"] = "BAJISTA"

    else:
        vela_cerrada["tipo"] = "NEUTRAL"

    estado["minuto_actual"] = minuto_actual

    estado["open"] = precio
    estado["high"] = precio
    estado["low"] = precio
    estado["close"] = precio

    return vela_cerrada