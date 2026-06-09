from estructura import obtener_ultimos_swings


def detectar_sweep_liquidez(velas):
    if len(velas) < 5:
        return "SIN_SWEEP"

    swings = obtener_ultimos_swings(velas)

    highs = swings["highs"]
    lows = swings["lows"]

    if not highs or not lows:
        return "SIN_SWEEP"

    ultima = list(velas)[-1]

    ultimo_high = highs[-1]["precio"]
    ultimo_low = lows[-1]["precio"]

    if ultima["high"] > ultimo_high and ultima["close"] < ultimo_high:
        return "SWEEP_HIGH"

    if ultima["low"] < ultimo_low and ultima["close"] > ultimo_low:
        return "SWEEP_LOW"

    return "SIN_SWEEP"
