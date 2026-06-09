from config import MIN_OPERACIONES_PATRON, WIN_RATE_MINIMO_PATRON


def analizar_contexto(velas):
    ultima = velas[-1]
    penultima = velas[-2]
    antepenultima = velas[-3]

    tipos = [antepenultima["tipo"], penultima["tipo"], ultima["tipo"]]
    patrones = [
        antepenultima["patron"],
        penultima["patron"],
        ultima["patron"]
    ]

    return tipos, patrones


def detectar_continuidad_impulso(velas):
    if len(velas) < 2:
        return "SIN_CONTINUIDAD"

    impulso_actual = velas[-1]["impulso"]
    impulso_anterior = velas[-2]["impulso"]

    if impulso_actual == "IMPULSO_ALCISTA" and impulso_anterior == "IMPULSO_ALCISTA":
        return "CONTINUIDAD_ALCISTA"

    if impulso_actual == "IMPULSO_BAJISTA" and impulso_anterior == "IMPULSO_BAJISTA":
        return "CONTINUIDAD_BAJISTA"

    return "SIN_CONTINUIDAD"


def generar_senal(
    tipos,
    patrones,
    continuidad,
    estructura="SIN_ESTRUCTURA",
    bos="SIN_BOS",
    sweep="SIN_SWEEP",
    contexto_valido=False
):
    senal_tecnica = "ESPERAR"

    tres_alcistas = tipos.count("ALCISTA") == 3
    tres_bajistas = tipos.count("BAJISTA") == 3

    if tres_alcistas:
        senal_tecnica = "COMPRAR"
    elif tres_bajistas:
        senal_tecnica = "VENDER"
    elif continuidad == "CONTINUIDAD_ALCISTA":
        senal_tecnica = "COMPRAR"
    elif continuidad == "CONTINUIDAD_BAJISTA":
        senal_tecnica = "VENDER"

    if patrones[-2] == "FUERTE_ALCISTA" and patrones[-1] == "DOJI":
        return "ESPERAR"

    if patrones[-2] == "FUERTE_BAJISTA" and patrones[-1] == "DOJI":
        return "ESPERAR"

    if senal_tecnica == "ESPERAR":
        return "ESPERAR"

    if senal_tecnica == "COMPRAR":
        if estructura == "ESTRUCTURA_BAJISTA":
            if bos != "BOS_ALCISTA" and sweep != "SWEEP_LOW":
                return "ESPERAR"

        if (
            estructura == "ESTRUCTURA_ALCISTA"
            or bos == "BOS_ALCISTA"
            or sweep == "SWEEP_LOW"
            or contexto_valido
        ):
            return "COMPRAR"

        return "ESPERAR"

    if senal_tecnica == "VENDER":
        if estructura == "ESTRUCTURA_ALCISTA":
            if bos != "BOS_BAJISTA" and sweep != "SWEEP_HIGH":
                return "ESPERAR"

        if (
            estructura == "ESTRUCTURA_BAJISTA"
            or bos == "BOS_BAJISTA"
            or sweep == "SWEEP_HIGH"
            or contexto_valido
        ):
            return "VENDER"

        return "ESPERAR"

    return "ESPERAR"


def obtener_tendencia_contexto(tipos):
    if tipos.count("ALCISTA") == 3:
        return "ALCISTA"

    if tipos.count("BAJISTA") == 3:
        return "BAJISTA"

    return "NEUTRAL"


def calcular_score(tipos, patron_actual, impulso, continuidad, estadisticas_patrones):
    score = 0

    if tipos.count("ALCISTA") == 3 or tipos.count("BAJISTA") == 3:
        score += 1

    if patron_actual in ["FUERTE_ALCISTA", "FUERTE_BAJISTA"]:
        score += 1

    if impulso in ["IMPULSO_ALCISTA", "IMPULSO_BAJISTA"]:
        score += 1

    if continuidad in ["CONTINUIDAD_ALCISTA", "CONTINUIDAD_BAJISTA"]:
        score += 1

    if patron_actual in estadisticas_patrones:
        datos = estadisticas_patrones[patron_actual]
        total = datos["correctas"] + datos["incorrectas"]

        if total >= 3:
            wr = (datos["correctas"] / total) * 100

            if wr >= 60:
                score += 1

    return score


def validar_patron(patron_actual, estadisticas_patrones):
    motivo = ""
    permitir = True

    if patron_actual in estadisticas_patrones:
        datos_patron = estadisticas_patrones[patron_actual]
        total_patron = datos_patron["correctas"] + datos_patron["incorrectas"]

        if total_patron >= MIN_OPERACIONES_PATRON:
            wr_patron = (datos_patron["correctas"] / total_patron) * 100
            print(f"📊 Win Rate {patron_actual}: {wr_patron:.2f}%")

            if wr_patron < WIN_RATE_MINIMO_PATRON:
                motivo = "patron_bajo_rendimiento_observado"
                permitir = True

    return permitir, motivo
