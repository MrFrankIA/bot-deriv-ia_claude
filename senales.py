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
