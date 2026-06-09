API_URL = "wss://api.derivws.com/trading/v1/options/ws/public"

ACTIVO = "R_75"

TICKS_POR_VELA = 10

ARCHIVO_VELAS = "velas.csv"
ARCHIVO_VELAS_M1 = "velas_m1.csv"
ARCHIVO_SENALES = "senales.csv"
ARCHIVO_EVALUACIONES = "evaluaciones.csv"
ARCHIVO_OPERACIONES_PAPER = "operaciones_paper.csv"

MAX_OPERACIONES_ABIERTAS = 3
MAX_PERDIDAS_CONSECUTIVAS = 999
VELAS_PARA_EVALUAR = 2

MIN_OPERACIONES_PATRON = 3
WIN_RATE_MINIMO_PATRON = 40

MIN_OPERACIONES_COMBINACION = 5
WIN_RATE_MINIMO_COMBINACION = 40

SCORE_MINIMO_OPERAR = 1

USAR_FILTRO_VOLATILIDAD = False
MAX_RANGO_VELA = 8

BALANCE_INICIAL = 1000
PAYOUT_SIMULADO = 0.80

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
