import csv
import os
from config import ARCHIVO_EVALUACIONES


def cargar_memoria():
    estadisticas = {
        "total": 0,
        "correctas": 0,
        "incorrectas": 0
    }

    estadisticas_patrones = {}
    perdidas_consecutivas = 0

    if not os.path.exists(ARCHIVO_EVALUACIONES):
        return estadisticas, estadisticas_patrones, perdidas_consecutivas

    with open(ARCHIVO_EVALUACIONES, mode="r", newline="") as archivo:
        reader = csv.DictReader(archivo)

        for fila in reader:
            resultado = fila.get("resultado", "")
            patron = fila.get("patron", "DESCONOCIDO")

            if resultado not in ["CORRECTA", "INCORRECTA"]:
                continue

            estadisticas["total"] += 1

            if patron not in estadisticas_patrones:
                estadisticas_patrones[patron] = {
                    "correctas": 0,
                    "incorrectas": 0
                }

            if resultado == "CORRECTA":
                estadisticas["correctas"] += 1
                estadisticas_patrones[patron]["correctas"] += 1
                perdidas_consecutivas = 0
            else:
                estadisticas["incorrectas"] += 1
                estadisticas_patrones[patron]["incorrectas"] += 1
                perdidas_consecutivas += 1

    print("🧠 Memoria cargada desde evaluaciones.csv")
    print(f"📌 Evaluaciones previas: {estadisticas['total']}")
    print(f"📉 Pérdidas consecutivas previas: {perdidas_consecutivas}")

    return estadisticas, estadisticas_patrones, perdidas_consecutivas
