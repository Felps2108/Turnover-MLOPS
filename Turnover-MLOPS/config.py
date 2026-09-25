"""
Constantes compartilhadas por toda a aplicacao.

Regra da disciplina: nenhum destes valores aparece escrito no meio do codigo.
Se voce vir "champion" digitado dentro do main.py, alguem quebrou a regra.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent
load_dotenv(RAIZ / ".env")

# -------------------------------------------------------------- Postgres ----
# Um servidor Postgres, dois bancos: o seu (turnover) e o do MLflow.
# Onde o servidor vive e escolha sua -- Docker, local ou nuvem.
# Senha em variavel de ambiente, nao no codigo -- ver .env.exemplo.
PG_HOST = os.getenv("PG_HOST", "127.0.0.1")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "turnover")
PG_SENHA = os.getenv("PG_SENHA", "turnover")
PG_DB_MLFLOW = os.getenv("PG_DB_MLFLOW", "mlflow")
PG_DB_APP = os.getenv("PG_DB_APP", "turnover")


def uri_postgres(banco):
    return f"postgresql://{PG_USER}:{PG_SENHA}@{PG_HOST}:{PG_PORT}/{banco}"


# Onde o MLflow guarda runs, metricas e o catalogo de versoes.
URI_BANCO_MLFLOW = uri_postgres(PG_DB_MLFLOW)

# Onde a aplicacao guarda o log de predicoes.
URI_BANCO_APP = uri_postgres(PG_DB_APP)

# ---------------------------------------------------------------- MLflow ----
URI_TRACKING = os.getenv("MLFLOW_URI", "http://127.0.0.1:5000")
NOME_EXPERIMENTO = "turnover_rh"
NOME_MODELO = "turnover_rh"
ALIAS_PROD = "champion"
ALIAS_CANDIDATO = "challenger"

# ------------------------------------------------------------ Aplicacao ----
PASTA_ARTEFATOS = RAIZ / "artefatos"
PASTA_DADOS = RAIZ / "dados"
PASTA_RELATORIOS = RAIZ / "relatorios"

# ---------------------------------------------------------------- Modelo ----
COLUNA_ID = "id_pessoa"
COLUNA_ALVO = "pediu_para_sair"

FEATURES = [
    "abs_eventos",
    "abs_qtd_total",
    "horas_previstas_total",
    "acidentes_eventos",
    "acidentes_com_afastamento",
    "acidentes_dias_perdidos",
    "he_eventos",
    "he_referencia_total",
    "he_valor_total",
    "hi_eventos",
    "hi_minutos_irregulares",
    "hi_minutos_extras",
    "mov_sal_eventos",
    "mov_sal_valor_total",
    "mov_sal_perc_medio",
]

LIMIAR_DECISAO = 0.5
FAIXA_ATENCAO = 0.50
FAIXA_ALERTA = 0.60

TABELA_TREINO = "treino_v1"
TABELA_VALIDACAO = "validacao_congelada"
TABELA_PREDICOES = "predicoes"

SEED = 42

# DOIS conjuntos de teste, com papeis diferentes -- um nao substitui o outro:
#
#   validacao_congelada  GUARDA DE REGRESSAO. Nunca muda, nunca e apagada.
#                        Responde "eu quebrei o que ja funcionava?"
#   validacao_atual      CONJUNTO DE ACEITACAO. Representa a populacao que o
#                        modelo atende HOJE. Cresce a cada lote rotulado.
#                        Responde "serve para o mundo de agora?"
TABELA_VALIDACAO_ATUAL = "validacao_atual"

# Ganho minimo de F1 para o candidato substituir o campeao.
# Abaixo disso a troca nao paga o risco de mexer em producao.
GANHO_MINIMO = 0.005


if __name__ == "__main__":
    print("python -m mlflow server"
          " --host 127.0.0.1"
          " --port 5000"
          f" --backend-store-uri {URI_BANCO_MLFLOW}"
          " --default-artifact-root ./mlruns")
