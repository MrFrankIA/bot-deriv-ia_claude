def detectar_mercado_lateral(velas, ventana=10):
    if len(velas) < ventana:
        return False

    ultimas = list(velas)[-ventana:]

    total_indecision = 0
    total_doji = 0

    for vela in ultimas:
        if vela.get("impulso") == "INDECISION":
            total_indecision += 1

        if vela.get("patron") == "DOJI":
            total_doji += 1

    porcentaje_indecision = total_indecision / ventana
    porcentaje_doji = total_doji / ventana

    return porcentaje_indecision >= 0.5 or porcentaje_doji >= 0.5


def evaluar_contexto_entrada(
    estructura,
    bos,
    sweep,
    mercado_lateral
):
    if mercado_lateral:
        return False, "mercado_lateral"

    if estructura == "ESTRUCTURA_ALCISTA":
        if bos == "BOS_ALCISTA" or sweep == "SWEEP_LOW":
            return True, ""

    if estructura == "ESTRUCTURA_BAJISTA":
        if bos == "BOS_BAJISTA" or sweep == "SWEEP_HIGH":
            return True, ""

    return False, "contexto_no_confirmado"
