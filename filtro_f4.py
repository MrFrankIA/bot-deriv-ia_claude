# -*- coding: utf-8 -*-
"""
Filtro F4: Bloquea dos patrones identificados como perdedores en 1.220 ops demo.

Hipotesis: Los contextos donde el bot pierde dinero de forma sistemática deben
bloquearse. El análisis muestra:
  - VENDER: WR 47.7% (siempre pierde, -49.2 USD netos)
  - BAJISTA|SIN_SWEEP: WR 47.3% (segundo peor, -33.8 USD)

F4 bloquea ambos. Resultado esperado (in-sample, n=593):
  WR 56.0%, esperanza +0.075/op, IC95 inferior 52.0% (toca break-even).

Reversible: flag FILTRO_F4_ACTIVO en config.
"""


def aplicar_filtro_f4(senal, estructura, sweep):
    """
    Retorna (bloqueado, motivo):
      - bloqueado=True si la senal debe rechazarse por F4.
      - motivo: razon descriptiva si se bloquea, "" si pasa.
    """
    # Bloqueo 1: VENDER siempre. Es sistematicamente perdedor (WR 47.7%).
    if senal == "VENDER":
        return True, "f4_vender_sistematico_perdedor"

    # Bloqueo 2: COMPRAR en BAJISTA sin barrera de liquidez (SIN_SWEEP).
    # Este es el segundo bucket con peor rendimiento (WR 47.3%, -33.8 USD).
    # La idea: en trending bajista sin barrido, el rebote es debil.
    if senal == "COMPRAR" and estructura == "ESTRUCTURA_BAJISTA" and sweep == "SIN_SWEEP":
        return True, "f4_comprar_bajista_sin_sweep_debil"

    return False, ""
