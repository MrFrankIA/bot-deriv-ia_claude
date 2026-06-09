def detectar_patron(vela):
    open_price = vela["open"]
    high_price = vela["high"]
    low_price = vela["low"]
    close_price = vela["close"]
    tipo_vela = vela["tipo"]

    cuerpo = abs(close_price - open_price)
    rango = high_price - low_price

    if rango == 0:
        return "DOJI"

    if cuerpo <= rango * 0.20:
        return "DOJI"

    if tipo_vela == "ALCISTA" and cuerpo >= rango * 0.70:
        return "FUERTE_ALCISTA"

    if tipo_vela == "BAJISTA" and cuerpo >= rango * 0.70:
        return "FUERTE_BAJISTA"

    return "NORMAL"


def clasificar_impulso(vela):
    open_price = vela["open"]
    high_price = vela["high"]
    low_price = vela["low"]
    close_price = vela["close"]

    cuerpo = abs(close_price - open_price)
    rango = high_price - low_price

    if rango == 0:
        return "INDECISION"

    proporcion_cuerpo = cuerpo / rango

    if proporcion_cuerpo <= 0.25:
        return "INDECISION"

    if close_price > open_price and proporcion_cuerpo >= 0.70:
        return "IMPULSO_ALCISTA"

    if close_price < open_price and proporcion_cuerpo >= 0.70:
        return "IMPULSO_BAJISTA"

    return "NORMAL"
