import asyncio
import json
import websockets
from collections import deque
from datetime import datetime

from config import (
    API_URL,
    ACTIVO,
    TICKS_POR_VELA,
    ACTIVAR_FILTRO_CONTEXTO,
    FILTRO_V5_ACTIVO,
    HORAS_V5_BLOQUEADAS,
    USAR_VELAS_TIEMPO,
    ARCHIVO_OPERACIONES_PAPER,
    VELAS_PARA_EVALUAR,
    EXPIRACION_DINAMICA_ACTIVA,
    VELAS_EVALUAR_LATERAL,
    VELAS_EVALUAR_RESTO,
    SEGUNDOS_VELA_M1
)
from almacenamiento import (
    crear_archivos_csv,
    guardar_vela,
    guardar_vela_m1,
    guardar_senal,
    guardar_evaluacion,
    guardar_operacion_paper
)
from velas import construir_vela
from velas_tiempo import (
    crear_estado_vela_tiempo,
    actualizar_vela_tiempo
)
from patrones import detectar_patron, clasificar_impulso
from senales import (
    analizar_contexto,
    detectar_continuidad_impulso,
    generar_senal,
    obtener_tendencia_contexto,
    calcular_score,
    validar_patron
)
from estrategia_pullback import generar_senal_pullback
from evaluador import evaluar_operaciones
from estadisticas import actualizar_estadisticas, mostrar_estadisticas
from riesgo import (
    validar_riesgo,
    actualizar_perdidas_consecutivas,
    actualizar_cooldown
)
from memoria import cargar_memoria
from setups import validar_combinacion, crear_clave_combinacion
from paper_trading import (
    crear_cuenta_paper,
    recuperar_cuenta_paper,
    actualizar_cuenta_paper,
    mostrar_cuenta_paper
)
from estructura import detectar_estructura, detectar_bos, detectar_choch
from liquidez import detectar_sweep_liquidez
from filtro_contexto import (
    detectar_mercado_lateral,
    evaluar_contexto_entrada
)


ticks_vela = []
velas = deque(maxlen=50)
velas_m1 = deque(maxlen=200)
operaciones = []
contador_velas = 0

estado_vela_m1 = crear_estado_vela_tiempo()

estadisticas, estadisticas_patrones, perdidas_consecutivas = cargar_memoria()
estadisticas_combinaciones = {}

cuenta_paper = recuperar_cuenta_paper(ARCHIVO_OPERACIONES_PAPER, reset_drawdown_operativo=True)


async def escuchar_ticks():
    global perdidas_consecutivas
    global contador_velas

    crear_archivos_csv()

    async with websockets.connect(API_URL) as websocket:
        print(f"✅ Escuchando mercado: {ACTIVO}")

        solicitud = {
            "ticks": ACTIVO,
            "subscribe": 1
        }

        await websocket.send(json.dumps(solicitud))

        while True:
            respuesta = await websocket.recv()
            datos = json.loads(respuesta)

            if "tick" not in datos:
                continue

            precio = float(datos["tick"]["quote"])
            print(f"📈 Tick: {precio}")

            if USAR_VELAS_TIEMPO:
                vela_m1 = actualizar_vela_tiempo(
                    estado_vela_m1,
                    precio,
                    SEGUNDOS_VELA_M1
                )

                if vela_m1 is not None:
                    velas_m1.append(vela_m1)
                    guardar_vela_m1(vela_m1)

                    print("\n⏱️ NUEVA VELA M1")
                    print(f"🕐 Inicio: {vela_m1['hora_inicio']}")
                    print(f"🕐 Cierre: {vela_m1['hora_cierre']}")
                    print(f"🟢 Open : {vela_m1['open']}")
                    print(f"🔺 High : {vela_m1['high']}")
                    print(f"🔻 Low  : {vela_m1['low']}")
                    print(f"🔴 Close: {vela_m1['close']}")
                    print(f"📊 Tipo : {vela_m1['tipo']}")

            ticks_vela.append(precio)

            if len(ticks_vela) < TICKS_POR_VELA:
                continue

            vela = construir_vela(ticks_vela)
            vela["patron"] = detectar_patron(vela)
            vela["impulso"] = clasificar_impulso(vela)

            velas.append(vela)
            contador_velas += 1
            actualizar_cooldown()

            close_price = vela["close"]
            patron = vela["patron"]
            impulso = vela["impulso"]

            print("\n🕯 NUEVA VELA TICK")
            print(f"🟢 Open : {vela['open']}")
            print(f"🔺 High : {vela['high']}")
            print(f"🔻 Low  : {vela['low']}")
            print(f"🔴 Close: {vela['close']}")
            print(f"📊 Tipo : {vela['tipo']}")
            print(f"🧠 Patrón: {patron}")
            print(f"⚡ Impulso: {impulso}")

            continuidad = detectar_continuidad_impulso(velas)

            # Por ahora estructura sigue usando tick candles.
            # En la siguiente fase la conectaremos a velas_m1.
            if len(velas_m1) >= 5:
                estructura = detectar_estructura(velas_m1)
                bos = detectar_bos(velas_m1)
                choch = detectar_choch(velas_m1)
                sweep = detectar_sweep_liquidez(velas_m1)
                mercado_lateral = detectar_mercado_lateral(velas_m1)

            else:
                estructura = "SIN_ESTRUCTURA"
                bos = "SIN_BOS"
                choch = "SIN_CHOCH"
                sweep = "SIN_SWEEP"
                mercado_lateral = False

            contexto_valido, motivo_contexto = evaluar_contexto_entrada(
                estructura,
                bos,
                sweep,
                mercado_lateral
            )

            print(f"⚡ Continuidad: {continuidad}")
            print(f"🏗️ Estructura: {estructura}")
            print(f"🧱 BOS: {bos}")
            print(f"🔄 CHOCH: {choch}")
            print(f"💧 Sweep: {sweep}")
            print(f"↔️ Mercado lateral: {mercado_lateral}")
            print(f"🧭 Contexto válido: {contexto_valido}")

            if len(velas) >= 3:
                tipos, patrones = analizar_contexto(velas)

                print("\n📚 ANALISIS DE CONTEXTO")

                tendencia_contexto = obtener_tendencia_contexto(tipos)
                patron_actual = patrones[-1]

                score_senal = calcular_score(
                    tipos,
                    patron_actual,
                    impulso,
                    continuidad,
                    estadisticas_patrones
                )

                senal_tecnica = generar_senal_pullback(
                    tipos,
                    patrones,
                    impulso,
                    continuidad,
                    estructura,
                    bos,
                    sweep,
                    contexto_valido
                )

                print(f"🚦 Señal técnica: {senal_tecnica}")
                print(f"🧠 Score señal: {score_senal}")
                print(f"📌 Operaciones pendientes: {len(operaciones)}")
                print(f"📉 Pérdidas consecutivas: {perdidas_consecutivas}")
                print(f"📉 Drawdown actual: {cuenta_paper['drawdown']}")

                evaluaciones = evaluar_operaciones(
                    operaciones,
                    contador_velas,
                    close_price
                )

                for evaluacion in evaluaciones:
                    operacion = evaluacion["operacion"]
                    precio_actual = evaluacion["precio_actual"]
                    resultado = evaluacion["resultado"]

                    print("\n🧪 EVALUACION")
                    print(f"📌 Señal: {operacion['senal']}")
                    print(f"💰 Entrada: {operacion['precio_entrada']}")
                    print(f"📍 Actual : {precio_actual}")
                    print(f"🎯 Resultado: {resultado}")

                    actualizar_estadisticas(
                        estadisticas,
                        estadisticas_patrones,
                        operacion,
                        resultado
                    )

                    combinacion = crear_clave_combinacion(
                        operacion["patron"],
                        operacion["impulso"],
                        operacion["continuidad"]
                    )

                    if combinacion not in estadisticas_combinaciones:
                        estadisticas_combinaciones[combinacion] = {
                            "correctas": 0,
                            "incorrectas": 0
                        }

                    if resultado == "CORRECTA":
                        estadisticas_combinaciones[combinacion]["correctas"] += 1
                    else:
                        estadisticas_combinaciones[combinacion]["incorrectas"] += 1

                    perdidas_consecutivas = actualizar_perdidas_consecutivas(
                        perdidas_consecutivas,
                        resultado
                    )

                    print(f"📉 Pérdidas consecutivas: {perdidas_consecutivas}")

                    mostrar_estadisticas(
                        estadisticas,
                        estadisticas_patrones
                    )

                    stake, profit_loss = actualizar_cuenta_paper(
                        cuenta_paper,
                        resultado
                    )

                    mostrar_cuenta_paper(cuenta_paper)

                    hora_evaluacion = datetime.now().strftime("%H:%M:%S")

                    guardar_evaluacion(
                        hora_evaluacion,
                        operacion["senal"],
                        operacion["precio_entrada"],
                        precio_actual,
                        resultado,
                        operacion["patron"],
                        operacion["impulso"],
                        operacion["continuidad"],
                        operacion["score_senal"]
                    )

                    guardar_operacion_paper(
                        hora_evaluacion,
                        operacion["senal"],
                        resultado,
                        stake,
                        profit_loss,
                        cuenta_paper["balance"],
                        cuenta_paper["equity_maxima"],
                        cuenta_paper["drawdown"],
                        operacion["patron"],
                        operacion["impulso"],
                        operacion["continuidad"],
                        operacion["score_senal"],
                        operacion["estructura"],
                        operacion["bos"],
                        operacion["choch"],
                        operacion["sweep"],
                        operacion["contexto_valido"]
                    )

                    print("💾 Evaluación y paper trading guardados")

                permitir_patron, motivo_patron = validar_patron(
                    patron_actual,
                    estadisticas_patrones
                )

                permitir_combinacion, motivo_combinacion, combinacion_actual, wr_combinacion = validar_combinacion(
                    patron_actual,
                    impulso,
                    continuidad,
                    estadisticas_combinaciones
                )

                print(f"🧬 Combinación: {combinacion_actual}")

                if wr_combinacion is not None:
                    print(f"📊 WR combinación: {wr_combinacion:.2f}%")
                else:
                    print("📊 WR combinación: sin datos suficientes")

                permitir_riesgo, motivo_riesgo = validar_riesgo(
                    operaciones,
                    perdidas_consecutivas,
                    score_senal,
                    vela,
                    cuenta_paper,
                    contexto_valido
                )

                permitir_operacion = (
                    permitir_patron
                    and permitir_riesgo
                    and permitir_combinacion
                )

                motivos = []

                if motivo_patron:
                    motivos.append(motivo_patron)

                if motivo_combinacion:
                    motivos.append(motivo_combinacion)

                if motivo_riesgo:
                    motivos.append(motivo_riesgo)

                hora_actual = datetime.now().strftime("%H")

                if FILTRO_V5_ACTIVO:
                    if (estructura == "ESTRUCTURA_ALCISTA"
                            and bos == "SIN_BOS"
                            and hora_actual in HORAS_V5_BLOQUEADAS):
                        permitir_operacion = False
                        motivos.append("filtro_v5_estructura_alcista_sin_bos_hora")
                        print("Operacion bloqueada por filtro V5 (ESTRUCTURA_ALCISTA + SIN_BOS + {}xx)".format(hora_actual))

                if ACTIVAR_FILTRO_CONTEXTO and not contexto_valido:
                    permitir_operacion = False
                    motivos.append(motivo_contexto)

                motivo_bloqueo = "|".join(motivos)

                if not permitir_operacion and motivo_bloqueo:
                    print(f"⛔ Operación bloqueada: {motivo_bloqueo}")

                if senal_tecnica != "ESPERAR" and permitir_operacion:
                    operacion = {
                        "senal": senal_tecnica,
                        "precio_entrada": close_price,
                        "vela_inicio": contador_velas,
                        "patron": patron_actual,
                        "impulso": impulso,
                        "continuidad": continuidad,
                        "score_senal": score_senal,
                        "estructura": estructura,
                    "velas_para_evaluar": (VELAS_EVALUAR_LATERAL
                        if EXPIRACION_DINAMICA_ACTIVA and estructura == "ESTRUCTURA_LATERAL"
                        else VELAS_EVALUAR_RESTO if EXPIRACION_DINAMICA_ACTIVA
                        else VELAS_PARA_EVALUAR),
                        "bos": bos,
                        "choch": choch,
                        "sweep": sweep,
                        "contexto_valido": contexto_valido
                    }

                    operaciones.append(operacion)
                    print("💾 Operación guardada para evaluación")

                hora_senal = datetime.now().strftime("%H:%M:%S")

                guardar_senal(
                    hora_senal,
                    senal_tecnica,
                    tendencia_contexto,
                    patron_actual,
                    impulso,
                    continuidad,
                    score_senal,
                    permitir_operacion,
                    motivo_bloqueo,
                    combinacion_actual,
                    wr_combinacion,
                    estructura,
                    bos,
                    choch,
                    sweep,
                    mercado_lateral,
                    contexto_valido,
                    motivo_contexto
                )

            hora = datetime.now().strftime("%H:%M:%S")
            guardar_vela(hora, vela, continuidad)

            ticks_vela.clear()


async def iniciar_bot():
    while True:
        try:
            await escuchar_ticks()

        except websockets.exceptions.ConnectionClosedError:
            print("⚠️ Conexión cerrada inesperadamente.")
            print("🔄 Reintentando conexión en 5 segundos...")
            await asyncio.sleep(5)

        except websockets.exceptions.ConnectionClosedOK:
            print("⚠️ Conexión cerrada normalmente.")
            print("🔄 Reintentando conexión en 5 segundos...")
            await asyncio.sleep(5)

        except Exception as error:
            print(f"❌ Error inesperado: {error}")
            print("🔄 Reintentando conexión en 10 segundos...")
            await asyncio.sleep(10)


asyncio.run(iniciar_bot())
