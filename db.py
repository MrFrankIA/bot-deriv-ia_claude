# -*- coding: utf-8 -*-
"""
Capa de persistencia SQLite (stdlib, sin dependencias externas).

Convive con el almacenamiento CSV como fuente analitica. Las escrituras desde
el bot las envuelve el llamador en try/except, de modo que un fallo de DB NUNCA
rompe el loop de trading: el CSV sigue siendo el respaldo y la ejecucion del
contrato ya ocurrio antes de persistir.

WAL activado para que el dashboard y el motor de aprendizaje puedan LEER
mientras el bot ESCRIBE (un escritor + varios lectores sin bloqueo).

Las tablas reflejan 1:1 las columnas de los CSV (operaciones_demo,
operaciones_paper, senales) para que la migracion sea directa y las consultas
del analisis ya validado porten sin cambios.
"""
import os
import sqlite3

# Ruta del archivo .db. Por defecto junto al codigo; configurable por entorno.
RUTA_DB = os.environ.get(
    "BOT_DB",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.db"),
)

DDL = """
CREATE TABLE IF NOT EXISTS operaciones_demo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT, hora TEXT,
    senal TEXT, resultado TEXT,
    buy_price REAL, profit REAL, payout REAL,
    entry_spot REAL, exit_spot REAL,
    contract_id TEXT UNIQUE,
    patron TEXT, impulso TEXT, continuidad TEXT, score_senal INTEGER,
    estructura TEXT, bos TEXT, choch TEXT, sweep TEXT, contexto_valido TEXT
);

CREATE TABLE IF NOT EXISTS operaciones_paper (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT, hora TEXT,
    senal TEXT, resultado TEXT,
    stake REAL, profit_loss REAL, balance REAL,
    equity_maxima REAL, drawdown REAL,
    patron TEXT, impulso TEXT, continuidad TEXT, score_senal INTEGER,
    estructura TEXT, bos TEXT, choch TEXT, sweep TEXT, contexto_valido TEXT
);

CREATE TABLE IF NOT EXISTS senales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT, hora TEXT,
    senal_tecnica TEXT, tendencia_contexto TEXT, patron_actual TEXT,
    impulso TEXT, continuidad TEXT, score_senal INTEGER,
    permitida TEXT, motivo_bloqueo TEXT, combinacion TEXT, wr_combinacion REAL,
    estructura TEXT, bos TEXT, choch TEXT, sweep TEXT,
    mercado_lateral TEXT, contexto_valido TEXT, motivo_contexto TEXT
);

CREATE INDEX IF NOT EXISTS idx_demo_fecha  ON operaciones_demo(fecha);
CREATE INDEX IF NOT EXISTS idx_demo_ctx    ON operaciones_demo(estructura, sweep, choch);
CREATE INDEX IF NOT EXISTS idx_demo_senal  ON operaciones_demo(senal);
CREATE INDEX IF NOT EXISTS idx_paper_fecha ON operaciones_paper(fecha);
CREATE INDEX IF NOT EXISTS idx_sen_fecha   ON senales(fecha);
"""

# Columnas por tabla (orden canonico para insercion).
COLS_DEMO = [
    "fecha", "hora", "senal", "resultado", "buy_price", "profit", "payout",
    "entry_spot", "exit_spot", "contract_id", "patron", "impulso",
    "continuidad", "score_senal", "estructura", "bos", "choch", "sweep",
    "contexto_valido",
]
COLS_PAPER = [
    "fecha", "hora", "senal", "resultado", "stake", "profit_loss", "balance",
    "equity_maxima", "drawdown", "patron", "impulso", "continuidad",
    "score_senal", "estructura", "bos", "choch", "sweep", "contexto_valido",
]
COLS_SENALES = [
    "fecha", "hora", "senal_tecnica", "tendencia_contexto", "patron_actual",
    "impulso", "continuidad", "score_senal", "permitida", "motivo_bloqueo",
    "combinacion", "wr_combinacion", "estructura", "bos", "choch", "sweep",
    "mercado_lateral", "contexto_valido", "motivo_contexto",
]


def conectar():
    con = sqlite3.connect(RUTA_DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    return con


def inicializar_db():
    con = conectar()
    try:
        con.executescript(DDL)
        con.commit()
    finally:
        con.close()


def _insertar(tabla, cols, valores, ignorar_duplicado=False):
    """Insercion de una fila. Abre/cierra conexion por llamada (tasa de
    escritura baja, ~cientos/dia); evita compartir conexiones entre hilos."""
    placeholders = ",".join("?" * len(cols))
    prefijo = "INSERT OR IGNORE" if ignorar_duplicado else "INSERT"
    sql = "%s INTO %s (%s) VALUES (%s)" % (
        prefijo, tabla, ",".join(cols), placeholders)
    con = conectar()
    try:
        con.execute(sql, valores)
        con.commit()
    finally:
        con.close()


def insertar_operacion_demo(valores):
    # contract_id es UNIQUE -> reintentos/duplicados se ignoran sin error.
    _insertar("operaciones_demo", COLS_DEMO, valores, ignorar_duplicado=True)


def insertar_operacion_paper(valores):
    _insertar("operaciones_paper", COLS_PAPER, valores)


def insertar_senal(valores):
    _insertar("senales", COLS_SENALES, valores)
