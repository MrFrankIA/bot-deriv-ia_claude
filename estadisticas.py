def actualizar_estadisticas(estadisticas, estadisticas_patrones, operacion, resultado):
    patron_operacion = operacion["patron"]

    if patron_operacion not in estadisticas_patrones:
        estadisticas_patrones[patron_operacion] = {
            "correctas": 0,
            "incorrectas": 0
        }

    if resultado == "CORRECTA":
        estadisticas["correctas"] += 1
        estadisticas_patrones[patron_operacion]["correctas"] += 1
    else:
        estadisticas["incorrectas"] += 1
        estadisticas_patrones[patron_operacion]["incorrectas"] += 1

    estadisticas["total"] += 1


def mostrar_estadisticas(estadisticas, estadisticas_patrones):
    if estadisticas["total"] == 0:
        return

    win_rate = (estadisticas["correctas"] / estadisticas["total"]) * 100

    print("\n📊 ESTADISTICAS BOT")
    print(f"📌 Total: {estadisticas['total']}")
    print(f"✅ Correctas: {estadisticas['correctas']}")
    print(f"❌ Incorrectas: {estadisticas['incorrectas']}")
    print(f"🎯 Win Rate: {win_rate:.2f}%")

    print("\n🧠 RENDIMIENTO POR PATRON")

    for patron, datos in estadisticas_patrones.items():
        total_patron = datos["correctas"] + datos["incorrectas"]

        if total_patron > 0:
            wr_patron = (datos["correctas"] / total_patron) * 100

            print(
                f"📌 {patron} → "
                f"{wr_patron:.2f}% "
                f"({total_patron} ops)"
            )
