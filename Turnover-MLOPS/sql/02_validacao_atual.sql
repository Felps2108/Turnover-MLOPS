-- =====================================================================
-- AULA 2 -- a validacao da populacao nova
--
--     psql turnover -U postgres -f sql/02_validacao_atual.sql
--
-- Na Aula 1 existia UM conjunto de teste. Agora sao DOIS, com papeis
-- diferentes -- e o segundo nao substitui o primeiro:
--
--   validacao_congelada  GUARDA DE REGRESSAO
--                        Nunca muda. Nunca e apagada. Nunca cresce.
--                        Responde: "eu quebrei o que ja funcionava?"
--
--   validacao_atual      CONJUNTO DE ACEITACAO  (esta tabela)
--                        Representa a populacao que o modelo atende HOJE.
--                        ACUMULA: cada lote rotulado e anexado, nunca
--                        substitui o anterior.
--                        Responde: "serve para o mundo de agora?"
--
-- Quando atualizar esta tabela:
--   gatilho    evidencia de mudanca de populacao no relatorio de drift.
--              Nao e calendario, e NAO e "quando o resultado nao agrada".
--   como       INSERT do lote rotulado. A mistura se corrige sozinha
--              conforme mais meses entram.
--   registro   a promocao grava em que conjunto foi decidida (validado_em).
-- =====================================================================

CREATE TABLE IF NOT EXISTS validacao_atual (
    id_pessoa                    TEXT PRIMARY KEY,
    abs_eventos                  DOUBLE PRECISION NOT NULL DEFAULT 0,
    abs_qtd_total                DOUBLE PRECISION NOT NULL DEFAULT 0,
    horas_previstas_total        DOUBLE PRECISION NOT NULL DEFAULT 0,
    acidentes_eventos            DOUBLE PRECISION NOT NULL DEFAULT 0,
    acidentes_com_afastamento    DOUBLE PRECISION NOT NULL DEFAULT 0,
    acidentes_dias_perdidos      DOUBLE PRECISION NOT NULL DEFAULT 0,
    he_eventos                   DOUBLE PRECISION NOT NULL DEFAULT 0,
    he_referencia_total          DOUBLE PRECISION NOT NULL DEFAULT 0,
    he_valor_total               DOUBLE PRECISION NOT NULL DEFAULT 0,
    hi_eventos                   DOUBLE PRECISION NOT NULL DEFAULT 0,
    hi_minutos_irregulares       DOUBLE PRECISION NOT NULL DEFAULT 0,
    hi_minutos_extras            DOUBLE PRECISION NOT NULL DEFAULT 0,
    mov_sal_eventos              DOUBLE PRECISION NOT NULL DEFAULT 0,
    mov_sal_valor_total          DOUBLE PRECISION NOT NULL DEFAULT 0,
    mov_sal_perc_medio           DOUBLE PRECISION NOT NULL DEFAULT 0,
    pediu_para_sair              SMALLINT NOT NULL,
    origem                       TEXT     NOT NULL   -- de qual lote saiu
);

-- Para recomecar:  DROP TABLE IF EXISTS validacao_atual;
