"""
A API de producao.

A aplicacao carrega o modelo do Model Registry pelo alias @champion. Assim,
nenhum caminho de .pkl nem numero fixo de versao fica dentro da API.
"""
import io
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import mlflow
import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from mlflow.tracking import MlflowClient
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from app import banco  # noqa: E402

ESTATICOS = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def ciclo_de_vida(app):
    """No boot, confere o banco e busca o modelo no registry."""
    banco.conferir()
    carregar_modelo()
    yield


app = FastAPI(title="Turnover RH - producao", lifespan=ciclo_de_vida)
app.mount("/static", StaticFiles(directory=ESTATICOS), name="static")

MODELO = None
VERSAO = None
COLUNAS_CONTRATO = None


def carregar_modelo():
    """Carrega na memoria o modelo indicado pelo alias de producao."""
    global MODELO, VERSAO, COLUNAS_CONTRATO
    mlflow.set_tracking_uri(config.URI_TRACKING)
    uri = f"models:/{config.NOME_MODELO}@{config.ALIAS_PROD}"
    try:
        info = mlflow.models.get_model_info(uri)
        COLUNAS_CONTRATO = [
            coluna["name"] for coluna in info.signature.inputs.to_dict()
        ]
        MODELO = mlflow.sklearn.load_model(uri)

        versao = MlflowClient().get_model_version_by_alias(
            config.NOME_MODELO, config.ALIAS_PROD
        )
        VERSAO = versao.version
        print(f"[modelo] versao {VERSAO} carregada de {uri}")
    except Exception as erro:
        MODELO, VERSAO, COLUNAS_CONTRATO = None, None, None
        print(
            f"[modelo] nenhum modelo em producao ({type(erro).__name__}). "
            "Rode onboard_v1.py."
        )


class Colaborador(BaseModel):
    """Uma entrada com as mesmas 15 features definidas no contrato."""

    id_pessoa: str | None = None
    abs_eventos: float = 0
    abs_qtd_total: float = 0
    horas_previstas_total: float = 0
    acidentes_eventos: float = 0
    acidentes_com_afastamento: float = 0
    acidentes_dias_perdidos: float = 0
    he_eventos: float = 0
    he_referencia_total: float = 0
    he_valor_total: float = 0
    hi_eventos: float = 0
    hi_minutos_irregulares: float = 0
    hi_minutos_extras: float = 0
    mov_sal_eventos: float = 0
    mov_sal_valor_total: float = 0
    mov_sal_perc_medio: float = 0


def faixa_de(prob):
    """Calcula a faixa de risco segundo a regra de negocio."""
    if prob >= config.FAIXA_ALERTA:
        return "alerta"
    if prob >= config.FAIXA_ATENCAO:
        return "atencao"
    return "ok"


def pontuar(df):
    """Aplica o modelo carregado, sem realizar treinamento."""
    X = df[config.FEATURES]
    prob = MODELO.predict_proba(X)[:, 1]
    classe = (prob >= config.LIMIAR_DECISAO).astype(int)
    return prob, classe


@app.get("/")
def pagina():
    return FileResponse(ESTATICOS / "index.html")


@app.get("/saude")
def saude():
    return {
        "modelo_carregado": MODELO is not None,
        "versao_modelo": VERSAO,
        "alias": config.ALIAS_PROD,
        "modelo": config.NOME_MODELO,
        "limiar": config.LIMIAR_DECISAO,
        "n_features": len(COLUNAS_CONTRATO) if COLUNAS_CONTRATO else None,
        "faixa_atencao": config.FAIXA_ATENCAO,
        "faixa_alerta": config.FAIXA_ALERTA,
        "lotes": banco.listar_lotes(),
    }


@app.get("/colaboradores")
def colaboradores():
    """Lista colaboradores pontuados com a faixa calculada no backend."""
    return {"colaboradores": banco.listar_colaboradores(), 
            "resumo": banco.resumo_por_lote() }


@app.post("/recarregar")
def recarregar():
    carregar_modelo()
    return saude()


@app.post("/prever")
def prever(colaborador: Colaborador):
    if MODELO is None:
        return JSONResponse(
            {"erro": "nenhum modelo em producao"}, status_code=503
        )

    dados = colaborador.model_dump()
    id_pessoa = dados.pop("id_pessoa") or f"avulso-{datetime.now():%H%M%S}"

    df = pd.DataFrame([dados])
    prob, classe = pontuar(df)

    banco.salvar_predicoes(
        lote="avulso",
        versao=VERSAO,
        ids=[id_pessoa],
        probabilidades=prob,
        classes=classe,
        entradas=[dados],
    )

    return {
        "id_pessoa": id_pessoa,
        "probabilidade": round(float(prob[0]), 4),
        "classe": int(classe[0]),
        "faixa": faixa_de(float(prob[0])),
        "limiar": config.LIMIAR_DECISAO,
        "versao_modelo": VERSAO,
    }


@app.post("/lote")
async def lote(arquivo: UploadFile = File(...)):
    if MODELO is None:
        return JSONResponse(
            {"erro": "nenhum modelo em producao"}, status_code=503
        )

    conteudo = await arquivo.read()
    df = pd.read_csv(io.BytesIO(conteudo), sep=";")

    faltando = [
        coluna for coluna in COLUNAS_CONTRATO if coluna not in df.columns
    ]
    if faltando:
        return JSONResponse(
            {
                "erro": (
                    "contrato violado -- este CSV nao serve para a "
                    "versao em producao"
                ),
                "versao_modelo": VERSAO,
                "colunas_faltando": faltando,
            },
            status_code=422,
        )

    prob, classe = pontuar(df)
    nome = Path(arquivo.filename).stem
    ids = (
        df[config.COLUNA_ID]
        if config.COLUNA_ID in df.columns
        else range(len(df))
    )

    banco.salvar_predicoes(
        lote=nome,
        versao=VERSAO,
        ids=list(ids),
        probabilidades=prob,
        classes=classe,
        entradas=df[config.FEATURES].to_dict(orient="records"),
    )

    return {
        "lote": nome,
        "linhas": len(df),
        "versao_modelo": VERSAO,
        "taxa_predicao_positiva": round(float(classe.mean()), 4),
        "probabilidade_media": round(float(prob.mean()), 4),
    }
