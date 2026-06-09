import csv
import os
from collections import defaultdict

ARCHIVO_EVALUACIONES = "evaluaciones.csv"

REPORTES = {
    "resumen": "resumen_backtesting.csv",
    "ranking_combinaciones": "ranking_combinaciones.csv",
    "peores_combinaciones": "peores_combinaciones.csv",
    "senal": "rendimiento_senal.csv",
    "patron": "rendimiento_patron.csv",
    "impulso": "rendimiento_impulso.csv",
    "continuidad": "rendimiento_continuidad.csv",
    "score": "rendimiento_score.csv",
}

MIN_OPERACIONES_RANKING = 3


def crear_grupo():
    return {"total": 0, "correctas": 0, "incorrectas": 0}


def actualizar_grupo(grupo, resultado):
    grupo["total"] += 1
    if resultado == "CORRECTA":
        grupo["correctas"] += 1
    else:
        grupo["incorrectas"] += 1


def win_rate(grupo):
    if grupo["total"] == 0:
        return 0
    return (grupo["correctas"] / grupo["total"]) * 100


def leer_evaluaciones():
    if not os.path.exists(ARCHIVO_EVALUACIONES):
        print(f"❌ No existe {ARCHIVO_EVALUACIONES}")
        return []

    filas = []

    with open(ARCHIVO_EVALUACIONES, mode="r", newline="", encoding="utf-8") as archivo:
        reader = csv.DictReader(archivo)

        for fila in reader:
            resultado = fila.get("resultado", "").strip()

            if resultado not in ["CORRECTA", "INCORRECTA"]:
                continue

            patron = fila.get("patron", "DESCONOCIDO").strip() or "DESCONOCIDO"
            impulso = fila.get("impulso", "DESCONOCIDO").strip() or "DESCONOCIDO"
            continuidad = fila.get("continuidad", "DESCONOCIDO").strip() or "DESCONOCIDO"

            fila["patron"] = patron
            fila["impulso"] = impulso
            fila["continuidad"] = continuidad
            fila["combinacion"] = f"{patron}|{impulso}|{continuidad}"

            filas.append(fila)

    return filas


def ordenar(diccionario, minimo=1, descendente=True):
    datos = [
        (categoria, grupo)
        for categoria, grupo in diccionario.items()
        if grupo["total"] >= minimo
    ]

    datos.sort(
        key=lambda item: (win_rate(item[1]), item[1]["total"]),
        reverse=descendente
    )

    return datos


def guardar_reporte(nombre_archivo, datos):
    with open(nombre_archivo, mode="w", newline="", encoding="utf-8") as archivo:
        writer = csv.writer(archivo)
        writer.writerow(["categoria", "total", "correctas", "incorrectas", "win_rate"])

        for categoria, grupo in datos:
            writer.writerow([
                categoria,
                grupo["total"],
                grupo["correctas"],
                grupo["incorrectas"],
                round(win_rate(grupo), 2)
            ])


def imprimir(titulo, datos, limite=None):
    print(titulo)

    if not datos:
        print("Sin datos suficientes.")
        return

    for i, (categoria, grupo) in enumerate(datos, start=1):
        print(
            f"{categoria} → {win_rate(grupo):.2f}% "
            f"({grupo['total']} ops | ✅ {grupo['correctas']} / ❌ {grupo['incorrectas']})"
        )

        if limite and i >= limite:
            break


def main():
    evaluaciones = leer_evaluaciones()

    if not evaluaciones:
        print("No hay evaluaciones válidas para analizar.")
        return

    general = crear_grupo()
    por_senal = defaultdict(crear_grupo)
    por_patron = defaultdict(crear_grupo)
    por_impulso = defaultdict(crear_grupo)
    por_continuidad = defaultdict(crear_grupo)
    por_score = defaultdict(crear_grupo)
    por_combinacion = defaultdict(crear_grupo)

    for fila in evaluaciones:
        resultado = fila["resultado"]
        senal = fila.get("senal", "DESCONOCIDA").strip() or "DESCONOCIDA"
        score = fila.get("score_senal", "SIN_SCORE").strip() or "SIN_SCORE"

        actualizar_grupo(general, resultado)
        actualizar_grupo(por_senal[senal], resultado)
        actualizar_grupo(por_patron[fila["patron"]], resultado)
        actualizar_grupo(por_impulso[fila["impulso"]], resultado)
        actualizar_grupo(por_continuidad[fila["continuidad"]], resultado)
        actualizar_grupo(por_score[score], resultado)
        actualizar_grupo(por_combinacion[fila["combinacion"]], resultado)

    print("\\n📊 BACKTESTING GENERAL")
    print(f"📌 Total operaciones: {general['total']}")
    print(f"✅ Correctas: {general['correctas']}")
    print(f"❌ Incorrectas: {general['incorrectas']}")
    print(f"🎯 Win Rate: {win_rate(general):.2f}%")

    ranking_senal = ordenar(por_senal)
    ranking_patron = ordenar(por_patron)
    ranking_impulso = ordenar(por_impulso)
    ranking_continuidad = ordenar(por_continuidad)
    ranking_score = ordenar(por_score)
    ranking_combinaciones = ordenar(por_combinacion, MIN_OPERACIONES_RANKING, True)
    peores_combinaciones = ordenar(por_combinacion, MIN_OPERACIONES_RANKING, False)

    imprimir("\\n📈 RENDIMIENTO POR SEÑAL", ranking_senal)
    imprimir("\\n🧠 RENDIMIENTO POR PATRÓN", ranking_patron)
    imprimir("\\n⚡ RENDIMIENTO POR IMPULSO", ranking_impulso)
    imprimir("\\n🔁 RENDIMIENTO POR CONTINUIDAD", ranking_continuidad)
    imprimir("\\n🎯 RENDIMIENTO POR SCORE", ranking_score)
    imprimir(f"\\n🏆 TOP COMBINACIONES — mínimo {MIN_OPERACIONES_RANKING} ops", ranking_combinaciones, 20)
    imprimir(f"\\n⚠️ PEORES COMBINACIONES — mínimo {MIN_OPERACIONES_RANKING} ops", peores_combinaciones, 20)

    with open(REPORTES["resumen"], mode="w", newline="", encoding="utf-8") as archivo:
        writer = csv.writer(archivo)
        writer.writerow(["total", "correctas", "incorrectas", "win_rate"])
        writer.writerow([
            general["total"],
            general["correctas"],
            general["incorrectas"],
            round(win_rate(general), 2)
        ])

    guardar_reporte(REPORTES["senal"], ranking_senal)
    guardar_reporte(REPORTES["patron"], ranking_patron)
    guardar_reporte(REPORTES["impulso"], ranking_impulso)
    guardar_reporte(REPORTES["continuidad"], ranking_continuidad)
    guardar_reporte(REPORTES["score"], ranking_score)
    guardar_reporte(REPORTES["ranking_combinaciones"], ranking_combinaciones)
    guardar_reporte(REPORTES["peores_combinaciones"], peores_combinaciones)

    print("\\n💾 Reportes generados correctamente.")


if __name__ == "__main__":
    main()
