def generar_senal_pullback(
    tipos,
    patrones,
    impulso,
    continuidad,
    estructura,
    bos,
    sweep,
    contexto_valido
):
    if len(tipos) < 3:
        return "ESPERAR"

    tipo_actual = tipos[-1]
    tipo_anterior = tipos[-2]
    patron_actual = patrones[-1]

    if patron_actual == "DOJI":
        return "ESPERAR"

    contexto_alcista = (
        estructura == "ESTRUCTURA_ALCISTA"
        or bos == "BOS_ALCISTA"
        or sweep == "SWEEP_LOW"
    )

    contexto_bajista = (
        estructura == "ESTRUCTURA_BAJISTA"
        or bos == "BOS_BAJISTA"
        or sweep == "SWEEP_HIGH"
    )

    hubo_retroceso_bajista = (
        tipo_anterior != "ALCISTA"
    )

    hubo_retroceso_alcista = (
        tipo_anterior != "BAJISTA"
    )

    confirmacion_alcista = (
        tipo_actual == "ALCISTA"
        and impulso == "IMPULSO_ALCISTA"
        and patron_actual in ["FUERTE_ALCISTA", "NORMAL"]
    )

    confirmacion_bajista = (
        tipo_actual == "BAJISTA"
        and impulso == "IMPULSO_BAJISTA"
        and patron_actual in ["FUERTE_BAJISTA", "NORMAL"]
    )

    if (
        contexto_alcista
        and hubo_retroceso_bajista
        and confirmacion_alcista
    ):
        return "COMPRAR"

    if (
        contexto_bajista
        and hubo_retroceso_alcista
        and confirmacion_bajista
    ):
        return "VENDER"

    return "ESPERAR"