"""Mede um lote ja pontuado e registra o resultado no MLflow.
 
Nao cria modelo, nao treina e nao promove. Sem gabarito, mede distribuicoes
e comportamento das predicoes; com gabarito, mede tambem as metricas reais.
"""
 
import argparse
import sys
 
import mlflow
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
 
import config
from app import banco
 
 
# MLflow 3.16 escreve um simbolo Unicode ao encerrar o run. Em consoles
# Windows configurados como cp1252, force UTF-8 para o monitor nao falhar
# depois de registrar metricas e artefatos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
 
 
def comparar_distribuicoes(referencia, atual):
    """Uma linha por feature: mudou a forma, escala ou disponibilidade?"""
    linhas = []
    for coluna in config.FEATURES:
        ref, atu = referencia[coluna].dropna(), atual[coluna].dropna()
        media_ref = ref.mean()
        linhas.append(
            {
                "feature": coluna,
                "ks": round(ks_2samp(ref, atu).statistic, 3),
                "media_ref": round(media_ref, 3),
                "media_atual": round(atu.mean(), 3),
                "razao_media": round(atu.mean() / media_ref, 3)
                if media_ref
                else np.nan,
                "perc_zeros_ref": round((ref == 0).mean() * 100, 1),
                "perc_zeros_atual": round((atu == 0).mean() * 100, 1),
            }
        )
    return pd.DataFrame(linhas).sort_values("ks", ascending=False)
 
 
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", required=True, help="nome do lote no banco de producao")
    ap.add_argument(
        "--referencia",
        default=config.TABELA_TREINO,
        help="tabela usada como espelho do passado",
    )
    ap.add_argument("--gabarito", default=None, help="CSV em dados/ com o rotulo")
    args = ap.parse_args()
 
    atual = banco.carregar_lote(args.lote)
    if atual.empty:
        raise SystemExit(
            f"lote '{args.lote}' nao existe no banco. Envie o CSV pelo front primeiro."
        )
    # A referencia pode ser uma tabela de conjunto ou um lote ja pontuado.
    # Isso permite que, depois de uma mudanca de populacao, o monitor compare
    # o proximo lote com a nova normalidade em vez de eternamente com a v1.
    if banco.existe_tabela(args.referencia):
        referencia = banco.carregar_conjunto(args.referencia)
    else:
        referencia = banco.carregar_lote(args.referencia)
        if referencia.empty:
            raise SystemExit(
                f"'{args.referencia}' nao e tabela nem lote pontuado."
            )
 
    relatorio = comparar_distribuicoes(referencia, atual)
    em_drift = relatorio[relatorio["ks"] > 0.2]
    mortas = relatorio[relatorio["perc_zeros_atual"] == 100.0]
 
    metricas = {
        "linhas": len(atual),
        "taxa_predicao_positiva": round(atual["classe"].mean(), 4),
        "probabilidade_media": round(atual["probabilidade"].mean(), 4),
        "features_em_drift": len(em_drift),
        "maior_ks": float(relatorio["ks"].max()),
        "features_mortas": len(mortas),
    }
 
    if args.gabarito:
        gab = pd.read_csv(config.PASTA_DADOS / args.gabarito, sep=";")
        gab[config.COLUNA_ID] = gab[config.COLUNA_ID].astype(str)
        juntos = atual.merge(gab, on=config.COLUNA_ID, how="inner")
        y, y_pred = juntos[config.COLUNA_ALVO], juntos["classe"]
        metricas.update(
            {
                "accuracy": round(accuracy_score(y, y_pred), 4),
                "f1": round(f1_score(y, y_pred), 4),
                "precision": round(precision_score(y, y_pred), 4),
                "recall": round(recall_score(y, y_pred), 4),
            }
        )
 
    config.PASTA_RELATORIOS.mkdir(exist_ok=True)
    caminho = config.PASTA_RELATORIOS / f"drift_{args.lote}.csv"
    relatorio.to_csv(caminho, sep=";", index=False)
 
    mlflow.set_tracking_uri(config.URI_TRACKING)
    mlflow.set_experiment(config.NOME_EXPERIMENTO)
    with mlflow.start_run(run_name=f"monitoramento_{args.lote}"):
        mlflow.set_tags(
            {
                "tipo": "monitoramento",
                "lote": args.lote,
                "referencia": args.referencia,
                "versao_modelo": atual["versao_modelo"].iloc[0],
            }
        )
        mlflow.log_params({"lote": args.lote, "referencia": args.referencia})
        mlflow.log_metrics(metricas)
        mlflow.log_artifact(str(caminho), artifact_path="drift")
 
    print(
        f"\nlote {args.lote}  ({len(atual)} linhas, "
        f"modelo v{atual['versao_modelo'].iloc[0]})"
    )
    print(f"referencia: {args.referencia}\n")
    print(relatorio.to_string(index=False))
    print("\nresumo")
    for k, v in metricas.items():
        print(f"  {k:<24} {v}")
    if len(mortas):
        print(
            "\n  atencao: feature(s) 100% zerada(s) -> "
            f"{', '.join(mortas['feature'])}"
        )
        print("  uma coluna 100% zerada nao esta em drift. Ela esta morta.")
 
 
if __name__ == "__main__":
    main()