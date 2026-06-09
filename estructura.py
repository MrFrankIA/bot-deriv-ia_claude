def detectar_swing_high(velas, indice):
    if indice <= 0 or indice >= len(velas) - 1:
        return False

    anterior = velas[indice - 1]
    actual = velas[indice]
    siguiente = velas[indice + 1]

    return actual["high"] > anterior["high"] and actual["high"] > siguiente["high"]


def detectar_swing_low(velas, indice):
    if indice <= 0 or indice >= len(velas) - 1:
        return False

    anterior = velas[indice - 1]
    actual = velas[indice]
    siguiente = velas[indice + 1]

    return actual["low"] < anterior["low"] and actual["low"] < siguiente["low"]


def obtener_ultimos_swings(velas, cantidad=5):
    velas_lista = list(velas)

    swings_high = []
    swings_low = []

    for i in range(1, len(velas_lista) - 1):
        if detectar_swing_high(velas_lista, i):
            swings_high.append({
                "indice": i,
                "precio": velas_lista[i]["high"]
            })

        if detectar_swing_low(velas_lista, i):
            swings_low.append({
                "indice": i,
                "precio": velas_lista[i]["low"]
            })

    return {
        "highs": swings_high[-cantidad:],
        "lows": swings_low[-cantidad:]
    }


def detectar_estructura(velas):
    swings = obtener_ultimos_swings(velas)

    highs = swings["highs"]
    lows = swings["lows"]

    if len(highs) < 2 or len(lows) < 2:
        return "SIN_ESTRUCTURA"

    ultimo_high = highs[-1]["precio"]
    high_anterior = highs[-2]["precio"]

    ultimo_low = lows[-1]["precio"]
    low_anterior = lows[-2]["precio"]

    if ultimo_high > high_anterior and ultimo_low > low_anterior:
        return "ESTRUCTURA_ALCISTA"

    if ultimo_high < high_anterior and ultimo_low < low_anterior:
        return "ESTRUCTURA_BAJISTA"

    return "ESTRUCTURA_LATERAL"

def detectar_bos(velas):
    if len(velas) < 6:
        return "SIN_BOS"

    swings = obtener_ultimos_swings(velas)

    highs = swings["highs"]
    lows = swings["lows"]

    if len(highs) < 2 or len(lows) < 2:
        return "SIN_BOS"

    ultima_vela = list(velas)[-1]

    ultimo_high = highs[-1]["precio"]
    high_anterior = highs[-2]["precio"]

    ultimo_low = lows[-1]["precio"]
    low_anterior = lows[-2]["precio"]

    estructura_alcista = (
        ultimo_high > high_anterior
        and ultimo_low > low_anterior
    )

    estructura_bajista = (
        ultimo_high < high_anterior
        and ultimo_low < low_anterior
    )

    if (
        estructura_alcista
        and ultima_vela["close"] > ultimo_high
    ):
        return "BOS_ALCISTA"

    if (
        estructura_bajista
        and ultima_vela["close"] < ultimo_low
    ):
        return "BOS_BAJISTA"

    return "SIN_BOS"

def detectar_choch(velas):
    if len(velas) < 6:
        return "SIN_CHOCH"

    swings = obtener_ultimos_swings(velas)

    highs = swings["highs"]
    lows = swings["lows"]

    if len(highs) < 2 or len(lows) < 2:
        return "SIN_CHOCH"

    ultima_vela = list(velas)[-1]

    ultimo_high = highs[-1]["precio"]
    high_anterior = highs[-2]["precio"]

    ultimo_low = lows[-1]["precio"]
    low_anterior = lows[-2]["precio"]

    venia_alcista = (
        ultimo_high > high_anterior
        and ultimo_low > low_anterior
    )

    venia_bajista = (
        ultimo_high < high_anterior
        and ultimo_low < low_anterior
    )

    if (
        venia_alcista
        and ultima_vela["close"] < ultimo_low
    ):
        return "CHOCH_BAJISTA"

    if (
        venia_bajista
        and ultima_vela["close"] > ultimo_high
    ):
        return "CHOCH_ALCISTA"

    return "SIN_CHOCH"