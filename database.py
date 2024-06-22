import sqlite3
import random
from datetime import datetime, timedelta

# Função para gerar uma data aleatória dentro de um intervalo
def random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

# Conecta ao banco de dados
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Cria a tabela se não existir
cursor.execute('''CREATE TABLE IF NOT EXISTS requisicoes (
                    id INTEGER PRIMARY KEY,
                    quantidade INTEGER,
                    tipo TEXT,
                    talao TEXT,
                    data DATE
                )''')

# Tipos e Talões possíveis
tipos = ["Groz-Beckert", "Neetex"]
taloes = ["Alto", "Baixo"]

# Popula o banco de dados com 10000 linhas
for _ in range(10000):
    quantidade = random.randint(1, 100)
    tipo = random.choice(tipos)
    talao = random.choice(taloes)
    data = random_date(datetime(2020, 1, 1), datetime(2023, 12, 31))

    # Insere os dados na tabela
    cursor.execute('''INSERT INTO requisicoes (quantidade, tipo, talao, data) 
                      VALUES (?, ?, ?, ?)''', (quantidade, tipo, talao, data))

# Confirma a inserção dos dados
conn.commit()

# Fecha a conexão com o banco de dados
conn.close()

print("Dados inseridos com sucesso.")
