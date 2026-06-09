def construir_vela(ticks_vela):
    open_price = ticks_vela[0]
    high_price = max(ticks_vela)
    low_price = min(ticks_vela)
    close_price = ticks_vela[-1]

    if close_price > open_price:
        tipo_vela = "ALCISTA"
    elif close_price < open_price:
        tipo_vela = "BAJISTA"
    else:
        tipo_vela = "NEUTRAL"

    return {
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "tipo": tipo_vela
    }
