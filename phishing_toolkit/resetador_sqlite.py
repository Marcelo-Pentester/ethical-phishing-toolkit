import sqlite3
import time
import os

# ====== CONFIGURAÇÃO ======
CAMINHO_BANCO = "db.sqlite"  # Caminho do seu banco
INTERVALO_MINUTOS = 30       # Tempo entre resets (em minutos)
# ===========================

def resetar_banco_sqlite(caminho):
    if not os.path.exists(caminho):
        print(f"[ERRO] Banco de dados não encontrado em: {caminho}")
        return

    print(f"[INFO] Resetando banco: {caminho}")
    conn = sqlite3.connect(caminho)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = OFF;")
        cursor.execute("BEGIN TRANSACTION;")

        # Seleciona todas as tabelas (exceto internas do SQLite)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tabelas = cursor.fetchall()

        for tabela in tabelas:
            nome = tabela[0]
            print(f" - DROP TABLE {nome}")
            cursor.execute(f'DROP TABLE IF EXISTS "{nome}";')

        cursor.execute("DELETE FROM sqlite_sequence;")  # Zera AUTOINCREMENT
        conn.commit()
        print("[OK] Banco resetado com sucesso.\n")

    except Exception as e:
        conn.rollback()
        print(f"[ERRO] Falha ao resetar banco: {e}")
    finally:
        conn.close()

def loop_reset():
    while True:
        resetar_banco_sqlite(CAMINHO_BANCO)
        print(f"[INFO] Aguardando {INTERVALO_MINUTOS} minutos até o próximo reset...\n")
        time.sleep(INTERVALO_MINUTOS * 60)

if __name__ == "__main__":
    print("[START] Iniciando script de reset periódico do banco SQLite...\n")
    loop_reset()

