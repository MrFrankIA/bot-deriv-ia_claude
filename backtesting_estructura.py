import csv
import os
from collections import defaultdict

ARCHIVO_SENALES = "senales.csv"

ARCHIVO_RENDIMIENTO_ESTRUCTURA = "rendimiento_estructura.csv"
ARCHIVO_RENDIMIENTO_BOS = "rendimiento_bos.csv"
ARCHIVO_RENDIMIENTO_CHOCH = "rendimiento_choch.csv"
ARCHIVO_RENDIMIENTO_SWEEP = "rendimiento_sweep.csv"
ARCHIVO_RENDIMIENTO_LATERAL = "rendimiento_mercado_lateral.csv"
ARCHIVO_RENDIMIENTO_CONTEXTO = "rendimiento_contexto_valido.csv"
ARCHIVO_RENDIMIENTO_MOTIVO_CONTEXTO = "rendimiento_motivo_contexto.csv"
ARCHIVO_RESUMEN_ESTRUCTURAL = "resumen_backtesting_estructura.csv"


def crear_grupo():
    return {
        "total": 0,
        "permitidas": 0,
        "bloqueadas": 0
    }


def actualizar_grupo(grupo, permitida):
    grupo["total"] += 1

    if permitida:
        grupo["permitidas"] += 1
    else:
        grupo["bloqueadas"] += 1


def porcentaje(valor, total):
    if total == 0:
        return 0

    return (valor / total) * 100


def leer_senales():
    if not os.path.exists(ARCHIVO_SENALES):
        print(f"❌ No existe {ARCHIVO_SENALES}")
        return []

    filas = []

    with open(
        ARCHIVO_SENALES,
        mode="r",
        newline="",
        encoding="utf-8"
    ) as archivo:
        reader = csv.DictReader(archivo)

        columnas = reader.fieldnames or []

        columnas_requeridas = [
            "estructura",
            "bos",
            "choch",
            "sweep",
            "mercado_lateral",
            "contexto_valido",
            "motivo_contexto"
        ]

        faltantes = [
            columna
            for columna in columnas_requeridas
            if columna not in columnas
        ]

        if faltantes:
            print("❌ senales.csv no tiene todavía las columnas nuevas.")
            print(f"Columnas faltantes: {faltantes}")
            print("Renombra o borra senales.csv y deja que main.py lo cree de nuevo.")
            return []

        for fila in reader:
            filas.append(fila)

    return filas


def texto_bool(valor):
    valor = str(valor).strip().lower()

    return valor in ["true", "1", "si", "sí", "yes"]


def ordenar(diccionario):
    datos = list(diccionario.items())

    datos.sort(
        key=lambda item: item[1]["total"],
        reverse=True
    )

    return datos


def guardar_reporte(nombre_archivo, datos):
    with open(
        nombre_archivo,
        mode="w",
        newline="",
        encoding="utf-8"
    ) as archivo:
        writer = csv.writer(archivo)

        writer.writerow([
            "categoria",
            "total",
            "permitidas",
            "bloqueadas",
            "porcentaje_permitidas",
            "porcentaje_bloqueadas"
        ])

        for categoria, grupo in datos:
            total = grupo["total"]

            writer.writerow([
                categoria,
                total,
                grupo["permitidas"],
                grupo["bloqueadas"],
                round(
                    porcentaje(grupo["permitidas"], total),
                    2
                ),
                round(
                    porcentaje(grupo["bloqueadas"], total),
                    2
                )
            ])


def imprimir_reporte(titulo, datos):
    print(f"\n{titulo}")

    if not datos:
        print("Sin datos.")
        return

    for categoria, grupo in datos:
        total = grupo["total"]
        permitidas = grupo["permitidas"]
        bloqueadas = grupo["bloqueadas"]

        print(
            f"{categoria} → "
            f"{total} señales | "
            f"Permitidas: {permitidas} "
            f"({porcentaje(permitidas, total):.2f}%) | "
            f"Bloqueadas: {bloqueadas} "
            f"({porcentaje(bloqueadas, total):.2f}%)"
        )


def main():
    senales = leer_senales()

    if not senales:
        return

    total_senales = len(senales)
    total_permitidas = 0
    total_bloqueadas = 0

    por_estructura = defaultdict(crear_grupo)
    por_bos = defaultdict(crear_grupo)
    por_choch = defaultdict(crear_grupo)
    por_sweep = defaultdict(crear_grupo)
    por_lateral = defaultdict(crear_grupo)
    por_contexto = defaultdict(crear_grupo)
    por_motivo_contexto = defaultdict(crear_grupo)

    for fila in senales:
        permitida = texto_bool(
            fila.get("permitida", "False")
        )

        if permitida:
            total_permitidas += 1
        else:
            total_bloqueadas += 1

        estructura = fila.get("estructura", "SIN_DATO") or "SIN_DATO"
        bos = fila.get("bos", "SIN_DATO") or "SIN_DATO"
        choch = fila.get("choch", "SIN_DATO") or "SIN_DATO"
        sweep = fila.get("sweep", "SIN_DATO") or "SIN_DATO"
        lateral = fila.get("mercado_lateral", "SIN_DATO") or "SIN_DATO"
        contexto = fila.get("contexto_valido", "SIN_DATO") or "SIN_DATO"
        motivo_contexto = fila.get("motivo_contexto", "SIN_MOTIVO") or "SIN_MOTIVO"

        actualizar_grupo(por_estructura[estructura], permitida)
        actualizar_grupo(por_bos[bos], permitida)
        actualizar_grupo(por_choch[choch], permitida)
        actualizar_grupo(por_sweep[sweep], permitida)
        actualizar_grupo(por_lateral[lateral], permitida)
        actualizar_grupo(por_contexto[contexto], permitida)
        actualizar_grupo(por_motivo_contexto[motivo_contexto], permitida)

    print("\n🏗️ BACKTESTING ESTRUCTURAL")
    print(f"📌 Total señales: {total_senales}")
    print(f"✅ Permitidas: {total_permitidas}")
    print(f"⛔ Bloqueadas: {total_bloqueadas}")
    print(
        f"📊 % Permitidas: "
        f"{porcentaje(total_permitidas, total_senales):.2f}%"
    )

    datos_estructura = ordenar(por_estructura)
    datos_bos = ordenar(por_bos)
    datos_choch = ordenar(por_choch)
    datos_sweep = ordenar(por_sweep)
    datos_lateral = ordenar(por_lateral)
    datos_contexto = ordenar(por_contexto)
    datos_motivo = ordenar(por_motivo_contexto)

    imprimir_reporte("🏗️ POR ESTRUCTURA", datos_estructura)
    imprimir_reporte("🧱 POR BOS", datos_bos)
    imprimir_reporte("🔄 POR CHOCH", datos_choch)
    imprimir_reporte("💧 POR SWEEP", datos_sweep)
    imprimir_reporte("↔️ POR MERCADO LATERAL", datos_lateral)
    imprimir_reporte("🧭 POR CONTEXTO VÁLIDO", datos_contexto)
    imprimir_reporte("📌 POR MOTIVO CONTEXTO", datos_motivo)

    guardar_reporte(
        ARCHIVO_RENDIMIENTO_ESTRUCTURA,
        datos_estructura
    )

    guardar_reporte(
        ARCHIVO_RENDIMIENTO_BOS,
        datos_bos
    )

    guardar_reporte(
        ARCHIVO_RENDIMIENTO_CHOCH,
        datos_choch
    )

    guardar_reporte(
        ARCHIVO_RENDIMIENTO_SWEEP,
        datos_sweep
    )

    guardar_reporte(
        ARCHIVO_RENDIMIENTO_LATERAL,
        datos_lateral
    )

    guardar_reporte(
        ARCHIVO_RENDIMIENTO_CONTEXTO,
        datos_contexto
    )

    guardar_reporte(
        ARCHIVO_RENDIMIENTO_MOTIVO_CONTEXTO,
        datos_motivo
    )

    with open(
        ARCHIVO_RESUMEN_ESTRUCTURAL,
        mode="w",
        newline="",
        encoding="utf-8"
    ) as archivo:
        writer = csv.writer(archivo)

        writer.writerow([
            "total_senales",
            "permitidas",
            "bloqueadas",
            "porcentaje_permitidas"
        ])

        writer.writerow([
            total_senales,
            total_permitidas,
            total_bloqueadas,
            round(
                porcentaje(total_permitidas, total_senales),
                2
            )
        ])

    print("\n💾 Reportes estructurales generados correctamente.")


if __name__ == "__main__":
    main()
