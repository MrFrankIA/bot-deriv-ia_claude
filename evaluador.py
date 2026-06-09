from config import VELAS_PARA_EVALUAR, EXPIRACION_DINAMICA_ACTIVA, VELAS_EVALUAR_LATERAL, VELAS_EVALUAR_RESTO


def evaluar_operaciones(operaciones, contador_velas, close_price):
    evaluaciones = []

    for operacion in operaciones[:]:
        velas_transcurridas = contador_velas - operacion["vela_inicio"]

        limite = operacion.get('velas_para_evaluar', VELAS_PARA_EVALUAR)
        if velas_transcurridas >= limite:
            precio_actual = close_price
            resultado = "INCORRECTA"

            if operacion["senal"] == "COMPRAR" and precio_actual > operacion["precio_entrada"]:
                resultado = "CORRECTA"

            elif operacion["senal"] == "VENDER" and precio_actual < operacion["precio_entrada"]:
                resultado = "CORRECTA"

            evaluaciones.append({
                "operacion": operacion,
                "precio_actual": precio_actual,
                "resultado": resultado
            })

            operaciones.remove(operacion)

    return evaluaciones
