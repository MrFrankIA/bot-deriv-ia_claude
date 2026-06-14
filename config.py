import os

API_URL = "wss://api.derivws.com/trading/v1/options/ws/public"

ACTIVO = "R_75"

TICKS_POR_VELA = 10

ARCHIVO_VELAS = "velas.csv"
ARCHIVO_VELAS_M1 = "velas_m1.csv"
ARCHIVO_SENALES = "senales.csv"
ARCHIVO_EVALUACIONES = "evaluaciones.csv"
ARCHIVO_OPERACIONES_PAPER = "operaciones_paper.csv"
ARCHIVO_OPERACIONES_DEMO = "operaciones_demo.csv"

MAX_OPERACIONES_ABIERTAS = 3
MAX_PERDIDAS_CONSECUTIVAS = 999
# 1 vela = 10 ticks = MAXIMO real de un contrato Rise/Fall por ticks en Deriv.
# El contrato de 20 ticks (2 velas) NO existe; ademas 1 vela es el mejor
# horizonte observado en el analisis. Ver memoria hallazgos-estrategia.
VELAS_PARA_EVALUAR = 1

MIN_OPERACIONES_PATRON = 3
WIN_RATE_MINIMO_PATRON = 40

MIN_OPERACIONES_COMBINACION = 5
WIN_RATE_MINIMO_COMBINACION = 40

SCORE_MINIMO_OPERAR = 1

USAR_FILTRO_VOLATILIDAD = False
MAX_RANGO_VELA = 8

BALANCE_INICIAL = 1000
# Payout NETO real cotizado por la API de Deriv (proposal) para R_75 Rise/Fall
# a 10 ticks: payout bruto 1.92 / stake 1.00 = 0.92 neto. Break-even = 52.08% WR.
PAYOUT_SIMULADO = 0.92

USAR_STAKE_DINAMICO = True
RIESGO_POR_OPERACION = 0.001
STAKE_MINIMO = 1
STAKE_MAXIMO = 5
STAKE_VIRTUAL = 1

MAX_DRAWDOWN_PERMITIDO = 100

ACTIVAR_COOLDOWN_DRAWDOWN = True
VELAS_COOLDOWN_DRAWDOWN = 5

ACTIVAR_FILTRO_CONTEXTO = False

# =========================
# TIME CANDLES
# =========================

USAR_VELAS_TIEMPO = True
SEGUNDOS_VELA_M1 = 60

# =========================
# FILTRO V5 CONTEXTUAL-HORARIO (EXPERIMENTAL)
# =========================
# Bloquea: ESTRUCTURA_ALCISTA + SIN_BOS en horas de bajo rendimiento.
# Simulacion (1674 ops): elimina 129 ops, mejora WR 49.76->51.20%,
# profit +53.43, expect -0.10427->-0.07839, drawdown 180.34->127.11.
# Ratio perdedoras evitadas / ganadoras sacrificadas: 2.59:1.
# Dejar en False hasta validar en VPS con datos reales.
FILTRO_V5_ACTIVO = False
HORAS_V5_BLOQUEADAS = {"02", "03", "09", "10", "14", "18", "19", "20"}

# =========================
# EXPIRACION DINAMICA (EXPERIMENTAL)
# =========================
# Hibrido: LATERAL=1 vela / resto=4 velas.
# Simulacion (2128 ops): WR 53.05%, exp -0.04502, DD 125.00 vs actual DD 200.40.
# Dejar en False hasta validar en VPS con datos reales.
EXPIRACION_DINAMICA_ACTIVA = False
VELAS_EVALUAR_LATERAL = 1
VELAS_EVALUAR_RESTO   = 4

# =========================
# FILTRO F4: Bloquear patrones perdedores (EXPERIMENTAL)
# =========================
# Análisis de ~1.233 ops demo identificó tres buckets sistematicamente perdedores
# (validado contra el modulo real filtro_f4.py):
#   - VENDER: WR 47.7% (lado corto sin edge)
#   - COMPRAR en SWEEP_HIGH: WR 38.3% (exp -0.265, el peor)
#   - COMPRAR en BAJISTA|SIN_SWEEP: WR 47.3% (rebote debil)
# F4 los bloquea. Resultado esperado (validado, n=601): WR 55.7%, exp +0.070/op,
# IC95 [51.7, 59.7]. Reversible: cambiar a False + reiniciar bot.
# MODO SOMBRA: F4 solo filtra la ejecucion DEMO real; el paper sigue operando
# TODO (shadow completo) para conservar datos de los buckets descartados y
# alimentar el motor de aprendizaje. Dashboard: demo=filtrado vs paper=todo.
FILTRO_F4_ACTIVO = True

# =========================
# EJECUCION DEMO (EXPERIMENTAL)
# =========================
# Por defecto el bot solo SIMULA (paper). Para operar en cuenta DEMO real de
# Deriv: poner MODO_EJECUCION = "demo" Y exportar DERIV_API_TOKEN_DEMO en el
# entorno (nunca en el repo; usar .env gitignored / EnvironmentFile de systemd).
# SOLO_CUENTA_VIRTUAL rechaza tokens de cuenta real como guard de seguridad.
MODO_EJECUCION = os.environ.get("MODO_EJECUCION", "paper")  # "paper" | "demo"
DERIV_APP_ID = os.environ.get("DERIV_APP_ID", "")
DERIV_API_TOKEN = os.environ.get("DERIV_API_TOKEN_DEMO", "")
DURACION_TICKS = 10            # 1 vela = 10 ticks (maximo real Rise/Fall ticks)
MONTO_CONTRATO = 1            # stake por operacion en demo
SOLO_CUENTA_VIRTUAL = True    # aborta si la cuenta autorizada no es virtual
