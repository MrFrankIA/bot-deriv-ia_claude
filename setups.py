from config import MIN_OPERACIONES_COMBINACION, WIN_RATE_MINIMO_COMBINACION


def crear_clave_combinacion(patron, impulso, continuidad):
    return f"{patron}|{impulso}|{continuidad}"


def validar_combinacion(
    patron,
    impulso,
    continuidad,
    estadisticas_combinaciones
):
    combinacion = crear_clave_combinacion(
        patron,
        impulso,
        continuidad
    )

    if combinacion not in estadisticas_combinaciones:
        return True, "", combinacion, None

    datos = estadisticas_combinaciones[combinacion]

    total = datos["correctas"] + datos["incorrectas"]

    if total < MIN_OPERACIONES_COMBINACION:
        return True, "", combinacion, None

    win_rate = (datos["correctas"] / total) * 100

    if win_rate < WIN_RATE_MINIMO_COMBINACION:
        return True, "combinacion_bajo_rendimiento", combinacion, win_rate

    return True, "", combinacion, win_rate