from config import (
    MAX_OPERACIONES_ABIERTAS,
    MAX_PERDIDAS_CONSECUTIVAS,
    SCORE_MINIMO_OPERAR,
    USAR_FILTRO_VOLATILIDAD,
    MAX_RANGO_VELA,
    MAX_DRAWDOWN_PERMITIDO,
    ACTIVAR_COOLDOWN_DRAWDOWN,
    VELAS_COOLDOWN_DRAWDOWN
)

cooldown_activo = False
velas_restantes_cooldown = 0


def actualizar_cooldown():
    global cooldown_activo
    global velas_restantes_cooldown

    if not cooldown_activo:
        return

    velas_restantes_cooldown -= 1

    print(
        f"⏸ Cooldown activo "
        f"({velas_restantes_cooldown} velas restantes)"
    )

    if velas_restantes_cooldown <= 0:
        cooldown_activo = False
        print("✅ Cooldown finalizado")


def activar_cooldown():
    global cooldown_activo
    global velas_restantes_cooldown

    cooldown_activo = True
    velas_restantes_cooldown = VELAS_COOLDOWN_DRAWDOWN

    print(
        f"⛔ Cooldown activado "
        f"por {VELAS_COOLDOWN_DRAWDOWN} velas"
    )


def validar_riesgo(
    operaciones,
    perdidas_consecutivas,
    score_senal,
    vela,
    cuenta_paper=None,
    contexto_valido=False
):
    permitir = True
    motivos = []

    if cooldown_activo:
        permitir = False
        motivos.append("cooldown_drawdown")

    if len(operaciones) >= MAX_OPERACIONES_ABIERTAS:
        permitir = False
        motivos.append("max_operaciones_abiertas")

    if perdidas_consecutivas >= MAX_PERDIDAS_CONSECUTIVAS:
        permitir = False
        motivos.append("max_perdidas_consecutivas")

    if score_senal < SCORE_MINIMO_OPERAR:
        permitir = False
        motivos.append("score_insuficiente")

    if cuenta_paper is not None:
        drawdown_actual = cuenta_paper.get("drawdown", 0)

        if drawdown_actual >= MAX_DRAWDOWN_PERMITIDO:
            permitir = False
            motivos.append("max_drawdown_permitido")

            if ACTIVAR_COOLDOWN_DRAWDOWN and not cooldown_activo:
                activar_cooldown()

    if USAR_FILTRO_VOLATILIDAD:
        rango = vela["high"] - vela["low"]

        if rango > MAX_RANGO_VELA:
            permitir = False
            motivos.append("volatilidad_alta")

    motivo_bloqueo = "|".join(motivos) if motivos else ""

    return permitir, motivo_bloqueo


def actualizar_perdidas_consecutivas(
    perdidas_consecutivas,
    resultado
):
    if resultado == "CORRECTA":
        return 0

    return perdidas_consecutivas + 1
