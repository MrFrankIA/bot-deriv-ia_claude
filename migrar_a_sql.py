# -*- coding: utf-8 -*-
"""
Migracion / resync de los CSV historicos a SQLite.

Ejecutar con el bot DETENIDO para evitar carreras: hace DELETE + reimport
completo desde cada CSV, por lo que es re-ejecutable (idempotente).

  systemctl stop botderivclaude
  venv/bin/python migrar_a_sql.py
  systemctl start botderivclaude

El CSV sigue siendo la fuente; esto solo llena la copia SQLite.
"""
import csv
import os

import db
from config import (
    ARCHIVO_OPERACIONES_DEMO,
    ARCHIVO_OPERACIONES_PAPER,
    ARCHIVO_SENALES,
)

TABLAS = [
    ("operaciones_demo",  ARCHIVO_OPERACIONES_DEMO,  db.COLS_DEMO),
    ("operaciones_paper", ARCHIVO_OPERACIONES_PAPER, db.COLS_PAPER),
    ("senales",           ARCHIVO_SENALES,           db.COLS_SENALES),
]


def importar(tabla, archivo, cols):
    if not os.path.exists(archivo):
        print(f"  {archivo}: no existe, omito")
        return 0
    with open(archivo, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    con = db.conectar()
    try:
        con.execute(f"DELETE FROM {tabla}")
        placeholders = ",".join("?" * len(cols))
        sql = f"INSERT INTO {tabla} ({','.join(cols)}) VALUES ({placeholders})"
        for fila in filas:
            # "" -> None para que las columnas numericas queden NULL, no texto.
            valores = [
                (fila.get(c) if fila.get(c) not in ("", None) else None)
                for c in cols
            ]
            con.execute(sql, valores)
        con.commit()
        return len(filas)
    finally:
        con.close()


def main():
    db.inicializar_db()
    print(f"DB: {db.RUTA_DB}")
    for tabla, archivo, cols in TABLAS:
        n = importar(tabla, archivo, cols)
        print(f"  {tabla}: {n} filas importadas desde {archivo}")
    con = db.conectar()
    try:
        print("--- verificacion ---")
        for tabla, _, _ in TABLAS:
            c = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            print(f"  {tabla}: {c} filas en DB")
    finally:
        con.close()


if __name__ == "__main__":
    main()
