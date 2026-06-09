import csv
import os

ARCHIVO_RANKING = "ranking_combinaciones.csv"
ARCHIVO_PEORES = "peores_combinaciones.csv"

ARCHIVO_SETUPS_APROBADOS = "setups_aprobados.csv"
ARCHIVO_SETUPS_BLOQUEADOS = "setups_bloqueados.csv"
ARCHIVO_RECOMENDACIONES = "recomendaciones_backtesting.csv"

MIN_OPERACIONES_SETUP = 5
WIN_RATE_APROBADO = 55
WIN_RATE_BLOQUEADO = 40


def leer_csv(nombre_archivo):
    if not os.path.exists(nombre_archivo):
        print(f"❌ No existe {nombre_archivo}")
        return []

    with open(nombre_archivo, mode="r", newline="", encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def numero(valor):
    try:
        return float(valor)
    except:
        return 0


def guardar_lista(nombre_archivo, filas):
    with open(nombre_archivo, mode="w", newline="", encoding="utf-8") as archivo:
        writer = csv.writer(archivo)
        writer.writerow(["combinacion", "total", "correctas", "incorrectas", "win_rate"])

        for fila in filas:
            writer.writerow([
                fila["categoria"],
                fila["total"],
                fila["correctas"],
                fila["incorrectas"],
                fila["win_rate"]
            ])


def guardar_recomendaciones(aprobados, bloqueados):
    if not aprobados and not bloqueados:
        observacion = (
            "Todavía no hay suficientes datos confiables. "
            "Deja correr el bot más tiempo antes de tomar decisiones."
        )
    elif aprobados:
        observacion = (
            "Ya existen setups prometedores. "
            "Revisa setups_aprobados.csv antes de usarlos en filtros reales."
        )
    else:
        observacion = (
            "Hay setups malos detectados, pero pocos o ningún setup aprobado. "
            "Conviene seguir recolectando datos."
        )

    with open(ARCHIVO_RECOMENDACIONES, mode="w", newline="", encoding="utf-8") as archivo:
        writer = csv.writer(archivo)
        writer.writerow(["tipo", "mensaje"])
        writer.writerow(["resumen", observacion])
        writer.writerow(["setups_aprobados", f"{len(aprobados)} combinaciones cumplen criterios"])
        writer.writerow(["setups_bloqueados", f"{len(bloqueados)} combinaciones deben evitarse"])


def main():
    ranking = leer_csv(ARCHIVO_RANKING)
    peores = leer_csv(ARCHIVO_PEORES)

    aprobados = []
    bloqueados = []

    for fila in ranking:
        total = numero(fila.get("total", 0))
        wr = numero(fila.get("win_rate", 0))

        if total >= MIN_OPERACIONES_SETUP and wr >= WIN_RATE_APROBADO:
            aprobados.append(fila)

    for fila in peores:
        total = numero(fila.get("total", 0))
        wr = numero(fila.get("win_rate", 0))

        if total >= MIN_OPERACIONES_SETUP and wr < WIN_RATE_BLOQUEADO:
            bloqueados.append(fila)

    guardar_lista(ARCHIVO_SETUPS_APROBADOS, aprobados)
    guardar_lista(ARCHIVO_SETUPS_BLOQUEADOS, bloqueados)
    guardar_recomendaciones(aprobados, bloqueados)

    print("\\n🧪 OPTIMIZADOR DE SETUPS")
    print(f"✅ Setups aprobados: {len(aprobados)}")
    print(f"⛔ Setups bloqueados: {len(bloqueados)}")
    print("\\n💾 Archivos generados:")
    print(f"- {ARCHIVO_SETUPS_APROBADOS}")
    print(f"- {ARCHIVO_SETUPS_BLOQUEADOS}")
    print(f"- {ARCHIVO_RECOMENDACIONES}")


if __name__ == "__main__":
    main()
