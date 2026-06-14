# -*- coding: utf-8 -*-
"""
Filtro F4: Bloquea tres patrones identificados como perdedores en ~1.233 ops demo.

Hipotesis: Los contextos donde el bot pierde dinero de forma sistemática deben
bloquearse. El análisis (validado contra el modulo real) muestra:
  - VENDER: WR 47.7% (siempre pierde, lado corto sin edge)
  - COMPRAR en BAJISTA|SIN_SWEEP: WR 47.3% (rebote debil en bajista sin barrido)
  - COMPRAR en SWEEP_HIGH: WR 38.3% (n=47, exp -0.265, el peor; comprar tras
    barrido de maximos = entrar justo antes de la reversion)

F4 bloquea los tres. Resultado esperado (validado, n=601):
  WR 55.7%, esperanza +0.070/op, IC95 [51.7, 59.7] (lower bound roza break-even).
Comparado con dejar pasar SWEEP_HIGH (n=648, exp +0.046): +0.024/op de mejora.

Reversible: flag FILTRO_F4_ACTIVO en config.
"""


def aplicar_filtro_f4(senal, estructura, sweep):
    """
    Retorna (bloqueado, motivo):
      - bloqueado=True si la senal debe rechazarse por F4.
      - motivo: razon descriptiva si se bloquea, "" si pasa.
    """
    # Bloqueo 1: VENDER siempre. El lado corto es sistematicamente perdedor
    # (WR 47.7%) por el drift alcista del sintetico.
    if senal == "VENDER":
        return True, "f4_vender_sistematico_perdedor"

    # Bloqueo 2: COMPRAR tras barrido de maximos (SWEEP_HIGH). Es el peor bucket
    # (WR 38.3%, exp -0.265): comprar fuerza tras un barrido de liquidez alta
    # suele ser entrar justo antes de la reversion bajista.
    if senal == "COMPRAR" and sweep == "SWEEP_HIGH":
        return True, "f4_comprar_sweep_high_reversion"

    # Bloqueo 3: COMPRAR en BAJISTA sin barrera de liquidez (SIN_SWEEP).
    # Segundo peor bucket (WR 47.3%): en trending bajista sin barrido, el
    # rebote es debil.
    if senal == "COMPRAR" and estructura == "ESTRUCTURA_BAJISTA" and sweep == "SIN_SWEEP":
        return True, "f4_comprar_bajista_sin_sweep_debil"

    return False, ""
